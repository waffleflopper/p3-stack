---
name: whats-next
description: Find what a repository should work on next and hand back one copy-paste `/p3-mode` prompt per recommended PR or program, each ending in `/ship-it`. Use for /whats-next, "what should we work on next", or "give me prompts for the next work".
---

# What's next

**Read-only. Find the next work, rank it, and hand back one prompt per item. The user pastes each prompt into its own worktree thread.** You start nothing yourself: no branches, threads, PRs or issue edits.

## Steps

1. **Snapshot on fresh trunk.** `git fetch`, then read:
   - what merged since the last look;
   - open issues with labels and update dates;
   - open PRs and remote integration branches;
   - open security alerts with severity and patched version (`gh api --paginate 'repos/<owner>/<repo>/dependabot/alerts?state=open'`).

   Take what the user says is in flight as given, and match it to branches and PRs. When the user reports items done, re-snapshot. Never reuse the last list.
2. **Check every candidate against current trunk.** Read its spec and comments. Confirm that the code it names exists, the defect is still present in source, and its decisions are recorded. Check that the spec's own instructions still work: branch names against CI triggers, file paths, superseded mocks. Back each claim with a file:line or command output.
3. **Sort each candidate into one of four groups.**
   - **Now.** It is ready and separate from in-flight work.
   - **Decide first.** It needs a product call no experiment settles. Carry your recommended default.
   - **Wait for X.** It shares files or a contract with in-flight work. Name the overlap.
   - **Not now.** It is labeled for the human, or its cost or conflict outweighs its value right now. Give the evidence.

   For a security alert, check whether the app reaches the vulnerable path before you rank it.
4. **Rank Now.** Order by who it helps and how much, then readiness, then size. Name every overlap between two items or with in-flight work. Name every migration or deploy gate.
5. **Write the prompts** in the format below.

## Prompt format

Put each prompt in its own fenced block. Each prompt stands alone, because the thread it starts gets nothing else. Aim for 120 to 300 words for a single PR, and up to 400 for a program.

- **First line.** Start with `/p3-mode `. State the job in one sentence with the issue number and how to read it (`gh issue view <n> --comments`).
- **Decisions.** Write the user's settled calls as "Decision (<name>)" or "Scope (<name>)", including any default you chose for them. Then they can edit it before pasting.
- **Where to start.** List the files, functions and endpoints you checked in step 2.
- **What must hold.**
  - Acceptance the issue doesn't state, or that you corrected.
  - The real-surface proof the repository requires: its verify command, viewport widths, loading and error states.
  - Role-based tests wherever data access changes.
- **Repository rules.** Restate the ones that cost most when missed, even if AGENTS.md or memory already has them: protected databases, runtime pins, migration ordering, recipe updates.
- **Model routing.** Add a line from `p3-models.md` (project root, else `~/.agents/p3-models.md`) or memory, for example "UI work stays on Claude models".
- **Gate.** End every prompt with `/ship-it`.
  - If a schema change needs a migration someone applies separately, put this sentence before `/ship-it`: "The PR body must tell <name> to apply the migration before merge. Stop before merging so they can."
- **Program.** For a spec split into slices:
  - Use a feature branch name that matches the CI triggers.
  - Give the slice order and which slices run in parallel, with one writer per worktree.
  - Keep the branch synced with trunk.
  - State "`/ship-it` scope is each slice PR into the feature branch. Stop before the final PR into trunk." This matches [ship-it](../ship-it/SKILL.md).
  - Require a decision trail, and a report after each slice.

## Reply

1. One line on what changed since the last look, and the trunk SHA you checked.
2. A table with these columns: order, work, who it's for, shape, migration.
3. Why this order, in one or two sentences.
4. Decisions only the user can make. Give each one with your default and the prompt it sits in.
5. Problems you found in specs, and how the prompts correct them.
6. Not now and Wait for X, each with its evidence.
7. The prompts, in ranked order.
8. Overlap and gates: which prompts stop before merge, and which merge conflicts to expect.
