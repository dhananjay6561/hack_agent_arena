# ://agent_arena — Battle Plan v2
> AppWorld Hackathon | Beat 48.8% TGC | **Brain: `gpt-5.5` (primary) or `gpt-5.5-pro` (max power)**
> Updated with audit findings + 4 missing improvements

---

## 1. What This Hackathon Actually Is

```
Given:    working but dumb agent (agent.py) + AppWorld environment
Goal:     make agent complete more tasks → higher TGC %
Scored:   TGC = % of 168 test_normal tasks fully completed
          SGC = tiebreaker (% of scenarios where ALL 3 variants pass)
Win:      beat 48.8% TGC (ReAct + GPT-4o baseline)
Bonus:    integrate HydraDB → extra credit
```

### The environment

| Stat | Value |
|---|---|
| Apps | 9 (Spotify, Gmail, Venmo, Amazon, Splitwise, Phone, FileSystem, SimpleNote, Todoist) |
| APIs | 457 total (~50/app) |
| People | ~100 simulated users |
| Task splits | Train: 105, Dev: 60, Test-Normal: 168, Test-Challenge: 417 |
| Avg task (normal) | 1.5 apps, 8.2 unique APIs, 42.5 API calls |
| Max task (normal) | 3 apps, 17 unique APIs, 244 API calls |

### How the agent works

```
supervisor gives NL task
  → agent writes Python code
  → code calls APIs via apis.{app}.{method}()
  → print() → observation back to agent
  → repeat until apis.supervisor.complete_task(answer=X)
```

---

## 2. Score Landscape

| Method | TGC (normal) | Notes |
|---|---|---|
| ReAct + GPT-4o | 48.8% | **baseline to beat** |
| ReAct + o1 | ~56% | better reasoning |
| LOOP (Apple RL, Qwen2.5-32B) | 71% | RL-finetuned, 2025 |
| SAGE (RL + skill library) | **72%** | current SOTA |

**Key insight from LOOP paper:** RL agents beat prompt agents by learning to:
- Consult API docs 60% more often
- Make 30% fewer unwarranted assumptions
- Recover from setbacks instead of failing silently

We replicate this behavior through prompt engineering + architecture, not RL.

---

## 2b. Model Selection (OpenAI API)

| Model | Reasoning | Tool use | Agentic benchmark | Verdict |
|---|---|---|---|---|
| `gpt-4o` | ✗ | Good | — | Baseline we're beating |
| `gpt-4.1` | ✗ | Great | — | Old fallback, superseded |
| `o4-mini` | ✓ | Great | — | Old recommendation, superseded |
| `gpt-5.5` | ✓ | Best | **82.7% Terminal-Bench 2.0** | **Primary — use this** |
| `gpt-5.5-pro` | ✓✓ | Best | Best-in-class | **Max power — use if available** |

**Use `gpt-5.5`.** It's OpenAI's newest frontier model released April 23, 2026, purpose-built for agentic tasks — long-horizon work, multi-step reasoning, tool use, and code execution. It scored 82.7% on Terminal-Bench 2.0 which specifically tests complex command-line workflows requiring planning, iteration, and tool coordination — exactly what AppWorld is.

**Use `gpt-5.5-pro` if you have access.** It's the higher-compute variant that thinks harder. Some requests may take several minutes — use background/async mode to avoid timeouts.

```python
# agent.py — model config
PRIMARY_MODEL = "gpt-5.5"       # ← use this
MAX_MODEL     = "gpt-5.5-pro"   # ← if you have Pro API access

# gpt-5.5 reasoning effort: none | low | medium (default) | high | xhigh
client.chat.completions.create(
    model=PRIMARY_MODEL,
    reasoning_effort="high",     # go high — we want best performance
    messages=[...]
)
```

> **`reasoning_effort="high"`** for AppWorld. The 30-step limit is per task, not per second — thinking harder per step means fewer wasted steps overall. Use `"xhigh"` only if you have `gpt-5.5-pro` and async mode enabled.

### Revised score projection (corrected from v1)

