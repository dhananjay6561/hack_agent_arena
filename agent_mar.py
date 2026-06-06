"""
team_mar — AppWorld agent. APPROACH: Multi-Agent Reflexion (MAR).

Difference vs baseline: on a step error, instead of blindly re-running the
same logic up to 3x, a single "critic panel" LLM call diagnoses the root
cause from 3 perspectives (Verifier / Skeptic / Logician) and synthesizes ONE
concrete corrective directive, which is injected into the retry. This shifts
the reasoning frame before retrying — the way humans debug.

Run (OpenRouter):
  # in .env: OPENROUTER_API_KEY=...   then set MODEL (e.g. meta-llama/llama-3.3-70b-instruct)
  APPWORLD_DATASET=mixed15 APPWORLD_EXPERIMENT=team_mar python agent_mar.py
"""

import os
import re
import json
import sys
from collections import defaultdict, Counter
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
DATASET        = os.environ.get("APPWORLD_DATASET", "dev")
EXPERIMENT     = os.environ.get("APPWORLD_EXPERIMENT", "team_mar")
MAX_INTERACTIONS = int(os.environ.get("MAX_INTERACTIONS", "30"))
MAX_TASKS      = int(os.environ.get("MAX_TASKS", "0"))

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

KEY FACTS FROM PREVIOUS STEPS:
{facts}

TOKENS (already logged in — use these directly):
{tokens}

