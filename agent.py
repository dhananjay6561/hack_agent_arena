"""
team_hydra — AppWorld agent. APPROACH: Episodic Memory (HydraDB).

Difference vs baseline: a persistent episodic memory of solved tasks. Before
solving, we recall the most semantically-similar past episodes (task -> apps ->
key API call sequence -> final answer) and inject them as worked examples.
After a task completes, we store its trajectory so later tasks benefit.

Backend:
  * If `hydra_db` is importable AND HYDRA_DB_API_KEY is set -> HydraDB (shared,
    survives across runs). NOTE: the HydraDB SDK surface here is a thin adapter
    (HydraBackend) — verify method names against your installed SDK version.
  * Otherwise -> a local JSON store at /tmp/hydra_episodic.json with file locking
    so it is safe across the multiprocessing Pool. Runs with zero setup.

Run (OpenRouter + HydraDB):
  # in .env: OPENROUTER_API_KEY=...  HYDRA_API_KEY=...   then set MODEL (e.g. meta-llama/llama-3.3-70b-instruct)
  APPWORLD_DATASET=mixed15 APPWORLD_EXPERIMENT=team_hydra python agent_hydra.py
"""

import os
import re
import json
import sys
import math
import fcntl
from collections import defaultdict
from multiprocessing import Pool

def log(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr, flush=True)

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from appworld import AppWorld, load_task_ids
from openai import OpenAI

# ── config ──────────────────────────────────────────────────────────────────
# >>> SET YOUR MODEL HERE (OpenRouter model id), or pass MODEL=... in the env <<<
#     e.g.  meta-llama/llama-3.3-70b-instruct   (organizers will confirm the exact id)
MODEL          = os.environ.get("MODEL", "")          # <<< PUT MODEL HERE

# OpenRouter is OpenAI-API compatible — point the client at their endpoint.
_openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
client = OpenAI(api_key=_openrouter_key or "MISSING_OPENROUTER_API_KEY",
                base_url="https://openrouter.ai/api/v1",
                max_retries=5)

# Episodic recall is handled by HydraDB (server-side semantic search), so local
# embeddings are OPTIONAL — only used by the local-file fallback when there's no
# HydraDB key. Used if an OpenAI key is present; otherwise embeddings are skipped.
_openai_key    = os.environ.get("OPENAI_API_KEY", "")
embed_client   = OpenAI(api_key=_openai_key, max_retries=5) if _openai_key else None
EMBED_MODEL    = os.environ.get("EMBED_MODEL", "text-embedding-3-small")

DATASET        = os.environ.get("APPWORLD_DATASET", "dev")
EXPERIMENT     = os.environ.get("APPWORLD_EXPERIMENT", "team_hydra")
MAX_INTERACTIONS = int(os.environ.get("MAX_INTERACTIONS", "30"))
MAX_TASKS      = int(os.environ.get("MAX_TASKS", "0"))
MEM_FILE       = os.environ.get("HYDRA_MEM_FILE", "/tmp/hydra_episodic.json")
# Accept any of the common env var spellings; strip stray whitespace.
HYDRA_KEY      = (os.environ.get("HYDRA_DB_API_KEY", "")
                  or os.environ.get("HYDRADB_API_KEY", "")
                  or os.environ.get("HYDRA_API_KEY", "")).strip()
RECALL_K       = int(os.environ.get("RECALL_K", "3"))

ALL_APPS = ["venmo", "splitwise", "spotify", "gmail", "amazon",
            "simple_note", "todoist", "file_system", "phone"]

# ── prompts ──────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """\
You are an autonomous coding agent in AppWorld. Complete tasks by writing Python code.

RULES (follow every turn):
1. ONE Python code block per turn, nothing else:
   ```python
   # code here
   ```
2. BEFORE calling any API you haven't used: read its doc first:
       print(apis.api_docs.show_api_doc(app_name='X', api_name='Y'))
