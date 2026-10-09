#!/usr/bin/env bash
# Install p3-stack skills and p3-mode hooks for T3 Code.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_PY="$ROOT/hooks/install.py"

# Claude Code ignores .agents/skills and reads <config dir>/skills. Print the
# config dir of every enabled Claude instance in T3 Code, resolved as T3 does:
# the instance's homePath, else CLAUDE_CONFIG_DIR, else ~/.claude.
claude_config_dirs() {
  if ! command -v python3 >/dev/null; then
    printf 'skip claude (python3 not found to read T3 Code settings)\n' >&2
    return 0
  fi
  python3 -I "$INSTALL_PY" claude-dirs
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

unlink_skills() {
  local target="$1" removed=0 link
  [[ -d "$target" ]] || return 0
  for link in "$target"/*; do
    if [[ -L "$link" && "$(readlink "$link")" == "$ROOT"/skills/* ]]; then
      rm "$link"
      removed=$((removed + 1))
    fi
  done
  printf 'unlinked %d skills from %s\n' "$removed" "$target"
}

install_hooks() {
  if command -v python3 >/dev/null; then
    python3 -I "$INSTALL_PY" hooks "$@"
  else
    printf 'skip hooks (python3 not found)\n' >&2
  fi
}

claude_dirs="$(claude_config_dirs)"

if [[ "${1:-}" == "--uninstall" ]]; then
  unlink_skills "$HOME/.agents/skills"
  while IFS= read -r dir; do
    if [[ -n "$dir" ]]; then
      unlink_skills "$dir/skills"
    fi
  done <<< "$claude_dirs"
  install_hooks --uninstall
elif [[ "${1:-}" == "--project" ]]; then
  project="${2:?usage: ./install.sh --project /path/to/repo}"
  link_skills "$project/.agents/skills"
  if [[ -n "$claude_dirs" ]]; then
    link_skills "$project/.claude/skills"
  fi
  install_hooks
else
  link_skills "$HOME/.agents/skills"
  while IFS= read -r dir; do
    if [[ -n "$dir" ]]; then
      link_skills "$dir/skills"
    fi
  done <<< "$claude_dirs"
  install_hooks
fi