| What we implement | Expected TGC |
|---|---|
| Baseline (starter, GPT-4o) | 48.8% |
| + better system prompt + pre-login + few-shot | ~54-56% |
| + keyword API index + app router | ~58-62% |
| + plan-execute (PEV) + working memory | ~63-67% |
| + error retry + hard verifier + answer normalization | ~67-70% |
| + step budget awareness + batch calls | +1-2% |
| + HydraDB (if useful) | +1-2% |

**Realistic target: 65-70% TGC**
**Stretch: 70%+ with aggressive prompting + HydraDB**

> ⚠️ v1 projection math was off — our baseline is 48.8% (given), not 30-35%. Each phase adds on top of that.

---

## 3. Why Vanilla ReAct Fails

| Failure mode | What happens | Frequency |
|---|---|---|
| Blind API discovery | Guesses wrong endpoint, wastes turns | High |
| No upfront plan | Gets lost mid-task on multi-step workflows | High |
| Assumes API behavior | Wrong params, wrong field names | High |
| No memory across turns | Re-fetches same data in same task | Medium |
| Login overhead per turn | Wastes 2-3 turns re-authenticating | Medium |
| Context drift | Forgets original goal after 10+ turns | Medium |
| Silent failure | Calls complete_task() without verifying | Low-Medium |
| Wrong answer format | `"$47.5"` vs `"$47.50"` fails SGC variants | Low-Medium |
| Hits step limit | 30-step wall reached before task done | Medium |

---

## 4. Our Architecture: Plan-Execute-Verify (PEV)

```
┌─────────────────────────────────────────────────────────┐
│                     TASK STARTUP                         │
│  1. Login ALL 9 apps (turn 0, runs once)                 │
│  2. Build API Index (keywords → API names, cached)       │
│  3. Load task from supervisor                            │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                    PLANNER LLM                           │
│  Input:  NL task                                         │
│  Output: JSON plan                                       │
│    {                                                     │
│      apps_needed: [venmo, splitwise],                    │
│      steps: [                                            │
│        {step: "get user id of John", app: "venmo"},      │
│        {step: "check balance", app: "venmo"},            │
│        {step: "send $20 to John", app: "venmo"}          │
│      ],                                                  │
│      answer_expected: true/false,                        │
│      answer_type: "currency|count|list|name|none"        │
│    }                                                     │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   EXECUTOR (ReAct loop)                  │
│  Per step:                                               │
│   1. Retrieve relevant APIs from index (top-5)           │
│   2. Fetch api_doc for those APIs                        │
│   3. Generate + execute Python code                      │
│      → BATCH multiple API calls per code block           │
│   4. Observe output → update working_memory dict         │
│   5. On error → retry with error context (max 3x)        │
│   6. At step 20/30 → inject step-budget warning          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                    VERIFIER                              │
│  Before complete_task():                                 │
│   - Re-read original task                               │
│   - If task has question word → answer must not be None  │
│   - Normalize answer format (see §9)                     │
│   - Confirm no collateral damage likely                  │
│   - If uncertain → do one more check API call            │
└─────────────────────────────────────────────────────────┘
```

---

## 5. The API Discovery Problem

**Problem:** 457 APIs. Agent can't brute-force discover every turn. Default ReAct wastes 3-5 turns on API discovery alone.

### Approach A: Static Keyword Index (primary)

```python
# Boot time: build index once
API_INDEX = {}
for app in ALL_APPS:
    descriptions = apis.api_docs.show_api_descriptions(app_name=app)
    for api in descriptions:
        for keyword in tokenize(api['description'] + api['name']):
            API_INDEX[keyword].append((app, api['name']))

# Per step: retrieve relevant APIs
def get_relevant_apis(task_text, top_k=5):
    keywords = extract_keywords(task_text)
    candidates = Counter()
    for kw in keywords:
        for (app, name) in API_INDEX.get(kw, []):
            candidates[(app, name)] += 1
    return candidates.most_common(top_k)
```

No embeddings needed. Pure keyword overlap. Fast.

### Approach B: App Router (before API search)

