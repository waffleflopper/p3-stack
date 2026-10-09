#!/usr/bin/env python3
"""Resolve T3 Code provider instances and install p3-mode hooks into them."""
import json
import os
import queue
import shlex
import subprocess
import sys
import threading
import time

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
HOOK = os.path.join(ROOT, "hooks", "p3-mode-hook.py")
MARKER = "/hooks/p3-mode-hook.py"
TRUST_TIMEOUT = 30

DRIVERS = {
    "claudeAgent": {"env": "CLAUDE_CONFIG_DIR", "home": "~/.claude", "file": "settings.json", "trust": False},
    "codex": {"env": "CODEX_HOME", "home": "~/.codex", "file": "hooks.json", "trust": True},
}

EVENTS = {
    "SessionStart": {"matcher": "compact"},
    "UserPromptSubmit": {},
    "SubagentStart": {},
}


def settings_path():
    return os.path.join(os.environ.get("T3CODE_HOME") or os.path.expanduser("~/.t3"), "userdata", "settings.json")


def load_instances():
    """Return [(driver, home, binary)] for every enabled instance, deduped by driver and home."""
    try:
        with open(settings_path()) as f:
            settings = json.load(f)
    except FileNotFoundError:
        return []
    except (OSError, ValueError) as err:
        print(f"skip t3 settings ({err})", file=sys.stderr)
        return []
    instances = dict(settings.get("providerInstances") or {})
    for driver in DRIVERS:
        legacy = (settings.get("providers") or {}).get(driver) or {}
        instances.setdefault(driver, {"driver": driver, "enabled": legacy.get("enabled", True), "config": legacy})
    found = {}
    for instance in instances.values():
        spec = DRIVERS.get(instance.get("driver"))
        if not spec or not instance.get("enabled", True):
            continue
        config = instance.get("config") or {}
        home = (config.get("homePath") or "").strip() or os.environ.get(spec["env"], "").strip() or spec["home"]
        home = os.path.realpath(os.path.expanduser(home))
        binary = (config.get("binaryPath") or "").strip() or "codex"
        found.setdefault((instance["driver"], home), binary)
    return [(driver, home, binary) for (driver, home), binary in found.items()]


def ours(group):
    return any(MARKER in (hook.get("command") or "") for hook in group.get("hooks") or [])


def merge(doc, install):
    """Return doc with p3 hook groups replaced (install) or removed. None if doc.hooks is unusable."""
    hooks = doc.get("hooks", {})
    if not isinstance(hooks, dict):
        return None
    removed = False
    for event in list(hooks):
        groups = hooks[event]
        if not isinstance(groups, list):
            continue
        kept = [g for g in groups if not (isinstance(g, dict) and ours(g))]
        if len(kept) != len(groups):
            removed = True
            hooks[event] = kept
            if not kept:
                del hooks[event]
    if install:
        command = f"python3 -I {shlex.quote(HOOK)}"
        for event, extra in EVENTS.items():
            group = dict(extra, hooks=[{"type": "command", "command": command, "timeout": 5}])
            hooks.setdefault(event, []).append(group)
    if hooks:
        doc["hooks"] = hooks
    elif removed:
        doc.pop("hooks", None)
    return doc


def write_hooks(path, install):
    try:
        with open(path) as f:
            original = f.read()
        doc = json.loads(original)
    except FileNotFoundError:
        original, doc = None, {}
    except (OSError, ValueError) as err:
        return f"skip {path} (not valid JSON: {err})"
    if not isinstance(doc, dict) or (merged := merge(doc, install)) is None:
        return f"skip {path} (unexpected structure)"
    if original is None and not merged:
        return f"hooks already absent from {path}"
    text = json.dumps(merged, indent=2) + "\n"
    if text == original:
        return f"hooks already {'installed in' if install else 'absent from'} {path}"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.p3-tmp"
    with open(tmp, "w") as f:
        f.write(text)
    os.replace(tmp, path)
    return f"hooks {'installed in' if install else 'removed from'} {path}"


class AppServer:
    def __init__(self, binary, home):
        env = dict(os.environ, CODEX_HOME=home)
        self.proc = subprocess.Popen(
            [binary, "app-server"], env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True,
        )
        self.lines = queue.Queue()
        self.deadline = time.monotonic() + TRUST_TIMEOUT
        self.next_id = 1
        threading.Thread(target=self._pump, daemon=True).start()

    def _pump(self):
        for line in self.proc.stdout:
            self.lines.put(line)
        self.lines.put(None)

    def send(self, message):
        self.proc.stdin.write(json.dumps(message) + "\n")
        self.proc.stdin.flush()

    def request(self, method, params):
        request_id = self.next_id
        self.next_id += 1
        self.send({"id": request_id, "method": method, "params": params})
        while True:
            try:
                line = self.lines.get(timeout=max(self.deadline - time.monotonic(), 0))
            except queue.Empty:
                raise TimeoutError(f"{method} timed out")
            if line is None:
                raise RuntimeError("app-server exited")
            try:
                message = json.loads(line)
            except ValueError:
                continue
            if message.get("id") != request_id or "method" in message:
                continue
            if "error" in message:
                raise RuntimeError(f"{method}: {message['error']}")
            return message.get("result") or {}

    def close(self):
        self.proc.terminate()
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def trust_codex_hooks(binary, home):
    try:
        server = AppServer(binary, home)
    except OSError as err:
        return f"skip trusting codex hooks in {home} ({err})"
    try:
        server.request("initialize", {"clientInfo": {"name": "p3-stack-install", "version": "1"}})
        server.send({"method": "initialized"})
        listed = server.request("hooks/list", {"cwds": [home]})
        mine = {}
        for entry in listed.get("data") or []:
            for hook in entry.get("hooks") or []:
                if MARKER in (hook.get("command") or ""):
                    mine[hook["key"]] = hook
        if not mine:
            return f"skip trusting codex hooks in {home} (codex lists none of ours)"
        pending = {k: {"trusted_hash": h["currentHash"]} for k, h in mine.items() if h.get("trustStatus") != "trusted"}
        if pending:
            server.request("config/value/write", {"keyPath": "hooks.state", "mergeStrategy": "upsert", "value": pending})
        return f"trusted {len(pending)} codex hooks in {home}" if pending else f"codex hooks already trusted in {home}"
    except (OSError, RuntimeError, TimeoutError, KeyError) as err:
        return f"skip trusting codex hooks in {home} ({err})"
    finally:
        server.close()


def cmd_claude_dirs():
    homes = sorted({home for driver, home, _ in load_instances() if driver == "claudeAgent"})
    for home in homes:
        print(home)


def cmd_hooks(install):
    for driver, home, binary in load_instances():
        spec = DRIVERS[driver]
        print(write_hooks(os.path.join(home, spec["file"]), install))
        if install and spec["trust"]:
            print(trust_codex_hooks(binary, home))


def main(argv):
    if argv[:1] == ["claude-dirs"] and len(argv) == 1:
        cmd_claude_dirs()
    elif argv[:1] == ["hooks"] and argv[1:] in ([], ["--uninstall"]):
        cmd_hooks(install=not argv[1:])
    else:
        print("usage: install.py claude-dirs | hooks [--uninstall]", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
