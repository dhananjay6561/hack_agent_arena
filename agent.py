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
MODEL          = os.environ.get("MODEL", "")

_openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
client = OpenAI(api_key=_openrouter_key or "MISSING_OPENROUTER_API_KEY",
                base_url="https://openrouter.ai/api/v1",
                max_retries=5)


DATASET        = os.environ.get("APPWORLD_DATASET", "dev")
EXPERIMENT     = os.environ.get("APPWORLD_EXPERIMENT", "team_hydra")
MAX_INTERACTIONS = int(os.environ.get("MAX_INTERACTIONS", "40"))
MAX_TASKS      = int(os.environ.get("MAX_TASKS", "0"))
MEM_FILE       = os.environ.get("HYDRA_MEM_FILE", "/tmp/hydra_episodic.json")
HYDRA_KEY      = (os.environ.get("HYDRA_DB_API_KEY", "")
                  or os.environ.get("HYDRADB_API_KEY", "")
                  or os.environ.get("HYDRA_API_KEY", "")).strip()
RECALL_K       = int(os.environ.get("RECALL_K", "3"))

ALL_APPS = ["venmo", "splitwise", "spotify", "gmail", "amazon",
            "simple_note", "todoist", "file_system", "phone"]

# ── prompts ──────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """\
You are an autonomous coding agent in AppWorld. Complete tasks by writing Python code.

AVAILABLE API ENDPOINTS — use these EXACT names (lowercase app_name, exact api_name):
venmo: show_account, show_profile, search_users, show_venmo_balance, add_to_venmo_balance, withdraw_from_venmo_balance, show_transactions, create_transaction, show_transaction, update_transaction, show_payment_cards, add_payment_card, show_payment_requests, create_payment_request, approve_payment_request, deny_payment_request, show_social_feed, show_notifications
splitwise: show_account, show_profile, search_users, show_groups, create_group, show_group, add_member_to_group, remove_member_from_group, record_expense, show_expense, delete_expense, update_expense, show_group_expenses, record_payment, show_payment, show_person_balance, show_people_balance, show_group_balance, settle_up, show_notifications
spotify: show_account, show_profile, search_songs, show_song, like_song, unlike_song, show_liked_songs, search_albums, show_album, like_album, search_playlists, create_playlist, show_playlist, delete_playlist, update_playlist, add_song_to_playlist, remove_song_from_playlist, show_downloaded_songs, download_song, show_following_artists, follow_artist, unfollow_artist, review_song, show_premium_plans, show_premium_subscriptions, subscribe_premium
gmail: show_account, show_profile, search_users, show_inbox_threads, show_outbox_threads, show_archived_threads, show_spam_threads, show_category_sizes, show_thread, delete_thread, show_email, label_thread, mark_thread_read, mark_thread_archived, mark_thread_starred, send_email, reply_to_email, forward_email_from_thread, show_drafts, create_draft, show_draft, delete_draft, update_draft, send_email_from_draft, download_attachment, upload_attachments_to_draft
amazon: show_account, show_profile, show_product, search_sellers, search_product_types, search_products, show_cart, add_product_to_cart, delete_product_from_cart, update_product_quantity_in_cart, show_wish_list, add_product_to_wish_list, delete_product_from_wish_list, show_orders, place_order, show_order, show_payment_cards, add_payment_card, show_addresses, add_address, show_product_reviews, write_product_review, show_prime_plans, show_prime_subscriptions, subscribe_prime
simple_note: show_account, show_profile, search_notes, create_note, show_note, delete_note, update_note, add_content_to_note
todoist: show_account, show_profile, search_users, show_projects, create_project, show_project, delete_project, update_project, show_sections, create_section, show_tasks, create_task, show_task, delete_task, update_task, show_sub_tasks, create_sub_task, search_labels, create_label, add_label_to_task, remove_label_from_task, show_task_comments, post_task_comment
file_system: show_account, show_profile, show_directory, create_directory, delete_directory, directory_exists, show_file, create_file, delete_file, update_file, file_exists, copy_file, move_file, compress_directory, decompress_file
phone: show_account, show_profile, show_contact_relationships, search_contacts, add_contact, delete_contact, update_contact, show_text_message_window, search_text_messages, show_text_message, send_text_message, show_alarms, create_alarm, show_alarm, delete_alarm, update_alarm, show_voice_message_window, send_voice_message, get_current_date_and_time
supervisor: complete_task, show_profile, show_account_passwords

RULES:
1. ONE Python code block per turn, nothing else.
2. To see parameters/response fields for an endpoint:
       print(apis.api_docs.show_api_doc(app_name='gmail', api_name='show_drafts'))
   Use the EXACT lowercase app_name and api_name from the list above.
   Read each doc AT MOST ONCE — the output stays in your conversation history.
   After reading a doc, your NEXT code block must make the actual API call.
3. NEVER guess field names or IDs — look them up from API responses.
4. BATCH multiple calls into one block to save steps.
5. On error: read the traceback, fix params, retry.
6. ACTION TASKS — if task says send/order/disable/add/delete/create, you MUST perform the write.
   Read data first to get IDs, then call the write endpoint.
7. To finish the task: apis.supervisor.complete_task(answer=<value or None>)
   - No question asked → answer=None
   - Question asked → answer must not be None
   - Currency: "$X.XX" | Count: integer string | List: comma-separated
