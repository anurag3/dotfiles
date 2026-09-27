#!/bin/sh
# PreToolUse hook for the implementer subagent (agents/implementer.md).
#
# Blocks git commands that change the index, HEAD, or the working tree.
# Parallel implementers share one working tree. One `git stash` or
# `git checkout .` removes the uncommitted edits of all other implementers.
# The controller commits after each wave.
#
# Also matches the `rtk git ...` form that rtk-rewrite.sh produces.

set -eu

cmd=$(jq -r '.tool_input.command // empty')

if printf '%s\n' "$cmd" | grep -Eq '(^|[;&|(`[:space:]])(rtk[[:space:]]+)?git([[:space:]]+-C[[:space:]]+[^[:space:]]+)?[[:space:]]+(add|commit|stash|checkout|switch|restore|reset|clean|rebase|merge|cherry-pick|revert|pull|push)([[:space:]]|$)'; then
  echo "Blocked: implementers must not change git state. The controller commits after the wave. Report your changes instead." >&2
  exit 2
fi

exit 0
