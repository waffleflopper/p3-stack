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

OFF_RE = re.compile(r"^[/$]p3-mode\s+off[.!]?$", re.IGNORECASE)
ACTIVATE_RE = re.compile(r"(?:^|\s)[/$]p3-mode(?=\s|$)|\[\$p3-mode\]\(")

# (event, class, active) -> (state action, output text). Missing key = do nothing.
TABLE = {
    ("UserPromptSubmit", "off", True): ("delete", OFF),
    ("UserPromptSubmit", "off", False): ("delete", OFF),
    ("UserPromptSubmit", "activate", True): ("touch", None),
    ("UserPromptSubmit", "activate", False): ("touch", None),
    ("UserPromptSubmit", "other", True): ("touch", REMINDER),
    ("SessionStart", "compact", True): (None, COMPACT),
}


def classify(event, payload):
    if event == "UserPromptSubmit":
        prompt = payload.get("prompt")
        prompt = prompt.strip() if isinstance(prompt, str) else ""
        if OFF_RE.match(prompt):
            return "off"
        return "activate" if ACTIVATE_RE.search(prompt) else "other"
    if event == "SessionStart":
        return payload.get("source")
    return None


def prune(now):
    for name in os.listdir(STATE_DIR):
        path = os.path.join(STATE_DIR, name)
        try:
            if now - os.stat(path).st_mtime > MAX_AGE:
                os.remove(path)
        except OSError:
            pass


def touch(path):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(path, "a"):
        pass
    os.utime(path)
    prune(time.time())


def main():
    payload = json.load(sys.stdin)
    event = payload.get("hook_event_name")
    session = payload.get("session_id")
    if not isinstance(session, str) or not session:
        return
    path = os.path.join(STATE_DIR, hashlib.sha256(session.encode()).hexdigest())
    active = os.path.exists(path)
    action, text = TABLE.get((event, classify(event, payload), active), (None, None))
    if action == "touch":
        touch(path)
    elif action == "delete" and active:
        os.remove(path)
    if text:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": event, "additionalContext": text}}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
