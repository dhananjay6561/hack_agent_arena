#!/usr/bin/env bash
# Quick verify the two candidate agents (HydraDB vs MAR) on OpenRouter, then compare.
#
# Before running:
#   1) put your key in .env:   OPENROUTER_API_KEY=...   (and HYDRA_API_KEY=... for hydra)
#   2) set the model — either edit the MODEL line in each agent, or export it once here:
#        export MODEL=meta-llama/llama-3.3-70b-instruct
#
# Usage:
#   ./verify.sh                 # both agents on the OFFICIAL eval set (agent_arena_eval, 10 tasks)
#   DATASET=mixed15 ./verify.sh # or our local mixed set / dev / etc.
set -uo pipefail
cd "$(dirname "$0")"
# shellcheck disable=SC1091
source .venv/bin/activate

export APPWORLD_DATASET="${DATASET:-agent_arena_eval}"
export WORKERS="${WORKERS:-3}"
[ -n "${MAX_TASKS:-}" ] && export MAX_TASKS
LOGDIR=/tmp/arena_logs; mkdir -p "$LOGDIR"

if [ -z "${MODEL:-}" ] && ! grep -qE 'MODEL\s*=\s*os.environ.get\("MODEL",\s*"[^"]+"\)' agent_hydra.py; then
  echo "⚠️  MODEL is not set. Either 'export MODEL=...' or edit the MODEL line in the agents first."
fi

echo "Dataset=$APPWORLD_DATASET  Workers=$WORKERS  Model=${MODEL:-<set in agent file>}"
APPWORLD_EXPERIMENT=team_hydra python agent_hydra.py > "$LOGDIR/team_hydra.log" 2>&1 &
APPWORLD_EXPERIMENT=team_mar   python agent_mar.py   > "$LOGDIR/team_mar.log"   2>&1 &
wait

echo
echo "================ RESULTS ($APPWORLD_DATASET) ================"
for exp in team_hydra team_mar; do
  echo "----- $exp -----"
  appworld evaluate "$exp" "$APPWORLD_DATASET" 2>&1 | grep -E "aggregate|difficulty|type|---" || \
    echo "  (eval failed — see $LOGDIR/$exp.log)"
  echo
done
echo "Full logs: $LOGDIR/team_hydra.log  $LOGDIR/team_mar.log"
