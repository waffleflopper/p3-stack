#!/usr/bin/env bash
# Read-only worktree prune audit. Classifies every git worktree by size, merge
# state, uncommitted work, remote/PR state, and last activity. Emits a table
# sorted by size with a suggested bucket. Never deletes anything; deletion stays
# a human-gated step in the playbook.
#
# Last activity is the newest of the branch's last commit time and the newest
# mtime of tracked-modified files. Anything active in the last 7 days is bucketed
# `verify-recent-thread`: check it with t3_worktree_status and t3_thread_search.
#
# Needs bash, git, coreutils. Optional: gh and jq (PR column shows "-" without them).
# Set P3_AUDIT_NO_FETCH=1 to skip the best-effort fetch of the default branch.
#
# Usage: worktree-audit.sh [repo-path]   (defaults to the current repo)
set -u

repo="${1:-$(git rev-parse --show-toplevel 2>/dev/null)}"
[ -z "$repo" ] && { echo "not in a git repo; pass a repo path" >&2; exit 1; }
cd "$repo" || exit 1

# The first entry is the main worktree; everything else is a candidate.
main_wt=$(git worktree list --porcelain | awk '/^worktree /{sub(/^worktree /,""); print; exit}')

# Default branch drives the merge check; fall back to main.
default=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##')
default="${default:-main}"
if [ "${P3_AUDIT_NO_FETCH:-}" != 1 ]; then
	git fetch origin "$default" --quiet 2>/dev/null || echo "warn: could not fetch origin/$default; merged column may be stale" >&2
fi
if git show-ref --verify --quiet "refs/remotes/origin/$default"; then base="origin/$default"
elif git show-ref --verify --quiet "refs/heads/$default"; then base="$default"
else base=""; echo "warn: no $default branch found; merged column is unknown" >&2; fi

# PR state by branch, fetched once. Empty if gh or jq is unavailable.
prs=$(mktemp)
trap 'rm -f "$prs"' EXIT
have_pr=no
if command -v gh >/dev/null 2>&1 && command -v jq >/dev/null 2>&1 &&
	gh pr list --author "@me" --state all --limit 1000 \
		--json number,state,headRefName > "$prs" 2>/dev/null; then
	have_pr=yes
fi

mtime() { stat -c %Y "$1" 2>/dev/null || stat -f %m "$1" 2>/dev/null; }

now=$(date +%s)
week=$((7 * 86400))

rows=$(mktemp)
trap 'rm -f "$prs" "$rows"' EXIT

git worktree list --porcelain | awk '/^worktree /{sub(/^worktree /,""); print}' | while IFS= read -r wt; do
	[ "$wt" = "$main_wt" ] && continue

	if [ ! -d "$wt" ]; then
		printf '0\t?\t?\t?\t?\t?\t?\t?\tmissing\t%s\n' "$wt" >> "$rows"
		continue
	fi

	kb=$(du -sk "$wt" 2>/dev/null | awk '{print $1}')
	kb="${kb:-0}"
	size=$(du -sh "$wt" 2>/dev/null | awk '{print $1}')
	head=$(git -C "$wt" rev-parse HEAD 2>/dev/null)
	head_ts=$(git -C "$wt" log -1 --format='%ct' HEAD 2>/dev/null || echo 0)
	head_ts="${head_ts:-0}"
	age=$([ "$head_ts" -gt 0 ] && echo "$(( (now - head_ts) / 86400 ))d" || echo "?")

	# Squash-merged branches are not ancestors of the default branch, so PR
	# state is the real signal; merge-base only catches fast-forward/rebase merges.
	if [ -n "$base" ] && git merge-base --is-ancestor "$head" "$base" 2>/dev/null; then merged=YES
	elif [ -n "$base" ]; then merged=no
	else merged="?"; fi

	# Distinguish real WIP (tracked edits) from disposable untracked scratch.
	porcelain=$(git -C "$wt" status --porcelain 2>/dev/null)
	tracked=$(printf '%s\n' "$porcelain" | grep -v '^??' | grep -v '^$')
	if [ -z "$porcelain" ]; then dirty=clean
	elif [ -n "$tracked" ]; then dirty="wip:$(printf '%s\n' "$tracked" | grep -c .)"
	else dirty="scratch:$(printf '%s\n' "$porcelain" | grep -c '^??')"; fi

	branch=$(git -C "$wt" symbolic-ref --quiet --short HEAD 2>/dev/null || echo "")
	if [ -z "$branch" ]; then remote=detached
	elif git -C "$wt" show-ref --verify --quiet "refs/remotes/origin/$branch"; then
		if [ "$(git -C "$wt" rev-parse "origin/$branch" 2>/dev/null)" = "$head" ]; then remote=pushed
		else remote="ahead$(git -C "$wt" rev-list --count "origin/$branch..HEAD" 2>/dev/null)"; fi
	else remote=no-remote; fi

	pr="-"
	if [ "$have_pr" = yes ] && [ -n "$branch" ]; then
		pr=$(jq -r --arg b "$branch" \
			'.[] | select(.headRefName==$b) | "#\(.number)/\(.state)"' "$prs" 2>/dev/null | head -1)
		[ -z "$pr" ] && pr="-"
	fi

	# Last activity: newest of last commit and tracked-modified file mtimes.
	last_ts=$head_ts
	if [ -n "$tracked" ]; then
		while IFS= read -r line; do
			path="${line:3}"
			path="${path##* -> }"
			path="${path%\"}"; path="${path#\"}"
			t=$(mtime "$wt/$path")
			[ -n "$t" ] && [ "$t" -gt "$last_ts" ] && last_ts=$t
		done <<< "$tracked"
	fi
	if [ "$last_ts" -gt 0 ]; then
		last="$(date -d "@$last_ts" '+%Y-%m-%d' 2>/dev/null || date -r "$last_ts" '+%Y-%m-%d' 2>/dev/null)($(( (now - last_ts) / 86400 ))d)"
		recent=$([ $((now - last_ts)) -le "$week" ] && echo yes || echo no)
	else last="?"; recent=no; fi

	case "$dirty" in
		wip:*) bucket=hold-wip ;;
		*) case "$pr" in
			*OPEN*) bucket=hold-open-pr ;;
			*) if [ "$recent" = yes ]; then bucket=verify-recent-thread
			   elif [ "$merged" = YES ] || [ "$pr" != "-" ]; then bucket=safe
			   else bucket=review; fi ;;
		esac ;;
	esac

	printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
		"$kb" "$size" "$age" "$merged" "$dirty" "$remote" "$pr" "$last" "$bucket" "$wt" >> "$rows"
done

{
	printf 'SIZE\tAGE\tMERGED\tDIRTY\tREMOTE\tPR\tLAST_ACTIVE\tBUCKET\tWORKTREE\n'
	sort -t$'\t' -k1,1 -rn "$rows" | cut -f2-
} | if command -v column >/dev/null 2>&1; then column -t -s$'\t'; else cat; fi
