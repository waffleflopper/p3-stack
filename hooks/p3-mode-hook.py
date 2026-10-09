#!/usr/bin/env python3
"""Keep p3-mode sticky per provider session. Reads a hook event on stdin; never fails."""
import hashlib
import json
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
STATE_DIR = os.path.join(
    os.environ.get("XDG_STATE_HOME") or os.path.expanduser("~/.local/state"),
    "p3-stack",
    "sessions",
)
MAX_AGE = 30 * 24 * 3600

REMINDER = (
    "p3-mode is active for this session. New task? Playbook match or rigor needed -> "
    "apply the p3-mode skill. Casual turn or user opts out -> don't."
)
COMPACT = (
    "p3-mode is active for this session and the context was just compacted. Read "
    f"{ROOT}/skills/p3-mode/SKILL.md in full before your next step, then continue under it."
)
OFF = "p3-mode is off for this session. Acknowledge in one line and stop applying the p3-mode skill."
AGENT_FILE = f"{ROOT}/agents/p3-agent.md"
AGENT = (
    f"You are a p3-stack delegated worker. Read {AGENT_FILE} and follow it for this whole session, "
    "including after compaction."
)
AGENT_REMINDER = f"You are a p3-stack delegated worker. Keep working under {AGENT_FILE}."
AGENT_COMPACT = (
    "You are a p3-stack delegated worker and the context was just compacted. Read "
    f"{AGENT_FILE} and follow it again before your next step."
)
SUBAGENT = f"You are a p3-stack worker spawned from a p3 session. Read {AGENT_FILE} and follow it before any work."

OFF_RE = re.compile(r"^[/$]p3-mode\s+off[.!]?$", re.IGNORECASE)
ACTIVATE_RE = re.compile(r"(?:^|\s)[/$]p3-mode(?=\s|$)|\[\$p3-mode\]\(")
AGENT_BRIEF_RE = re.compile(r"(?:Act as the [\w-]+ sub-agent for this task\.\s*)?Read [^\n]*agents/p3-agent\.md")

ROLE_NONE, ROLE_MODE, ROLE_AGENT, ROLE_SAME = "none", "mode", "agent", "same"

# (event, class, role) -> (new role, output text). "same" keeps the current role. Missing key = no state change, no output.
TABLE = {
    ("UserPromptSubmit", "off", ROLE_NONE): (ROLE_NONE, OFF),
    ("UserPromptSubmit", "off", ROLE_MODE): (ROLE_NONE, OFF),
    ("UserPromptSubmit", "off", ROLE_AGENT): (ROLE_NONE, OFF),
    ("UserPromptSubmit", "activate", ROLE_NONE): (ROLE_MODE, None),
    ("UserPromptSubmit", "activate", ROLE_MODE): (ROLE_MODE, None),
    ("UserPromptSubmit", "activate", ROLE_AGENT): (ROLE_AGENT, AGENT_REMINDER),
    ("UserPromptSubmit", "agent", ROLE_NONE): (ROLE_AGENT, AGENT),
    ("UserPromptSubmit", "agent", ROLE_MODE): (ROLE_MODE, REMINDER),
    ("UserPromptSubmit", "agent", ROLE_AGENT): (ROLE_AGENT, AGENT_REMINDER),
    ("UserPromptSubmit", "other", ROLE_MODE): (ROLE_MODE, REMINDER),
    ("UserPromptSubmit", "other", ROLE_AGENT): (ROLE_AGENT, AGENT_REMINDER),
    ("SessionStart", "compact", ROLE_MODE): (ROLE_MODE, COMPACT),
    ("SessionStart", "compact", ROLE_AGENT): (ROLE_AGENT, AGENT_COMPACT),
    ("SubagentStart", "start", ROLE_MODE): (ROLE_SAME, SUBAGENT),
    ("SubagentStart", "start", ROLE_AGENT): (ROLE_SAME, SUBAGENT),
}


def classify(event, payload):
    if event == "UserPromptSubmit":
        prompt = payload.get("prompt")
        prompt = prompt.strip() if isinstance(prompt, str) else ""
        if OFF_RE.match(prompt):
            return "off"
        if AGENT_BRIEF_RE.match(prompt):
            return "agent"
        return "activate" if ACTIVATE_RE.search(prompt) else "other"
    if event == "SessionStart":
        return payload.get("source")
    if event == "SubagentStart":
        return "start"
    return None


def read_role(path):
    try:
        with open(path) as f:
            content = f.read().strip()
    except FileNotFoundError:
        return ROLE_NONE
    return ROLE_AGENT if content == ROLE_AGENT else ROLE_MODE


def prune(now):
    for name in os.listdir(STATE_DIR):
        path = os.path.join(STATE_DIR, name)
        try:
            if now - os.stat(path).st_mtime > MAX_AGE:
                os.remove(path)
        except OSError:
            pass


def write_role(path, role):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(path, "w") as f:
        f.write(role)
    prune(time.time())


def main():
    payload = json.load(sys.stdin)
    event = payload.get("hook_event_name")
    session = payload.get("session_id")
    if not isinstance(session, str) or not session:
        return
    path = os.path.join(STATE_DIR, hashlib.sha256(session.encode()).hexdigest())
    role = read_role(path)
    new, text = TABLE.get((event, classify(event, payload), role), (ROLE_SAME, None))
    if new == ROLE_NONE:
        if role != ROLE_NONE:
            os.remove(path)
    elif new != ROLE_SAME and (event == "UserPromptSubmit" or new != role):
        write_role(path, new)
    if text:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": event, "additionalContext": text}}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
