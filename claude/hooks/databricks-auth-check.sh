#!/bin/sh
# SessionStart hook: warn when a configured Databricks CLI profile's auth has
# actually gone invalid/expired.
#
# Supplements (does not replace) the vendored
# databricks@claude-plugins-official plugin's own SessionStart hook
# (hooks/databricks-context.py), which lists configured profile *names* from
# ~/.databrickscfg but never checks whether their auth still works.
# `databricks auth profiles` does that validation itself, so this hook runs
# it and surfaces only the profiles that come back invalid.
#
# Fail-silent by design: missing `databricks`/`jq`, a CLI error, a timeout, or
# all profiles valid all exit 0 with no output. Must never block session
# start.

set -eu

databricks_bin=$(command -v databricks) || exit 0
command -v jq >/dev/null 2>&1 || exit 0

# `databricks auth profiles` validates each profile against its workspace API
# (confirmed via `databricks auth profiles --debug`: one GET
# /api/2.0/preview/scim/v2/Me per profile) -- a network call that could hang.
# Guard it with a timeout. macOS ships neither GNU `timeout` nor `gtimeout`,
# so fall back to perl's alarm() (bundled with macOS) as a portable timeout.
if command -v timeout >/dev/null 2>&1; then
  output=$(timeout 5 "$databricks_bin" auth profiles 2>/dev/null) || exit 0
elif command -v gtimeout >/dev/null 2>&1; then
  output=$(gtimeout 5 "$databricks_bin" auth profiles 2>/dev/null) || exit 0
else
  output=$(perl -e 'alarm shift; exec @ARGV' 5 "$databricks_bin" auth profiles 2>/dev/null) || exit 0
fi

# Columns are: Name, Host, Valid. Collect the invalid ones as "name|host".
invalid=$(printf '%s\n' "$output" | awk 'NR>1 && NF>=3 && $NF=="NO" {print $1"|"$2}') || exit 0
[ -z "$invalid" ] && exit 0

banner=$(printf '%s\n' "$invalid" | while IFS='|' read -r name host; do
  printf "⚠️ Databricks profile '%s' has invalid/expired auth — run 'databricks auth login --host %s --profile %s' before using it.\n" "$name" "$host" "$name"
done)
[ -z "$banner" ] && exit 0

jq -n --arg ctx "$banner" \
  '{hookSpecificOutput: {hookEventName: "SessionStart", additionalContext: $ctx}}' 2>/dev/null || exit 0
