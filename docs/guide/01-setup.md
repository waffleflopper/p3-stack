# Set up p3-stack

In this page you install p3-stack, pick which models it uses, and run your first task. Setup is one command plus a short conversation.

## Install the skills and hooks

Clone the repo and run the installer:

```bash
git clone https://github.com/waffleflopper/p3-stack.git
cd p3-stack
./install.sh
```

`install.sh` symlinks every skill into `~/.agents/skills/`, where Codex and most T3 Code providers read skills. Claude reads only its config dir, so the script also reads T3 Code's provider settings and links every skill into the `skills/` dir of each enabled Claude instance. That dir is the instance's `homePath`, else `$CLAUDE_CONFIG_DIR`, else `~/.claude`.

It also installs `hooks/p3-mode-hook.py` into every enabled Claude and Codex instance: `<config dir>/settings.json` for Claude, `<CODEX_HOME>/hooks.json` for Codex. Codex runs only hooks you trust, so the script marks its own hooks trusted. The installer prints one line per instance. Other hooks in those files stay as they are, and reruns change nothing.

Rerun `./install.sh` after you add a provider instance or pull. `./install.sh --project /path/to/repo` targets a project's `.agents/skills/` instead. `./install.sh --uninstall` removes the links and the hooks.

## Pick your models

Run:

```text
/setup-p3
```

[`/setup-p3`](../../skills/setup-p3/SKILL.md) asks which models, each with a reasoning level, p3-stack may use. Plain language ("Opus 5.5 High", "GPT Sol 6.1 XHigh", "DeepSeek V4.1 Flash Max") or exact ids are both fine. That list is the pool. Every model setup writes comes from it. It never substitutes a model you did not name.

It resolves each pool entry against `orchestrator_capabilities` to an exact provider instance, model id, and reasoning option, and shows you the resolved list. It asks only about entries that are ambiguous (the same model under two provider instances, two close versions) or that match nothing.

Then it maps every role (code delegates, judgment, the review panels) from the pool and recommends a split: the strongest entry for judgment, prose, and the hardest tasks; a fast strong coder for the code roles, explorers, investigators, and swarm; panels spread across distinct providers in the pool. Change any role you want. It writes `p3-models.md`, a small file every p3-stack skill reads, either in the project root or at `~/.agents/p3-models.md`. Readers check the project root first, else `~/.agents/p3-models.md`. Each entry reads `<providerInstanceId>/<model> (<effort>)`. The file records the pool, so a rerun starts from it and keeps each role whose value is still in the pool.

You only override what you care about. A role with no line keeps the skill's default. To restore a default, delete that role's line.

You might be wondering how to run a role on whatever model the thread already uses. Set it to `inherit-parent` and p3-stack omits the model in `delegate_task`, so the child runs on the parent thread's model. For a panel role the value is a list, and one `delegate_task` runs per entry, so the list length sets the panel size. Setup also configures `swarm workers`, the default model for every `/swarm` worker unless a race names a model for each arm.

## Accept the verification offer, or don't

At the end of setup, `/setup-p3` looks for a way to prove app behavior in your project, either a `verify-*` skill or an existing harness. If it finds neither, it offers once to generate one with [`/create-verification-skill`](../../skills/create-verification-skill/SKILL.md).

Say yes and it writes `.agents/skills/verify-<app>/`, a project-local skill that teaches agents to drive your app the way a user does. It proves the skill works once before handing it over. Say no and setup moves on. You can run `/create-verification-skill` yourself any time. [Verify and ship](./06-verify-and-ship.md#create-a-project-verification-skill) covers it in depth.

If you're new to p3-stack, say yes. An agent that can check its own work keeps going until the check passes. An agent that can't hands every result back to you to check by hand. Of everything in this guide, the verification skill pays off the most.

After setup, start a new thread. `p3-models.md` applies to new sessions.

## Keep the cost in check

p3-stack spends extra tokens on delegated tasks and review panels. That's the price of the rigor. To spend fewer:

- Rerun `/setup-p3` and name a cheaper pool or lower reasoning levels. A strong model in the main thread with cheaper, faster models in the code roles is a good split.
- Set a role to `inherit-parent` so it runs on the thread's own model.
- Shorten a panel list. Each entry runs one `delegate_task`.
- Save `/p3-mode` for work that needs rigor. A small, obvious edit doesn't.

## Run your first task

Pick something real but small, and describe it the way you'd describe it to a colleague:

```text
/p3-mode add a --json flag to this command. text output stays byte-identical. verify both.
```

Watch the todo list. Its first items are the matched playbook's steps copied in, the [Feature playbook](../../skills/p3-mode/playbooks/feature.md) for this prompt. If `/p3-mode` skips a step, the step stays in the list with `skip: <reason>`, so you can see what it chose not to do.

From here you can type normal follow-ups. `/p3-mode` stays on for the rest of the thread, through compaction and resume, until you send `/p3-mode off`. A new thread starts without it.

## Confirm the hook works

The hook is what keeps the mode on, so check it once after install:

1. Start a new thread and send a `/p3-mode` task. On that turn the hook adds a note telling the agent to read `skills/p3-mode/SKILL.md` and apply it, so the mode loads even if the provider passes `/p3-mode` through as plain text. The agent opens the playbook todo list.
2. Send a normal follow-up and ask the agent what context the hook added. It should quote a one-line reminder: "p3-mode is active for this session. New task? Playbook match or rigor needed -> apply the p3-mode skill. Casual turn or user opts out -> don't."
3. Send `/p3-mode off`. The agent confirms in one line. Later turns carry no reminder.

If step 1 gets no note, rerun `./install.sh` and read its output. A provider instance missing from it is disabled or absent in T3's provider settings. A Codex line starting `skip trusting` means its hooks are installed but not trusted, so Codex won't run them.

Next: [Route work through `/p3-mode`](./02-p3-mode.md).