3. NEVER guess field names or user IDs — look them up from API responses.
4. BATCH multiple calls into one block to save steps.
5. On error: read the full traceback, fix the params, retry.
6. ANSWER RULES — before calling complete_task():
   - If the task asks "top N" items → your answer MUST contain exactly N items.
   - If the task asks a question (what/how many/which/who/list) → answer MUST NOT be None.
   - Currency answers: "$X.XX" format. Count answers: plain integer string.
   - List answers: comma-separated, e.g. "Title A, Title B, Title C".
7. Call complete_task() ONLY when the task is 100%% done.

TASK: {task}
STEP: {steps_used}/30 used. {budget_warning}

MEMORY — how similar past tasks were solved (use as a guide, adapt to THIS task):
{memory}

KEY FACTS FROM PREVIOUS STEPS:
{facts}

TOKENS (already logged in — use these directly):
{tokens}

--- EXAMPLE ---
Task: "Send $15 to Alice on Venmo for lunch. Her username is alice99."
Turn 1:
```python
token = '{{'venmo_token'}}'  # from tokens above
alice = apis.venmo.search_users(access_token=token, query='alice99')
result = apis.venmo.create_transaction(access_token=token, receiver_id=alice[0]['id'], amount=15.00, description='lunch', private=False)
print(result)
```
Turn 2:
```python
apis.supervisor.complete_task(answer=None)
```
--- END EXAMPLE ---
"""

PLANNER_PROMPT = """\
You are a task planner for an AppWorld agent.
Given the task below, output a JSON object with this exact schema:
{{
  "apps_needed": ["<app1>", ...],
  "steps": [
    {{"step": "<what to do>", "app": "<app>"}}
  ],
  "answer_expected": true/false,
  "answer_type": "currency|count|list|name|none"
}}

Known apps: venmo, splitwise, spotify, gmail, amazon, simple_note, todoist, file_system, phone.
answer_type rules:
  - currency: task involves a dollar amount answer
  - count: task asks how many
  - list: task asks to list/enumerate items
  - name: task asks for a name/username/title
  - none: task is an action with no question

Output ONLY the JSON object, no other text.

