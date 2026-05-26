#!/usr/bin/env bash
# Claude Code status line — three-line layout
# Line 1: Model | Ctx Used | Cost | Session duration
# Line 2: git branch | git tree icon + main
# Line 3: PR number (if any)

input=$(cat)

# --- Line 1: Model, context, cost, session ---
model=$(echo "$input" | jq -r '.model.display_name // "Unknown"')

used_pct=$(echo "$input" | jq -r '.context_window.used_percentage // empty')
if [ -n "$used_pct" ]; then
  ctx_str=$(printf "%.1f%%" "$used_pct")
else
  ctx_str="0.0%"
fi

# Cost: sum input + output tokens and estimate cost (we don't have cost directly, so leave as $0.00 placeholder unless available)
total_in=$(echo "$input" | jq -r '.context_window.total_input_tokens // 0')
total_out=$(echo "$input" | jq -r '.context_window.total_output_tokens // 0')
# Approximate cost using claude-sonnet-4 pricing: $3/1M input, $15/1M output
cost=$(awk "BEGIN { printf \"%.2f\", ($total_in * 3 / 1000000) + ($total_out * 15 / 1000000) }")

# Session duration: use transcript_path mtime vs now
transcript=$(echo "$input" | jq -r '.transcript_path // empty')
if [ -n "$transcript" ] && [ -f "$transcript" ]; then
  start_epoch=$(stat -f %B "$transcript" 2>/dev/null || stat -c %W "$transcript" 2>/dev/null)
  now_epoch=$(date +%s)
  elapsed=$(( now_epoch - start_epoch ))
  if [ "$elapsed" -lt 60 ]; then
    duration="<1m"
  elif [ "$elapsed" -lt 3600 ]; then
    duration="$(( elapsed / 60 ))m"
  else
    duration="$(( elapsed / 3600 ))h$(( (elapsed % 3600) / 60 ))m"
  fi
else
  duration="<1m"
fi

line1="Model: $model | Ctx Used: $ctx_str | Cost: \$$cost | Session: $duration"

# --- Line 2: git branch and relation to main ---
cwd=$(echo "$input" | jq -r '.cwd // .workspace.current_dir // ""')

branch=""
main_rel=""
if [ -n "$cwd" ] && git -C "$cwd" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  branch=$(git -C "$cwd" rev-parse --abbrev-ref HEAD 2>/dev/null)

  # Determine tree icon: ahead/behind relative to main
  ahead=$(git -C "$cwd" rev-list --count origin/main..HEAD 2>/dev/null || git -C "$cwd" rev-list --count main..HEAD 2>/dev/null || echo "0")
  behind=$(git -C "$cwd" rev-list --count HEAD..origin/main 2>/dev/null || git -C "$cwd" rev-list --count HEAD..main 2>/dev/null || echo "0")

  if [ "$ahead" -gt 0 ] && [ "$behind" -gt 0 ]; then
    tree_icon="↕"   # diverged
  elif [ "$ahead" -gt 0 ]; then
    tree_icon="↑"   # ahead of main
  elif [ "$behind" -gt 0 ]; then
    tree_icon="↓"   # behind main
  else
    tree_icon="="   # up to date
  fi

  main_rel="$tree_icon main"
fi

if [ -n "$branch" ]; then
  line2="\\ $branch | $main_rel"
else
  line2=""
fi

# --- Line 3: PR number ---
pr_line=""
if [ -n "$cwd" ] && command -v gh >/dev/null 2>&1; then
  pr_num=$(git -C "$cwd" --no-optional-locks rev-parse --abbrev-ref HEAD 2>/dev/null \
    | xargs -I{} gh pr list --head {} --json number --jq '.[0].number' 2>/dev/null)
  if [ -n "$pr_num" ] && [ "$pr_num" != "null" ]; then
    pr_line="PR #$pr_num"
  fi
fi

# --- Output ---
echo "$line1"
[ -n "$line2" ] && echo "$line2"
[ -n "$pr_line" ] && echo "$pr_line"
