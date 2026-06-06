# ://agent_arena — Team `sideeffects`

AppWorld agent submission for the Agents Arena Hackathon (sponsored by HydraDB).

| | |
|---|---|
| **Team name** | `sideeffects` |
| **Model** | `meta-llama/llama-3.3-70b-instruct` (via OpenRouter) |
| **Eval set** | `agent_arena_eval` (official 10-task set, 3 easy / 3 medium / 4 hard) |
| **HydraDB used?** | **Yes** — cross-task episodic memory (see below) |
| **Self-reported TGC / SGC** | _see `experiments/outputs/team_sideeffects/evaluations/agent_arena_eval.json`_ |

## The agent (`agent.py`)
A Plan–Execute–Verify ReAct code agent:
- **Pre-login** all 9 apps once at startup; access tokens injected into every task.
- **Planner** LLM call decomposes the task (apps needed, steps, answer type).
- **ReAct loop** — one Python block per turn, runtime API-doc discovery, batched calls.
- **Error retry** with the full traceback re-injected, **step-budget** warnings, and
  **answer normalization** (currency / count / list / name).

## 🐉 HydraDB integration (bonus)
The agent has a **persistent episodic memory** backed by HydraDB
([`hydra-db-python`](https://pypi.org/project/hydra-db-python/)):
- **Before** solving a task, it recalls the most similar past task trajectories
  (`client.recall.recall_preferences`) — each holds the apps used, the key API-call
  sequence, and the final answer — and injects them as worked examples.
- **After** a task completes, it stores that episode (`client.upload.add_memory`),
  so later tasks benefit from earlier ones.

This is **general** cross-task memory — no answers are keyed to specific `task_id`s.

## How to run
```bash
bash setup.sh && source .venv/bin/activate
# .env:
#   OPENROUTER_API_KEY=...      (provider)
#   HYDRA_API_KEY=...           (HydraDB)
#   MODEL=meta-llama/llama-3.3-70b-instruct
export APPWORLD_EXPERIMENT=team_sideeffects
export APPWORLD_DATASET=agent_arena_eval MAX_TASKS=0
python agent.py
appworld evaluate team_sideeffects agent_arena_eval
```

Outputs (for verification) are in `experiments/outputs/team_sideeffects/`, including
`evaluations/agent_arena_eval.json` and each task's `tasks/<id>/dbs/`.

See [`SUBMISSION.md`](SUBMISSION.md) and [`EVAL.md`](EVAL.md) for the official format.