```python
APP_HINTS = {
    "pay": ["venmo", "splitwise"],
    "transfer": ["venmo"],
    "music": ["spotify"],
    "playlist": ["spotify"],
    "email": ["gmail"],
    "send": ["gmail", "venmo"],
    "note": ["simplenote"],
    "todo": ["todoist"],
    "file": ["filesystem"],
    "call": ["phone"],
    "contact": ["phone"],
    "buy": ["amazon"],
    "order": ["amazon"],
    "split": ["splitwise"],
    "expense": ["splitwise"],
}

def route_task_to_apps(task: str) -> list[str]:
    task_lower = task.lower()
    apps = set()
    for hint, app_list in APP_HINTS.items():
        if hint in task_lower:
            apps.update(app_list)
    return list(apps) or ALL_APPS
```

### Approach C: API Dependency Pre-mapping

Some APIs always chain. Pre-know these:

```python
API_CHAINS = {
    "venmo": ["login", "get_user_by_username", "send_money"],
    "gmail": ["login", "list_messages", "get_message"],
    "splitwise": ["login", "get_friends", "create_expense"],
    "spotify": ["login", "show_song_library", "show_album_library"],
    "phone": ["login", "list_contacts", "send_sms"],
}
```

When executor hits a step, inject the known chain so it doesn't rediscover.

### Approach D: Exploration Cache (per-session)

```python
EXPLORED_APIS = {}

def get_api_doc(app, api_name):
    if (app, api_name) not in EXPLORED_APIS:
        EXPLORED_APIS[(app, api_name)] = apis.api_docs.show_api_doc(
            app_name=app, api_name=api_name
        )
    return EXPLORED_APIS[(app, api_name)]
```

Never fetch the same doc twice per session.

---

## 6. Working Memory Pattern

Pass a dict every turn instead of relying on LLM to remember:

```python
working_memory = {
    "task": "Pay John $20 on Venmo for pizza",
    "plan": [...],
    "current_step": 2,
    "steps_remaining": 28,        # ← track budget
    "logged_in": ["venmo", "splitwise", "gmail"],
    "known_ids": {
        "my_venmo_id": "usr_abc123",
        "john_venmo_id": "usr_xyz789",
    },
    "facts": [
        "John's username is john_doe",
        "Current venmo balance: $47.50",
    ],
    "errors": [
        "venmo.send_money failed: missing memo field"
    ],
    "completed_steps": [0, 1],
    "answer_type": "currency",    # ← from planner
}
```

Injected into every LLM prompt — no context drift.

---

## 7. System Prompt Design

```
You are an autonomous agent in AppWorld. Complete tasks by writing Python
code that calls the `apis` object.

RULES:
1. ALWAYS check api_docs before calling any API you haven't used before
2. NEVER assume field names — read the doc
3. NEVER assume user IDs — look them up
4. After each API call: extract relevant data → update working_memory
5. If API call fails: read the error → fix params → retry (max 3x)
6. Before complete_task(): re-read original task, verify all steps done
7. If task has a question word (what/how many/which/who):
   answer MUST NOT be None — find the exact value
8. BATCH multiple related API calls in one code block when possible
9. One Python block per turn. Use print() for all observations.

STARTUP (do once at turn 0):
- login to ALL apps using apis.supervisor.show_account_passwords()
- build api keyword index from api_docs

FORMAT:
Thought: [what I know, what I need to do next, steps remaining]
Code:
```python
# your code here — batch multiple calls per block
print(result)
```

--- EXAMPLE TASK (follow this pattern) ---

Task: "Send $15 to Alice on Venmo for lunch. Her username is alice99."

Turn 1 — Thought: I need to login and get Alice's user ID, then send money.
Code:
```python
creds = apis.supervisor.show_account_passwords()
token = apis.venmo.login(
    username=creds['venmo']['username'],
    password=creds['venmo']['password']
)['access_token']
alice = apis.venmo.get_user_by_username(
    access_token=token, username='alice99'
)
print(f"token={token}, alice_id={alice['id']}")
```

Turn 2 — Thought: I have alice_id. Now send $15.
Code:
```python
result = apis.venmo.send_money(
    access_token=token,
    user_id=alice_id,
    amount=15.00,
    note="lunch"
)
print(result)
```

Turn 3 — Thought: Payment confirmed. Task had no question → answer=None.
Code:
```python
apis.supervisor.complete_task(answer=None)
```
--- END EXAMPLE ---
```

---

## 8. Error Recovery Protocol