Task: {task}
"""

# ── embedding helper ────────────────────────────────────────────────────────
def _embed(text: str):
    """Optional — returns None if no embeddings backend is configured."""
    if embed_client is None:
        return None
    resp = embed_client.embeddings.create(model=EMBED_MODEL, input=[text])
    return resp.data[0].embedding


def _norm(v: list[float]) -> float:
    return math.sqrt(sum(x * x for x in v)) or 1.0


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (_norm(a) * _norm(b))


# ── episodic memory backends ────────────────────────────────────────────────
class LocalBackend:
    """JSON file + flock, safe across the multiprocessing Pool."""
    def __init__(self, path: str):
        self.path = path
        if not os.path.exists(path):
            try:
                with open(path, "w") as f:
                    json.dump([], f)
            except Exception:
                pass

    def _read(self) -> list[dict]:
        try:
            with open(self.path) as f:
                fcntl.flock(f, fcntl.LOCK_SH)
                try:
                    return json.load(f)
                finally:
                    fcntl.flock(f, fcntl.LOCK_UN)
        except Exception:
            return []

    def add(self, episode: dict) -> None:
        try:
            with open(self.path, "r+") as f:
                fcntl.flock(f, fcntl.LOCK_EX)
                try:
                    try:
                        data = json.load(f)
                    except Exception:
                        data = []
                    data.append(episode)
                    f.seek(0); f.truncate()
                    json.dump(data, f)
                finally:
                    fcntl.flock(f, fcntl.LOCK_UN)
        except Exception as e:
            log(f"  [mem] local add failed: {e}")

    def recall(self, task_text: str, query_emb, k: int) -> list[dict]:
        if not query_emb:
            return []
        data = self._read()
        scored = []
        for ep in data:
            emb = ep.get("emb")
            if not emb:
                continue
            scored.append((_cosine(query_emb, emb), ep))
        scored.sort(key=lambda t: t[0], reverse=True)
        return [ep for _, ep in scored[:k]]


class HydraBackend:
    """Adapter over the real hydra-db-python SDK (verified against v0.1.6).

    add    -> client.upload.add_memory(memories=[{text,title,infer,document_metadata}], ...)
    recall -> client.recall.recall_preferences(query=<task text>, ...) -> RetrievalResult.chunks
              (add_memory writes the "memories" store; recall_preferences reads it.
               full_recall reads the separate knowledge/sources store and returns
               nothing for these — verified against the live API.)

    HydraDB ranks semantically server-side, so the task embedding is unused here
    (kept for interface parity with LocalBackend). Any failure degrades to a
    no-op / empty result rather than crashing the task.
    """
    def __init__(self, key: str):
        from hydra_db import HydraDB
        self.client = HydraDB(token=key)
        self.tenant = os.environ.get("HYDRA_TENANT", "appworld")
        self.sub = EXPERIMENT  # one sub-tenant per experiment

    def add(self, episode: dict) -> None:
        try:
            self.client.upload.add_memory(
                tenant_id=self.tenant, sub_tenant_id=self.sub, upsert=True,
                memories=[{
                    "text": episode_text(episode),
                    "title": (episode.get("task") or "")[:80],
                    "infer": False,
                    # HydraDB expects document_metadata as a JSON *string*.
                    "document_metadata": json.dumps({
                        "apps": episode.get("apps", []),
                        "calls": episode.get("calls", ""),
                        "answer": episode.get("answer"),
                        "success": bool(episode.get("success")),
                    }),
                }],
            )
        except Exception as e:
            log(f"  [mem] hydra add failed: {e}")

    def recall(self, task_text: str, query_emb, k: int) -> list[dict]:
        try:
            res = self.client.recall.recall_preferences(
                tenant_id=self.tenant, sub_tenant_id=self.sub,
                query=task_text or "appworld task", max_results=k,
            )
            out = []
            for ch in (getattr(res, "chunks", None) or [])[:k]:
                # Primary source of truth: the stored text (round-trips reliably).
                ep = parse_episode_text(getattr(ch, "chunk_content", "") or "")
                # Supplement with document_metadata if the API echoes it back.
                md_raw = getattr(ch, "document_metadata", None)
                md = {}
                if isinstance(md_raw, str):
                    try:
                        md = json.loads(md_raw)
                    except Exception:
                        md = {}
                elif isinstance(md_raw, dict):
                    md = md_raw
                if md:
                    ep["apps"] = md.get("apps") or ep["apps"]
                    ep["calls"] = md.get("calls") or ep["calls"]
                    ep["answer"] = md.get("answer", ep["answer"])
                    ep["success"] = md.get("success", ep["success"])
                if not ep.get("task"):
                    ep["task"] = getattr(ch, "source_title", None) or task_text
                out.append(ep)
            return out
        except Exception as e:
            log(f"  [mem] hydra recall failed: {e}")
            return []


def make_memory():
    if HYDRA_KEY:
        try:
            import hydra_db  # noqa: F401
            log("  [mem] using HydraDB backend")
            return HydraBackend(HYDRA_KEY)
        except Exception as e:
            log(f"  [mem] HydraDB unavailable ({e}); falling back to local store")
    return LocalBackend(MEM_FILE)


def parse_episode_text(text: str) -> dict:
    """Reverse of episode_text() — reconstruct an episode from stored text."""
    ep = {"task": "", "apps": [], "calls": "", "answer": None, "success": None}
    for line in (text or "").splitlines():
        if line.startswith("Task:"):
            ep["task"] = line[5:].strip()
        elif line.startswith("Apps:"):
            ep["apps"] = [a.strip() for a in line[5:].split(",") if a.strip()]
        elif line.startswith("Key API calls:"):
            ep["calls"] = line[len("Key API calls:"):].strip()
        elif line.startswith("Answer:"):
            v = line[7:].strip()
            ep["answer"] = None if v in ("None", "") else v
        elif line.startswith("Result:"):
            ep["success"] = "success" in line.lower()
    return ep


def episode_text(ep: dict) -> str:
    """Readable, embeddable summary of one solved episode (HydraDB stores this)."""
    status = "success" if ep.get("success") else "incomplete"
    return (
        f"Task: {ep.get('task','')}\n"
        f"Apps: {', '.join(ep.get('apps', []))}\n"
        f"Key API calls: {ep.get('calls','')}\n"
        f"Answer: {ep.get('answer')}\n"
        f"Result: {status}"
    )


def render_memory(episodes: list[dict]) -> str:
    if not episodes:
        return "(no similar past tasks yet)"
    blocks = []
    for ep in episodes:
        status = "SUCCESS" if ep.get("success") else "incomplete"
        blocks.append(
            f"- Past task ({status}): {ep.get('task','')[:160]}\n"
            f"    apps: {', '.join(ep.get('apps', []))}\n"
            f"    key calls: {ep.get('calls','')[:300]}\n"
            f"    answer: {ep.get('answer')}"
        )
    return "\n".join(blocks)


# ── pre-login ─────────────────────────────────────────────────────────────────
def pre_login(world: AppWorld) -> dict[str, str]:
    code = """
