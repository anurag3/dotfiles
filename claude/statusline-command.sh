#!/usr/bin/env bash
# Claude Code status line in a two-line layout
# Line 1: Model | Ctx Used | Cost | Session duration
# Line 2: git repo | branch | worktree

input=$(cat)

# Read all fields with one jq call. For a bad field type, "?" gives the default value, so the other fields stay correct.
# The unit separator keeps empty fields. Tab is IFS whitespace, so read merges empty tab fields.
IFS=$'\x1f' read -r model effort used_pct cost total_in total_out dur_ms transcript cwd repo worktree < <(
  echo "$input" | jq -r '[
    (.model.display_name? // "Unknown"), (.effort.level? // ""), (.context_window.used_percentage? // ""),
    (.cost.total_cost_usd? // ""), (.context_window.total_input_tokens? // 0),
    (.context_window.total_output_tokens? // 0), (.cost.total_duration_ms? // ""),
    (.transcript_path? // ""), (.cwd? // .workspace.current_dir? // ""),
    ((.workspace.repo | if . then .owner + "/" + .name else "" end)? // ""),
    (.worktree.name? // .workspace.git_worktree? // "")
  ] | map(tostring) | join("\u001f")')

# --- Line 1: Model, context, cost, session duration ---
[ -n "$effort" ] && model="$model [$effort]"

if [ -n "$used_pct" ]; then
  ctx_str=$(printf "%.1f%%" "$used_pct")
else
  ctx_str="0.0%"
fi

# Cost: use the official total_cost_usd field. If it is not available, estimate the cost from the token counts.
if [ -n "$cost" ]; then
  cost=$(printf "%.2f" "$cost")
else
  # Estimate only. Use Sonnet list prices: $3/1M input, $15/1M output.
  cost=$(awk "BEGIN { printf \"%.2f\", ($total_in * 3 / 1000000) + ($total_out * 15 / 1000000) }")
fi

# Session duration: use the official total_duration_ms field. If it is not available, use the transcript creation time.
if [ -n "$dur_ms" ]; then
  elapsed=$(( dur_ms / 1000 ))
else
  if [ -n "$transcript" ] && [ -f "$transcript" ]; then
    if [ "$(uname)" = Darwin ]; then
      start_epoch=$(stat -f %B "$transcript" 2>/dev/null)
    else
      start_epoch=$(stat -c %W "$transcript" 2>/dev/null)
    fi
    now_epoch=$(date +%s)
    [ -z "$start_epoch" ] && start_epoch=$now_epoch
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
# Keep the cwd check. git -C "" uses the current directory.
branch=""
[ -n "$cwd" ] && branch=$(git -C "$cwd" --no-optional-locks rev-parse --abbrev-ref HEAD 2>/dev/null)

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