```python
def execute_with_retry(code: str, max_retries: int = 3) -> str:
    for attempt in range(max_retries):
        result = execute_code(code)
        if "Error" not in result and "Exception" not in result:
            return result
        error_context = f"Attempt {attempt+1} failed: {result}"
        code = llm_fix_code(original_intent, code, error_context)
    return "FAILED_AFTER_RETRIES"
```

On retry, inject:
- Original intent
- Failed code
- Full error message
- Relevant api_doc (re-fetch fresh)

---

## 9. Answer Normalization (NEW — fixes SGC)

SGC requires ALL 3 task variants to pass. Most variant failures are answer
format mismatches. Add a post-processor before `complete_task()`:

```python
def normalize_answer(raw_answer, answer_type: str) -> str:
    if answer_type == "currency":
        # "$47.5" → "$47.50", "47.50" → "$47.50"
        amount = float(str(raw_answer).replace("$", "").replace(",", ""))
        return f"${amount:.2f}"

    if answer_type == "count":
        # "3.0" → "3", "three" → look up
        return str(int(float(raw_answer)))

    if answer_type == "list":
        # Normalize separators: "A,B" → "A, B"
        items = [x.strip() for x in str(raw_answer).split(",")]
        return ", ".join(items)

    if answer_type == "name":
        # Strip extra whitespace, preserve case
        return str(raw_answer).strip()

    return raw_answer  # fallback: return as-is
```

The planner sets `answer_type` in its JSON output. The verifier calls
`normalize_answer()` before `complete_task()`.

---

## 10. Step Budget Awareness (NEW)

The agent has 30 steps max. Inject a warning at step 20 to force urgency:

```python
def build_prompt(working_memory, observation):
    steps_used = working_memory["current_step"]
    prompt = f"Working memory: {working_memory}\nObservation: {observation}\n"

    if steps_used >= 20:
        remaining = 30 - steps_used
        prompt += f"""
⚠️ BUDGET WARNING: {remaining} steps left.
- Skip any remaining discovery steps
- Batch all remaining API calls into one block
- Move directly to complete_task() as soon as possible
"""
    return prompt
```

Also: explicitly tell the agent it can batch multiple API calls per block.
This alone reduces avg steps per task significantly.

---

## 11. Verifier (Hardened — was underdefined in v1)

```python
def verify_before_complete(task: str, working_memory: dict) -> dict:
    """
    Returns: {ok: bool, answer: str|None, reason: str}
    """
    task_lower = task.lower()
    question_words = ["what", "how many", "which", "who", "when", "where",
                      "list", "give me", "tell me"]

    answer = working_memory.get("answer")
    answer_type = working_memory.get("answer_type", "none")

    # Hard rule: question task → must have answer
    has_question = any(qw in task_lower for qw in question_words)
    if has_question and (answer is None or answer == ""):
        return {
            "ok": False,
            "reason": "Task asks a question but answer is None — keep searching"
        }

    # Normalize the answer format
    if answer is not None:
        answer = normalize_answer(answer, answer_type)

    # Check all plan steps are marked complete
    plan_steps = working_memory.get("plan", [])
    completed = set(working_memory.get("completed_steps", []))
    if len(completed) < len(plan_steps):
        missing = [i for i in range(len(plan_steps)) if i not in completed]
        return {
            "ok": False,
            "reason": f"Steps {missing} not yet completed"
        }

    return {"ok": True, "answer": answer, "reason": "All checks passed"}
```

---

## 12. Batching API Calls (NEW)

Vanilla ReAct does one API call per code block = one step per call.
For a task with 42 avg API calls that's 42 steps — hitting the 30-step wall.

**Explicitly instruct the agent to batch:**

```
When multiple API calls are logically sequential and you already know the
params for each, write them ALL in one code block:

# GOOD — 3 calls, 1 step
library = apis.spotify.show_song_library(access_token=token)
albums = apis.spotify.show_album_library(access_token=token)
playlists = apis.spotify.show_playlist_library(access_token=token)
print(library, albums, playlists)

# BAD — same 3 calls across 3 steps (wastes budget)
```

The API chains in §5C also help here — when you know the chain upfront,
you can pre-batch the whole sequence.

---

## 13. HydraDB Integration (Bonus)