--- EXAMPLE ---
Task: "Send $15 to Alice on Venmo for lunch. Her username is alice99."
Turn 1:
```python
token = '{{'venmo_token'}}'  # from tokens above
alice = apis.venmo.get_user_by_username(access_token=token, username='alice99')
result = apis.venmo.send_money(access_token=token, user_id=alice['id'], amount=15.00, note='lunch')
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

# ── MAR critic panel prompt ───────────────────────────────────────────────────
MAR_REFLECT_PROMPT = """\
A step in an AppWorld coding agent FAILED. Convene a 3-perspective critic panel
to diagnose the ROOT CAUSE, then synthesize ONE concrete corrective directive.

THE FAILING CODE:
```python
{code}
```

THE ERROR / OUTPUT:
{error}

RECENT FACTS:
{facts}

Think as three critics (be terse, one or two sentences each):
- VERIFIER: Do the call's parameters match the API doc exactly (names, types, required)?
- SKEPTIC: Are we even calling the RIGHT api? Maybe the wrong api/app for this sub-goal.
- LOGICIAN: Is the data-flow/order wrong (using an id/field that was never fetched)?

Then output a single final block:
FIX: <one concrete, specific instruction for the next attempt — name the exact api,
the exact params to change, or the exact lookup to do first. Prefer reading the
api_doc if the signature is uncertain.>

Keep the whole reply under 120 words.
"""

# ── API index (built once per run) ───────────────────────────────────────────
API_INDEX: dict[str, list[tuple[str, str]]] = defaultdict(list)
EXPLORED_APIS: dict[tuple[str, str], str] = {}

APP_HINTS = {
    "pay": ["venmo", "splitwise"],
    "transfer": ["venmo"],
    "send money": ["venmo"],
    "music": ["spotify"],
    "playlist": ["spotify"],
    "song": ["spotify"],
    "album": ["spotify"],
    "email": ["gmail"],
    "mail": ["gmail"],
    "message": ["gmail", "phone"],
    "note": ["simple_note"],
    "todo": ["todoist"],
    "task": ["todoist"],
    "file": ["file_system"],
    "folder": ["file_system"],
    "call": ["phone"],
    "contact": ["phone"],
    "sms": ["phone"],
    "buy": ["amazon"],
    "order": ["amazon"],
    "product": ["amazon"],
    "split": ["splitwise"],
    "expense": ["splitwise"],
    "friend": ["splitwise", "venmo"],
}


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z]{3,}", text.lower())


def build_api_index(world: AppWorld) -> None:
    global API_INDEX
    API_INDEX = defaultdict(list)
    for app in ALL_APPS:
        try:
            descs = world.execute(
                f"print(apis.api_docs.show_api_descriptions(app_name='{app}'))"
            )
            for token in _tokenize(str(descs)):
                API_INDEX[token].append((app, app))
            if isinstance(descs, list):
                for item in descs:
                    name = item.get("name", "") if isinstance(item, dict) else str(item)
                    desc = item.get("description", "") if isinstance(item, dict) else ""
                    for token in _tokenize(name + " " + desc):
                        API_INDEX[token].append((app, name))
        except Exception:
            pass


def route_apps(task: str) -> list[str]:
    task_lower = task.lower()
    apps: set[str] = set()
    for hint, app_list in APP_HINTS.items():
        if hint in task_lower:
            apps.update(app_list)
    return list(apps) if apps else ALL_APPS


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


# ── MAR reflection ──────────────────────────────────────────────────────────────
def mar_reflect(code: str, error: str, working_memory: dict) -> str:
    """Critic-panel diagnosis of a failed step. Returns a corrective directive."""
    facts_str = "\n".join(working_memory.get("facts", [])[-6:]) or "none yet"
    prompt = MAR_REFLECT_PROMPT.format(
        code=code[:1500], error=str(error)[:1200], facts=facts_str,
    )
    try:
        # NOTE: gpt-5.x at reasoning_effort=high spends ~500 tokens on hidden
        # reasoning before any visible text, so this budget must be generous —
        # 600 returns finish_reason=length with EMPTY content (MAR becomes a
        # silent no-op). 2000 leaves room for the critic panel + FIX line.
        resp = _create_completion([{"role": "user", "content": prompt}], max_tokens=2000)
        directive = (resp.choices[0].message.content or "").strip()
        return directive or "FIX: re-read the api_doc for the exact api name/params and correct them."
    except Exception as e:
        return f"FIX: re-read the api_doc and correct the parameters. ({e})"


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
        facts=facts_str,
        tokens=tokens_str,
    )
    resp = _create_completion(messages, system=system, max_tokens=2000)
    return resp.choices[0].message.content


def extract_code(text: str) -> str:
    m = re.search(r"```(?:python)?\s*\n(.*?)```", text, re.S)
    return m.group(1).strip() if m else text.strip()


# ── error-retry executor (MAR-augmented) ───────────────────────────────────────
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
            # MAR: critic-panel diagnosis instead of blind retry
            directive = mar_reflect(code, output, working_memory)
            log(f"    MAR diagnosis (attempt {attempt+1}): {directive[:160]!r}")
            retry_prompt = (
                f"Your code raised an error (attempt {attempt+1}):\n{output}\n\n"
                f"A critic panel diagnosed the failure:\n{directive}\n\n"
                f"Apply the FIX directive precisely and try again."
            )
            retry_messages = messages + [
                {"role": "assistant", "content": reply},
                {"role": "user", "content": retry_prompt},
            ]
            reply = call_llm(retry_messages, working_memory, step)
            code = extract_code(reply)

    return reply, output


# ── main solve loop ──────────────────────────────────────────────────────────
def solve(world: AppWorld, tokens: dict[str, str]) -> None:
    task_text = world.task.instruction
    supervisor = getattr(world.task, "supervisor", "")

    plan = plan_task(task_text)
    answer_type = plan.get("answer_type", "none")
    apps_needed = plan.get("apps_needed", ALL_APPS)

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

    for step in range(MAX_INTERACTIONS):
        working_memory["current_step"] = step
        reply, output = execute_with_retry(world, messages, working_memory, step)

        short_out = str(output)[:200]
        log(f"  step {step+1}: {short_out!r}")

        working_memory["facts"].append(f"step {step+1}: {short_out}")
        if len(working_memory["facts"]) > 10:
            working_memory["facts"] = working_memory["facts"][-10:]

        if any(ind in output for ind in ["Error", "Exception", "Traceback"]):
            working_memory["errors"].append(f"step {step+1}: {short_out}")

        messages.append({"role": "assistant", "content": reply})
        messages.append({"role": "user", "content": f"Execution output:\n{output}"})

        if world.task_completed():
            log("  ✓ task_completed")
            return

    log("  ✗ hit MAX_INTERACTIONS without completion")


# ── per-task worker ─────────────────────────────────────────────────────────────
def _run_task(args: tuple) -> tuple:
    i, task_id = args
    with AppWorld(task_id=task_id, experiment_name=EXPERIMENT) as world:
        try:
            tokens = pre_login(world)
            solve(world, tokens)
            return (i, task_id, "✓")
        except Exception as e:
            return (i, task_id, f"! error: {e}")


# ── main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    task_ids = load_task_ids(DATASET)
    if MAX_TASKS:
        task_ids = task_ids[:MAX_TASKS]
    log(f"[MAR] Running '{EXPERIMENT}' on {len(task_ids)} '{DATASET}' tasks with {MODEL}")

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
