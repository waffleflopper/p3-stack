# p3-stack

p3-stack is [pstack](https://github.com/cursor/plugins/tree/main/pstack) rebuilt for T3 Code. Same engineering discipline, native T3 orchestration.

pstack is poteto's answer to AI slop code. It turns an agent into an engineering team: one mode skill that routes to playbooks, principles that ground every decision, and verification strict enough that you can parallelize with confidence. p3-stack keeps that system and rewires the mechanics to T3 Code's primitives:

- **Delegation.** `delegate_task` child agents replace Cursor's Task tool, with per-role providers and models resolved from `orchestrator_capabilities`. Cross-model panels are native.
- **Worktrees.** `t3_thread_launch` binds a worker to its own worktree and branch. One writer per worktree, enforced by the app instead of by advice.
- **Watching.** `watch_pull_request` wakes the thread when checks finish, someone comments, or the branch conflicts. No polling loops.
- **Scheduling.** `schedule_task` runs audits and overnight cadences even when no turn is active. No `/loop`.
- **Memory.** `t3_thread_read` and `t3_thread_search` replace mining Cursor transcript files.
- **Sticky mode.** Provider hooks keep `/p3-mode` on for the rest of a thread, the way Cursor's Custom Mode keeps pstack's mode on. T3 Code has no per-thread instructions, so `install.sh` adds the hooks to every Claude and Codex instance in T3's provider settings.
- **Proof.** `preview_*` browser tools and `device_*` simulators replace external control skills. Screenshots and recordings land in the thread.

## Install

```bash
git clone https://github.com/uzairansaruzi/p3-stack.git
cd p3-stack
./install.sh
```

`install.sh` links every `skills/*` directory into `~/.agents/skills/`, where Codex and most T3 Code providers read skills. Claude Code reads only `<config dir>/skills/`, so the script also reads T3 Code's provider settings and links into the config dir of every enabled Claude instance: its `homePath`, else `$CLAUDE_CONFIG_DIR`, else `~/.claude`. Use `./install.sh --project /path/to/repo` to install into a project's `.agents/skills/`, plus `.claude/skills/` when Claude is enabled.

The script also installs the mode hooks into each enabled Claude and Codex instance. Claude instances get them in `<config dir>/settings.json`. Codex instances get them in `<CODEX_HOME>/hooks.json`, where `CODEX_HOME` is the instance's `homePath`, else `$CODEX_HOME`, else `~/.codex`. Codex runs only hooks you trust, so the script marks its own two hooks trusted through `codex app-server`. Other hooks in those files stay as they are, and reruns change nothing. Rerun the script after you add a provider instance. To remove the skill links and the hooks, run `./install.sh --uninstall`.

## Get started

1. Run `/setup-p3`. It reads `orchestrator_capabilities` and writes `p3-models.md`, mapping each role (code, judgment, the review panels) to a provider and model you actually have.
2. Use `/p3-mode` whenever you want rigorous work. It reads the request, picks a playbook, and runs the other skills as the steps need them. It stays on for the rest of the thread, through compaction and resume, until you send `/p3-mode off`.
3. Stuck or unsure which skill fits? Ask `/p3-help`.

## The mode

`p3-mode` routes every task. After you invoke it, a `UserPromptSubmit` hook adds pstack's one-line reminder to each turn: "New task? Playbook match or rigor needed -> apply the p3-mode skill. Casual turn or user opts out -> don't." After compaction, a `SessionStart` hook tells the agent to reread `skills/p3-mode/SKILL.md`. The mode is per session. A new thread starts without it, and delegated workers get it from `agents/p3-agent.md` instead. Its playbooks: investigation, bug fix, perf issue, hillclimb, runtime forensics, trace forensics, feature, refactoring, prototype, visual parity, authoring a skill, eval, babysit, shipping, autonomous run, orchestrate, autopilot-full, autopilot-stack, session pickup, pause safely, multi-phase plan, worktree cleanup, opening a PR.

## Skills

architect, arena, automate-me, benchmark-checklist, blast-radius, bro, correct, create-verification-skill, figure-it-out, how, interrogate, maintain-verification-skill, make-bot-ui, no-comments, p3-help, recall, reflect, setup-p3, show-me-your-work, swarm, tdd, teach, technical-writing, typescript-best-practices, unslop, why.

## Principles

The twenty-four principle skills are indexed inside `p3-mode` and referenced by the other skills by name.

## Credit

p3-stack adapts [pstack](https://github.com/cursor/plugins/tree/main/pstack) by [poteto](https://x.com/poteto). The skills, principles, and language are hers; the T3 Code rewiring is this repo's. MIT, see [LICENSE](LICENSE).