Ask organizers what HydraDB is. Based on name — likely structured DB for agent state.

**If it's a key-value / document store:** Use it as persistent working_memory across tasks:

```python
# Store successful API call patterns
hydra.set("venmo:send_pattern", {params_that_worked})
pattern = hydra.get("venmo:send_pattern")
```

**If it's a vector store:** Use it as semantic API retrieval instead of keyword index:

```python
# At boot: embed all 457 API docs → store in HydraDB
# Per step: query with task text → get top-k relevant APIs
```

Cross-task learning: if task A discovers "John's venmo ID is usr_xyz",
store that. If task B needs John's ID, retrieve it without re-fetching.

---

## 14. Implementation Phases

### Phase 1: Foundation (Day 1, ~3hrs) → target ~54-56% TGC
- [ ] Read agent.py fully
- [ ] Run `appworld play` — hand-solve 3-5 tasks to understand API patterns
- [ ] Implement pre-login at startup (all 9 apps, turn 0)
- [ ] Implement working_memory dict with steps_remaining
- [ ] Rewrite system prompt (force api_doc check, add few-shot example)
- [ ] Test on dev set (60 tasks) → get baseline score
- [ ] Set up parallel runner (4-5 tasks concurrent) for fast iteration

### Phase 2: API Discovery (Day 1-2, ~3hrs) → target ~58-62% TGC
- [ ] Build static keyword API index at boot
- [ ] Implement App Router (task → apps)
- [ ] Add API dependency chains (pre-map known sequences)
- [ ] Implement exploration cache (never re-fetch same doc)
- [ ] Test delta on dev set

### Phase 3: Plan-Execute (Day 2, ~4hrs) → target ~63-67% TGC
- [ ] Implement Planner LLM call (outputs JSON plan with answer_type)
- [ ] Executor follows plan step-by-step
- [ ] Per-step API retrieval from index
- [ ] Inject batching instructions into prompt
- [ ] Test delta on dev set

### Phase 4: Verifier + Error Recovery (Day 2-3, ~3hrs) → target ~67-70% TGC
- [ ] Add hardened verifier (question-word check + normalize answer)
- [ ] Add answer normalization by type (currency/count/list/name)
- [ ] Add step-budget warning at step 20
- [ ] Add retry loop with error context re-injection (max 3x)
- [ ] Final test on dev set

### Phase 5: Submit
```bash
export APPWORLD_DATASET=test_normal MAX_TASKS=0 && python agent.py
appworld evaluate $APPWORLD_EXPERIMENT test_normal
# Zip experiments/outputs/$APPWORLD_EXPERIMENT/ and submit
```

---

## 15. Quick Reference: AppWorld API Patterns

```python
# Get credentials
creds = apis.supervisor.show_account_passwords()

# Discover APIs
apis.api_docs.show_api_descriptions(app_name='venmo')
apis.api_docs.show_api_doc(app_name='venmo', api_name='send_money')

# Login pattern
token = apis.venmo.login(
    username=creds['venmo']['username'],
    password=creds['venmo']['password']
)['access_token']

# Complete task
apis.supervisor.complete_task(answer="$47.50")  # question task
apis.supervisor.complete_task(answer=None)       # action-only task
```

---

## 16. Key Files

```
hack_agent_arena/
├── agent.py              ← main file we edit
├── .env                  ← ANTHROPIC_API_KEY here
├── setup.sh              ← run once
└── experiments/
    └── outputs/
        └── team_himanshu/
            ├── evaluations/test_normal.json   ← submit this
            └── tasks/*/dbs/                   ← submit this folder
```

---

## TL;DR

```
Beat 48.8% TGC by:

CORE (Phase 1-2):
1. Pre-login all apps once at startup
2. Few-shot example in system prompt (concrete trace)
3. Keyword API index + App Router → smart retrieval
4. Working memory dict → no context drift

ADVANCED (Phase 3-4):
5. Planner decomposes task → JSON plan with answer_type
6. Batch multiple API calls per code block
7. Step-budget warning at step 20 of 30
8. Hard verifier: question word → answer must not be None
9. Answer normalization by type → fixes SGC variant failures
10. Error retry with re-injection (max 3x)

Target: 65-70% TGC | Stretch: 70%+
```