creds_list = apis.supervisor.show_account_passwords()
creds = {c['account_name']: c['password'] for c in creds_list}
profile = apis.supervisor.show_profile()
email = profile.get('email', '')
phone_number = profile.get('phone_number', '')
login_map = {
    'venmo': ('venmo', email), 'splitwise': ('splitwise', email),
    'spotify': ('spotify', email), 'gmail': ('gmail', email),
    'amazon': ('amazon', email), 'simple_note': ('simple_note', email),
    'todoist': ('todoist', email), 'file_system': ('file_system', email),
    'phone': ('phone', phone_number),
}
for app, (cred_key, username) in login_map.items():
    try:
        tok = getattr(apis, app).login(username=username, password=creds.get(cred_key, ''))
        print('TOKEN:' + app + ':' + tok.get('access_token', ''))
    except Exception as e:
        print('TOKEN:' + app + ':FAILED')
"""
    output = str(world.execute(code))
    tokens: dict[str, str] = {}
    for line in output.splitlines():
        if line.startswith("TOKEN:"):
            parts = line.split(":", 2)
            if len(parts) == 3 and parts[2] != "FAILED":
                tokens[parts[1]] = parts[2]
    log(f"  pre-login: {list(tokens.keys())}")
    return tokens


# ── completion helper ──────────────────────────────────────────────────────────
def _create_completion(messages, system=None, max_tokens=2000):
    msgs = ([{"role": "system", "content": system}] if system else []) + messages
    kwargs = dict(model=MODEL, messages=msgs)
    # strip any OpenRouter "provider/" prefix before sniffing for reasoning models
    _name = MODEL.split("/")[-1]
    if _name.startswith("gpt-5") or _name.startswith(("o1", "o3", "o4")):
        kwargs["max_completion_tokens"] = max_tokens
        kwargs["reasoning_effort"] = "high"
    else:
        kwargs["max_tokens"] = max_tokens
        kwargs["temperature"] = 0.0
    return client.chat.completions.create(**kwargs)


def plan_task(task: str) -> dict:
    prompt = PLANNER_PROMPT.format(task=task)
    resp = _create_completion([{"role": "user", "content": prompt}], max_tokens=800)
    raw = resp.choices[0].message.content.strip()
    try:
        raw = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()
        return json.loads(raw)
    except Exception:
        return {
            "apps_needed": ALL_APPS,
            "steps": [{"step": task, "app": "unknown"}],
            "answer_expected": False,
            "answer_type": "none",
        }


# ── answer normalization ──────────────────────────────────────────────────────
def normalize_answer(raw, answer_type: str):
    if raw is None:
        return None
    if answer_type == "currency":
        try:
            amount = float(str(raw).replace("$", "").replace(",", "").strip())
            return f"${amount:.2f}"
        except Exception:
            return raw
    if answer_type == "count":
        try:
            return str(int(float(str(raw).strip())))
        except Exception:
            return raw
    if answer_type == "list":
        items = [x.strip() for x in str(raw).split(",")]
        return ", ".join(items)
    if answer_type == "name":
        return str(raw).strip()
    return raw


# ── LLM call ─────────────────────────────────────────────────────────────────
def call_llm(messages: list[dict], working_memory: dict, steps_used: int) -> str:
    if steps_used >= 20:
        remaining = MAX_INTERACTIONS - steps_used
        budget_warning = (
            f"⚠️ ONLY {remaining} STEPS LEFT — skip discovery, batch remaining calls, "
            f"call complete_task() as soon as possible."
        )
    else:
        budget_warning = ""

    facts_str = "\n".join(working_memory.get("facts", [])[-6:]) or "none yet"
    tokens_str = ", ".join(
        f"{app}: use variable '{app}_token' (already set)" if working_memory["tokens"].get(app)
        else f"{app}: login failed"
        for app in working_memory.get("apps_needed", ALL_APPS)
    )
    system = SYSTEM_PROMPT.format(
        task=working_memory.get("task", ""),
        steps_used=steps_used,
        budget_warning=budget_warning,
        memory=working_memory.get("memory", ""),
        facts=facts_str,
        tokens=tokens_str,
    )
    resp = _create_completion(messages, system=system, max_tokens=2000)
    return resp.choices[0].message.content


def extract_code(text: str) -> str:
    m = re.search(r"```(?:python)?\s*\n(.*?)```", text, re.S)
    return m.group(1).strip() if m else text.strip()


# ── error-retry executor ─────────────────────────────────────────────────────
def execute_with_retry(world: AppWorld, messages: list[dict],
                       working_memory: dict, step: int,
                       max_retries: int = 3) -> tuple[str, str]:
    reply = call_llm(messages, working_memory, step)
    code = extract_code(reply)

    for attempt in range(max_retries):
        output = str(world.execute(code))
        error_indicators = ["Error", "Exception", "Traceback", "error:"]
        if not any(ind in output for ind in error_indicators):
            return reply, output

        if attempt < max_retries - 1:
            retry_prompt = (
                f"Your code raised an error (attempt {attempt+1}):\n{output}\n\n"
                f"Fix the code and try again. Re-read the api_doc if needed."
            )
            retry_messages = messages + [
                {"role": "assistant", "content": reply},
                {"role": "user", "content": retry_prompt},
            ]
            reply = call_llm(retry_messages, working_memory, step)
            code = extract_code(reply)

    return reply, output


# ── main solve loop ──────────────────────────────────────────────────────────
def solve(world: AppWorld, tokens: dict[str, str], memory) -> None:
    task_text = world.task.instruction
    supervisor = getattr(world.task, "supervisor", "")

    plan = plan_task(task_text)
    answer_type = plan.get("answer_type", "none")
    apps_needed = plan.get("apps_needed", ALL_APPS)

    # recall similar past episodes (HydraDB ranks by query text; the embedding is
    # only for the local-file fallback, so a missing embedding never blocks recall)
    task_emb = None
    try:
        task_emb = _embed(task_text)
    except Exception as e:
        log(f"  [mem] embedding unavailable ({e}); HydraDB recall uses query text")
    try:
        recalled = memory.recall(task_text, task_emb, RECALL_K)
    except Exception as e:
        recalled = []
        log(f"  [mem] recall failed: {e}")
    log(f"  [mem] recalled {len(recalled)} episode(s)")

    working_memory: dict = {
        "task": task_text,
        "supervisor": supervisor,
        "plan_steps": [s["step"] for s in plan.get("steps", [])],
        "apps_needed": apps_needed,
        "current_step": 0,
        "completed_steps": [],
        "logged_in": list(tokens.keys()),
        "tokens": tokens,
        "known_ids": {},
        "facts": [],
        "errors": [],
        "answer": None,
        "answer_type": answer_type,
        "answer_expected": plan.get("answer_expected", False),
        "memory": render_memory(recalled),
        "calls": [],
    }

    token_setup_lines = []
    for app in apps_needed:
        if tokens.get(app):
            token_setup_lines.append(f"{app}_token = {tokens[app]!r}")
    token_preamble = "\n".join(token_setup_lines)

    first_user_msg = (
        f"Supervisor: {supervisor}\n\n"
        f"Task: {task_text}\n\n"
        f"Your tokens (already logged in — paste these at the top of your first code block):\n"
        f"```python\n{token_preamble}\n```\n\n"
        "Begin. One Python code block per turn. Batch multiple calls. "
        "For list answers, include ALL requested items."
    )

    messages = [{"role": "user", "content": first_user_msg}]
    success = False

    for step in range(MAX_INTERACTIONS):
        working_memory["current_step"] = step
        reply, output = execute_with_retry(world, messages, working_memory, step)

        short_out = str(output)[:200]
        log(f"  step {step+1}: {short_out!r}")

        # capture apis.<app>.<api>( calls for the episode trace
        for call in re.findall(r"apis\.\w+\.\w+\(", extract_code(reply)):
            working_memory["calls"].append(call.rstrip("("))

        working_memory["facts"].append(f"step {step+1}: {short_out}")
        if len(working_memory["facts"]) > 10:
            working_memory["facts"] = working_memory["facts"][-10:]

        if any(ind in output for ind in ["Error", "Exception", "Traceback"]):
            working_memory["errors"].append(f"step {step+1}: {short_out}")

        messages.append({"role": "assistant", "content": reply})
        messages.append({"role": "user", "content": f"Execution output:\n{output}"})

        if world.task_completed():
            log("  ✓ task_completed")
            success = True
            break
    else:
        log("  ✗ hit MAX_INTERACTIONS without completion")

    # store episode
    try:
        calls_seq = " -> ".join(dict.fromkeys(working_memory["calls"]))  # dedup, keep order
        episode = {
            "task": task_text,
            "apps": apps_needed,
            "calls": calls_seq,
            "answer": working_memory.get("answer"),
            "success": success,
            "emb": task_emb,
        }
        memory.add(episode)
    except Exception as e:
        log(f"  [mem] store failed: {e}")


# ── per-task worker ─────────────────────────────────────────────────────────────
def _run_task(args: tuple) -> tuple:
    i, task_id = args
    memory = make_memory()
    with AppWorld(task_id=task_id, experiment_name=EXPERIMENT) as world:
        try:
            tokens = pre_login(world)
            solve(world, tokens, memory)
            return (i, task_id, "✓")
        except Exception as e:
            return (i, task_id, f"! error: {e}")


# ── main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    task_ids = load_task_ids(DATASET)
    if MAX_TASKS:
        task_ids = task_ids[:MAX_TASKS]
    log(f"[HYDRA] Running '{EXPERIMENT}' on {len(task_ids)} '{DATASET}' tasks with {MODEL}")
    log(f"  memory backend: {'HydraDB' if HYDRA_KEY else 'local file ' + MEM_FILE}")

    WORKERS = int(os.environ.get("WORKERS", "3"))
    log(f"Running {WORKERS} tasks in parallel...")
    n = len(task_ids)
    with Pool(processes=WORKERS) as pool:
        for result in pool.imap_unordered(_run_task, enumerate(task_ids, 1)):
            i, task_id, status = result
            log(f"  [{i}/{n}] {task_id} {status}")

    log(f"\nDone. Outputs in ./experiments/outputs/{EXPERIMENT}/")


if __name__ == "__main__":
    main()
