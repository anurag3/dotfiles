#!/usr/bin/env bash
# Claude Code status line — two-line layout
# Line 1: Model | Ctx Used | Cost | Session duration
# Line 2: git repo | branch | worktree

input=$(cat)

# --- Line 1: Model, context, cost, session duration ---
model=$(echo "$input" | jq -r '.model.display_name // "Unknown"')

used_pct=$(echo "$input" | jq -r '.context_window.used_percentage // empty')
if [ -n "$used_pct" ]; then
  ctx_str=$(printf "%.1f%%" "$used_pct")
else
  ctx_str="0.0%"
fi

# Cost: prefer the official total_cost_usd field; fall back to a token-based estimate.
cost=$(echo "$input" | jq -r '.cost.total_cost_usd // empty')
if [ -n "$cost" ]; then
  cost=$(printf "%.2f" "$cost")
else
  total_in=$(echo "$input" | jq -r '.context_window.total_input_tokens // 0')
  total_out=$(echo "$input" | jq -r '.context_window.total_output_tokens // 0')
  # Approximate using claude-sonnet pricing: $3/1M input, $15/1M output
  cost=$(awk "BEGIN { printf \"%.2f\", ($total_in * 3 / 1000000) + ($total_out * 15 / 1000000) }")
fi

# Session duration: prefer the official total_duration_ms field; fall back to transcript mtime.
dur_ms=$(echo "$input" | jq -r '.cost.total_duration_ms // empty')
if [ -n "$dur_ms" ]; then
  elapsed=$(( dur_ms / 1000 ))
else
  transcript=$(echo "$input" | jq -r '.transcript_path // empty')
  if [ -n "$transcript" ] && [ -f "$transcript" ]; then
    start_epoch=$(stat -f %B "$transcript" 2>/dev/null || stat -c %W "$transcript" 2>/dev/null)
    now_epoch=$(date +%s)
    elapsed=$(( now_epoch - start_epoch ))
  else
    elapsed=0
  fi
fi

if [ "$elapsed" -lt 60 ]; then
  duration="<1m"
elif [ "$elapsed" -lt 3600 ]; then
  duration="$(( elapsed / 60 ))m"
else
  duration="$(( elapsed / 3600 ))h$(( (elapsed % 3600) / 60 ))m"
fi

line1="$model | $ctx_str | \$$cost | $duration"

# --- Line 2: git repo, branch, worktree ---
cwd=$(echo "$input" | jq -r '.cwd // .workspace.current_dir // ""')

repo=$(echo "$input" | jq -r '.workspace.repo | if . then .owner + "/" + .name else empty end')

branch=""
if [ -n "$cwd" ] && git -C "$cwd" --no-optional-locks rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  branch=$(git -C "$cwd" --no-optional-locks rev-parse --abbrev-ref HEAD 2>/dev/null)
fi

worktree=$(echo "$input" | jq -r '.worktree.name // .workspace.git_worktree // empty')

[ -z "$repo" ] && repo="None"
[ -z "$branch" ] && branch="None"
[ -z "$worktree" ] && worktree="None"

if [ "$STATUSLINE_NO_EMOJI" = "1" ]; then
  line2="$repo | $branch | worktree:$worktree"
else
  line2="🐙 $repo | 🌿 $branch | 🌲 $worktree"
fi

# --- Output ---
echo "$line1"
echo "$line2"
