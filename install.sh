#!/usr/bin/env bash
# Install p3-stack skills for T3 Code.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
T3_SETTINGS="${T3CODE_HOME:-$HOME/.t3}/userdata/settings.json"

# Claude Code ignores .agents/skills and reads <config dir>/skills. Print the
# config dir of every enabled Claude instance in T3 Code, resolved as T3 does:
# the instance's homePath, else CLAUDE_CONFIG_DIR, else ~/.claude.
claude_config_dirs() {
  [[ -f "$T3_SETTINGS" ]] || return 0
  if ! command -v python3 >/dev/null; then
    printf 'skip claude (python3 not found to read %s)\n' "$T3_SETTINGS" >&2
    return 0
  fi
  python3 -I - "$T3_SETTINGS" <<'PY' | sort -u
import json, os, sys
settings = json.load(open(sys.argv[1]))
instances = settings.get("providerInstances", {})
legacy = settings.get("providers", {}).get("claudeAgent", {})
instances.setdefault("claudeAgent", {"driver": "claudeAgent", "enabled": legacy.get("enabled", True), "config": legacy})
fallback = os.environ.get("CLAUDE_CONFIG_DIR", "").strip() or "~/.claude"
for instance in instances.values():
    if instance.get("driver") == "claudeAgent" and instance.get("enabled", True):
        home = instance.get("config", {}).get("homePath", "").strip() or fallback
        print(os.path.realpath(os.path.expanduser(home)))
PY
}

link_skills() {
  local target="$1" installed=0 skipped=0 skill name
  mkdir -p "$target"
  for skill in "$ROOT"/skills/*/; do
    name="$(basename "$skill")"
    if [[ -L "$target/$name" ]]; then
      rm "$target/$name"
    elif [[ -e "$target/$name" ]]; then
      printf 'skip %s (exists and is not a symlink)\n' "$name"
      skipped=$((skipped + 1))
      continue
    fi
    ln -s "$skill" "$target/$name"
    installed=$((installed + 1))
  done
  printf 'linked %d skills into %s' "$installed" "$target"
  if [[ "$skipped" -gt 0 ]]; then
    printf ' (%d skipped)' "$skipped"
  fi
  printf '\n'
}

claude_dirs="$(claude_config_dirs)"

if [[ "${1:-}" == "--project" ]]; then
  project="${2:?usage: ./install.sh --project /path/to/repo}"
  link_skills "$project/.agents/skills"
  if [[ -n "$claude_dirs" ]]; then
    link_skills "$project/.claude/skills"
  fi
else
  link_skills "$HOME/.agents/skills"
  while IFS= read -r dir; do
    if [[ -n "$dir" ]]; then
      link_skills "$dir/skills"
    fi
  done <<< "$claude_dirs"
fi