8. Call complete_task() ONLY after ALL actions are fully done.

TASK: {task}
STEP: {steps_used}/40 used. {budget_warning}

MEMORY (similar past tasks — adapt to THIS task):
{memory}

KEY FACTS FROM PREVIOUS STEPS:
{facts}

TOKEN VARIABLES (pre-set in environment — use directly, no need to reassign):
{tokens}

EXAMPLE:
Task: "Send $15 to Alice (username alice99) on Venmo for lunch."
```python
alice = apis.venmo.search_users(access_token=venmo_token, query='alice99')
apis.venmo.create_transaction(access_token=venmo_token, receiver_id=alice[0]['id'], amount=15.00, description='lunch', private=False)
apis.supervisor.complete_task(answer=None)
```
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
def _embed(_text: str):
    return None  # OpenRouter does not expose an embeddings endpoint; use text-based recall


def _norm(v: list[float]) -> float:
    return math.sqrt(sum(x * x for x in v)) or 1.0


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (_norm(a) * _norm(b))


# ── episodic memory backends ────────────────────────────────────────────────
class LocalBackend:
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
    def __init__(self, key: str):
        from hydra_db import HydraDB
        self.client = HydraDB(token=key)
        self.tenant = os.environ.get("HYDRA_TENANT", "appworld")
        self.sub = EXPERIMENT

    def add(self, episode: dict) -> None:
        try:
            self.client.upload.add_memory(
                tenant_id=self.tenant, sub_tenant_id=self.sub, upsert=True,
                memories=[{
                    "text": episode_text(episode),
                    "title": (episode.get("task") or "")[:80],
                    "infer": False,
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
                ep = parse_episode_text(getattr(ch, "chunk_content", "") or "")
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
def _create_completion(messages, system=None, max_tokens=4096):
    msgs = ([{"role": "system", "content": system}] if system else []) + messages
    kwargs = dict(model=MODEL, messages=msgs)
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
    if steps_used >= 30:
        remaining = MAX_INTERACTIONS - steps_used
        budget_warning = (
            f"⚠️ ONLY {remaining} STEPS LEFT — batch all remaining calls, "
            f"call apis.supervisor.complete_task() immediately."
        )
    elif steps_used >= 20:
        budget_warning = "⚠️ Over halfway — start wrapping up. Avoid re-reading docs you already have."
    else:
        budget_warning = ""

    facts_str = "\n".join(working_memory.get("facts", [])[-8:]) or "none yet"
    tokens_str = ", ".join(
        f"{app}_token" if working_memory["tokens"].get(app)
        else f"{app}: login failed"
        for app in ALL_APPS
    )
    system = SYSTEM_PROMPT.format(
        task=working_memory.get("task", ""),
        steps_used=steps_used,
        budget_warning=budget_warning,
        memory=working_memory.get("memory", ""),
        facts=facts_str,
        tokens=tokens_str,
    )
    resp = _create_completion(messages, system=system, max_tokens=4096)
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
                f"Fix the code and try again. Check the api_doc if unsure of params."
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

    # Pre-execute token variables into AppWorld so they're always in scope
    token_setup_lines = [f"{app}_token = {tokens[app]!r}" for app in ALL_APPS if tokens.get(app)]
    if token_setup_lines:
        world.execute("\n".join(token_setup_lines))

    first_user_msg = (
        f"Supervisor: {supervisor}\n\n"
        f"Task: {task_text}\n\n"
        "Token variables are already set in the environment "
        "(venmo_token, gmail_token, amazon_token, phone_token, splitwise_token, etc.).\n\n"
        "Begin. One Python code block per turn. Batch calls where possible."
    )

    messages = [{"role": "user", "content": first_user_msg}]
    success = False

    for step in range(MAX_INTERACTIONS):
        working_memory["current_step"] = step
        reply, output = execute_with_retry(world, messages, working_memory, step)

        short_out = str(output)[:200]
        log(f"  step {step+1}: {short_out!r}")

        for call in re.findall(r"apis\.\w+\.\w+\(", extract_code(reply)):
            working_memory["calls"].append(call.rstrip("("))

        working_memory["facts"].append(f"step {step+1}: {short_out}")
        if len(working_memory["facts"]) > 10:
            working_memory["facts"] = working_memory["facts"][-10:]

        if any(ind in output for ind in ["Error", "Exception", "Traceback"]):
            working_memory["errors"].append(f"step {step+1}: {short_out}")

        messages.append({"role": "assistant", "content": reply})

        # If the output looks like an API doc, push the model to act on it now
        is_doc_output = ('"app_name"' in output and '"api_name"' in output
                         and '"parameters"' in output)
        user_content = f"Execution output:\n{output}"
        if is_doc_output:
            user_content += (
                "\n\n[You just read an API doc. Now write code that USES those "
                "parameters to make the actual API call. Do NOT re-read this doc.]"
            )
        messages.append({"role": "user", "content": user_content})

        if world.task_completed():
            log("  ✓ task_completed")
            success = True
            break
    else:
        log("  ✗ hit MAX_INTERACTIONS without completion")

    try:
        calls_seq = " -> ".join(dict.fromkeys(working_memory["calls"]))
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
