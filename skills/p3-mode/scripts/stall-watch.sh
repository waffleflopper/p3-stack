#!/usr/bin/env bash
# Token-free stall watcher for a coordinator. It sleeps in a plain shell and
# calls out only when a lane goes quiet, so a healthy program spends no model
# turns between real events.
#
# A lane is a name and a path the lane's worker writes as it makes progress: its
# worktree, its decision trail, or its report file. A lane is quiet when nothing
# under the path changed for --quiet minutes. node_modules and .git/objects are
# ignored.
#
# Lanes come from NAME=PATH arguments and from --lanes FILE (one "NAME PATH" per
# line, re-read every cycle so the coordinator can add and drop lanes without a
# restart). With --lanes, an empty set keeps watching; with only NAME=PATH
# arguments, it exits 0.
#
# With P3_STALL_WEBHOOK set (a schedule_task webhook URL, kept out of argv), each
# quiet spell POSTs {"stalled":"<names>"} once and the watcher keeps running;
# activity re-arms the lane. Without it, the watcher prints the quiet lanes and
# exits 3, so a harness that wakes on background-command exit wakes once.
#
# Usage: stall-watch.sh [--quiet MINUTES] [--interval SECONDS] [--lanes FILE] [NAME=PATH...]
set -u

quiet=90
interval=120
lanes_file=""
declare -a arg_lanes=()
while [ $# -gt 0 ]; do
	case "$1" in
	--quiet) quiet="$2"; shift 2 ;;
	--interval) interval="$2"; shift 2 ;;
	--lanes) lanes_file="$2"; shift 2 ;;
	-h | --help) sed -n '2,22p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
	*=*) arg_lanes+=("$1"); shift ;;
	*) echo "unknown argument: $1" >&2; exit 2 ;;
	esac
done

declare -A reported=()

read_lanes() {
	local entry
	for entry in "${arg_lanes[@]}"; do printf '%s %s\n' "${entry%%=*}" "${entry#*=}"; done
	if [ -n "$lanes_file" ] && [ -r "$lanes_file" ]; then
		grep -v '^[[:space:]]*\(#\|$\)' "$lanes_file"
	fi
}

active_since() {
	find "$1" \( -name node_modules -o -path '*/.git/objects' \) -prune -o -newermt "@$2" -print -quit 2>/dev/null | grep -q .
}

while :; do
	cutoff=$(($(date +%s) - quiet * 60))
	stalled=()
	seen=0
	while read -r name path; do
		[ -n "${name:-}" ] || continue
		seen=1
		if [ -e "$path" ] && active_since "$path" "$cutoff"; then
			unset "reported[$name]"
		elif [ -z "${reported[$name]:-}" ]; then
			if [ -e "$path" ]; then stalled+=("$name"); else stalled+=("$name(missing)"); fi
		fi
	done < <(read_lanes)

	[ "$seen" = 1 ] || [ -n "$lanes_file" ] || exit 0
	if [ "${#stalled[@]}" -gt 0 ]; then
		if [ -z "${P3_STALL_WEBHOOK:-}" ]; then
			printf 'quiet for %sm: %s\n' "$quiet" "${stalled[*]}"
			exit 3
		fi
		body=$(printf '{"stalled":"%s","quietMinutes":%s}' "${stalled[*]}" "$quiet")
		if curl -fsS -m 20 -H 'content-type: application/json' -d "$body" "$P3_STALL_WEBHOOK" >/dev/null; then
			for name in "${stalled[@]}"; do reported[${name%(missing)}]=1; done
		else
			echo "$(date -u +%FT%TZ) webhook post failed; retrying next cycle" >&2
		fi
	fi
	sleep "$interval"
done
