#!/usr/bin/env bash
# -------------------------------------------------------------
# why3_run.sh  —  build, bench, and replay a Why3 session
#
# Usage:  ./why3_run.sh human_eval_003
# -------------------------------------------------------------
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: $0 <why3_module_basename>" >&2
  exit 1
fi

NAME="$1"                # e.g. human_eval_003
MLW_FILE="${NAME}.mlw"   # e.g. human_eval_003.mlw

# Check that the .mlw file exists
if [ ! -f "$MLW_FILE" ]; then
  echo "Error: file '$MLW_FILE' not found." >&2
  exit 1
fi

echo "=== Creating Why3 session for ${MLW_FILE} ==="
why3 session create \
     -a split_vc -a split_vc -a split_vc  \
     -L . \
     -P alt-ergo:z3:cvc4 \
     --timelimit=10 \
     -o "$NAME" \
     "$MLW_FILE"

echo "=== Benchmarking session (${NAME}) ==="
why3 bench -L . -f "$NAME"

why3 session info --session-stats "$MLW_FILE"

#echo "=== Replaying proofs (${NAME}) ==="
#why3 replay "$NAME"

echo "=== Done ==="

