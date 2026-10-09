import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
HOOK = os.path.join(ROOT, "hooks", "p3-mode-hook.py")
INSTALL = os.path.join(ROOT, "hooks", "install.py")
COMMAND = f"python3 -I {shlex.quote(HOOK)}"

REMINDER = (
    "p3-mode is active for this session. New task? Playbook match or rigor needed -> "
    "apply the p3-mode skill. Casual turn or user opts out -> don't."
)
OFF = "p3-mode is off for this session. Acknowledge in one line and stop applying the p3-mode skill."


def output(event, text):
    return {"hookSpecificOutput": {"hookEventName": event, "additionalContext": text}}


class HookTest(unittest.TestCase):
    def setUp(self):
        self.state = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.state)

    def run_hook(self, stdin):
        env = dict(os.environ, XDG_STATE_HOME=self.state)
        proc = subprocess.run(["python3", "-I", HOOK], input=stdin, capture_output=True, text=True, env=env)
        self.assertEqual(proc.returncode, 0)
        return proc.stdout

    def event(self, event, session="s1", **fields):
        payload = {"session_id": session, "cwd": "/tmp", "hook_event_name": event, **fields}
        out = self.run_hook(json.dumps(payload))
        return json.loads(out) if out else None

    def prompt(self, text, session="s1"):
        return self.event("UserPromptSubmit", session, prompt=text)

    def test_activation_forms_make_session_sticky(self):
        for i, text in enumerate(["/p3-mode fix it", "$p3-mode fix it", "please $p3-mode", "[$p3-mode](skill://x) go"]):
            session = f"sticky-{i}"
            self.assertIsNone(self.prompt(text, session))
            self.assertEqual(self.prompt("now do the thing", session), output("UserPromptSubmit", REMINDER))
            self.assertIsNone(self.prompt("now do the thing", "other-" + session))

    def test_near_misses_do_not_activate(self):
        for text in ["/p3-modes fix it", "foo/p3-mode fix it", "$p3-mode-x", "p3-mode off"]:
            self.assertIsNone(self.prompt(text))
            self.assertIsNone(self.prompt("plain"))

    def test_off_clears_state(self):
        self.prompt("/p3-mode go")
        self.assertEqual(self.prompt("  /P3-MODE OFF.  "), output("UserPromptSubmit", OFF))
        self.assertIsNone(self.prompt("plain"))

    def test_session_start_events(self):
        self.assertIsNone(self.event("SessionStart", source="compact"))
        self.prompt("/p3-mode go")
        compact = self.event("SessionStart", source="compact")
        skill = os.path.join(ROOT, "skills", "p3-mode", "SKILL.md")
        self.assertTrue(os.path.isfile(skill))
        self.assertEqual(
            compact,
            output(
                "SessionStart",
                "p3-mode is active for this session and the context was just compacted. "
                f"Read {skill} in full before your next step, then continue under it.",
            ),
        )
        self.assertIsNone(self.event("SessionStart", source="resume"))
        self.assertIsNone(self.event("SessionStart", source="startup"))
        self.assertIsNone(self.event("Stop"))

    def test_garbage_input_is_silent(self):
        for stdin in ["", "not json", "[]", '{"session_id": 5}', '{"hook_event_name":"UserPromptSubmit"}']:
            self.assertEqual(self.run_hook(stdin), "")

    def test_old_session_files_are_pruned(self):
        self.prompt("/p3-mode go", "old")
        sessions = os.path.join(self.state, "p3-stack", "sessions")
        (old,) = os.listdir(sessions)
        stale = os.path.getmtime(os.path.join(sessions, old)) - 31 * 24 * 3600
        os.utime(os.path.join(sessions, old), (stale, stale))
        self.prompt("/p3-mode go", "new")
        self.assertNotIn(old, os.listdir(sessions))
        self.assertEqual(len(os.listdir(sessions)), 1)


class InstallTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)
        self.t3 = os.path.join(self.tmp, "t3")
        self.home = os.path.join(self.tmp, "home")
        os.makedirs(os.path.join(self.t3, "userdata"))
        os.makedirs(self.home)

    def write_settings(self, settings):
        with open(os.path.join(self.t3, "userdata", "settings.json"), "w") as f:
            json.dump(settings, f)

    def run_install(self, *args):
        env = dict(os.environ, T3CODE_HOME=self.t3, HOME=self.home)
        for var in ("CLAUDE_CONFIG_DIR", "CODEX_HOME"):
            env.pop(var, None)
        env["PATH"] = os.path.join(self.tmp, "nobin")
        proc = subprocess.run([sys.executable, "-I", INSTALL, *args], capture_output=True, text=True, env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc.stdout.splitlines()

    def read(self, *parts):
        with open(os.path.join(*parts)) as f:
            return f.read()

    def ours(self):
        return [
            {"matcher": "compact", "hooks": [{"type": "command", "command": COMMAND, "timeout": 5}]},
        ], [{"hooks": [{"type": "command", "command": COMMAND, "timeout": 5}]}]

    def test_claude_hooks_merge_idempotent_and_uninstall(self):
        claude = os.path.join(self.tmp, "claude-a")
        disabled = os.path.join(self.tmp, "claude-off")
        for d in (claude, disabled):
            os.makedirs(d)
        foreign = {"hooks": [{"type": "command", "command": "echo hi"}]}
        original = {"model": "opus", "hooks": {"UserPromptSubmit": [foreign], "Stop": [foreign]}}
        with open(os.path.join(claude, "settings.json"), "w") as f:
            json.dump(original, f)
        self.write_settings({
            "providerInstances": {
                "claude-a": {"driver": "claudeAgent", "config": {"homePath": claude}},
                "claude-off": {"driver": "claudeAgent", "enabled": False, "config": {"homePath": disabled}},
            },
            "providers": {"codex": {"enabled": False}},
        })

        self.assertEqual(self.run_install("claude-dirs"), [os.path.realpath(claude), os.path.realpath(os.path.join(self.home, ".claude"))])
        lines = self.run_install("hooks")
        self.assertIn(f"hooks installed in {os.path.realpath(claude)}/settings.json", lines)

        start, submit = self.ours()
        expected = {
            "model": "opus",
            "hooks": {"UserPromptSubmit": [foreign, *submit], "Stop": [foreign], "SessionStart": start},
        }
        settings = os.path.join(claude, "settings.json")
        self.assertEqual(json.loads(self.read(settings)), expected)
        first = self.read(settings)
        self.assertTrue(first.endswith("}\n"))
        self.run_install("hooks")
        self.assertEqual(self.read(settings), first)
        self.assertFalse(os.path.exists(os.path.join(disabled, "settings.json")))

        lines = self.run_install("hooks", "--uninstall")
        self.assertIn(f"hooks removed from {os.path.realpath(claude)}/settings.json", lines)
        self.assertEqual(json.loads(self.read(settings)), original)
        self.assertEqual(json.loads(self.read(self.home, ".claude", "settings.json")), {})

    def test_uninstall_drops_emptied_hooks_key(self):
        claude = os.path.join(self.tmp, "claude-a")
        self.write_settings({"providerInstances": {"c": {"driver": "claudeAgent", "config": {"homePath": claude}}}})
        self.run_install("hooks")
        self.run_install("hooks", "--uninstall")
        self.assertEqual(json.loads(self.read(claude, "settings.json")), {})

    def test_invalid_json_is_skipped_untouched(self):
        claude = os.path.join(self.tmp, "claude-a")
        os.makedirs(claude)
        with open(os.path.join(claude, "settings.json"), "w") as f:
            f.write("{nope")
        self.write_settings({"providerInstances": {"c": {"driver": "claudeAgent", "config": {"homePath": claude}}}})
        lines = self.run_install("hooks")
        self.assertTrue(any(l.startswith(f"skip {os.path.realpath(claude)}/settings.json (not valid JSON") for l in lines), lines)
        self.assertEqual(self.read(claude, "settings.json"), "{nope")

    def test_missing_settings_is_silent(self):
        self.assertEqual(self.run_install("hooks"), [])
        self.assertEqual(self.run_install("claude-dirs"), [])

    def test_legacy_codex_without_binary_skips_trust(self):
        codex_home = os.path.join(self.home, ".codex")
        self.write_settings({"providers": {"claudeAgent": {"enabled": False}}})
        lines = self.run_install("hooks")
        real = os.path.realpath(codex_home)
        self.assertEqual(lines[0], f"hooks installed in {real}/hooks.json")
        self.assertTrue(lines[1].startswith(f"skip trusting codex hooks in {real} ("), lines)
        start, submit = self.ours()
        self.assertEqual(
            json.loads(self.read(codex_home, "hooks.json")),
            {"hooks": {"SessionStart": start, "UserPromptSubmit": submit}},
        )

    @unittest.skipUnless(shutil.which("codex"), "codex binary not installed")
    def test_codex_hooks_are_trusted_end_to_end(self):
        codex_home = os.path.realpath(os.path.join(self.tmp, "codex-home"))
        os.makedirs(codex_home)
        with open(os.path.join(codex_home, "config.toml"), "w") as f:
            f.write('[hooks.state."other:key"]\ntrusted_hash = "sha256:abc"\n')
        self.write_settings({
            "providerInstances": {
                "codex": {"driver": "codex", "config": {"homePath": codex_home, "binaryPath": shutil.which("codex")}},
            },
            "providers": {"claudeAgent": {"enabled": False}},
        })
        lines = self.run_install("hooks")
        self.assertEqual(lines, [f"hooks installed in {codex_home}/hooks.json", f"trusted 2 codex hooks in {codex_home}"])

        config = self.read(codex_home, "config.toml")
        self.assertIn('"other:key"', config)
        self.assertIn("sha256:abc", config)
        self.assertEqual(config.count("trusted_hash"), 3)

        lines = self.run_install("hooks")
        self.assertEqual(lines, [f"hooks already installed in {codex_home}/hooks.json", f"codex hooks already trusted in {codex_home}"])


if __name__ == "__main__":
    unittest.main()
