# Route work through `/p3-mode`

`/p3-mode` is the front door. You give it a goal, it matches one of twenty-three playbooks, copies that playbook's steps into the todo list, and calls the other skills as the steps need them. In this page you learn what a good prompt looks like, and how little of one you actually need.

![Theo Browne pulls a switch lever to route robots on rail handcars toward lit gates, under a /p3-mode departure board listing BUG FIX, FEATURE, and INVESTIGATION.](./images/router.jpg)

## What happens to your prompt

```mermaid
flowchart TD
    A[Your prompt] --> B[p3-mode]
    B --> C[Read the Principles section]
    C --> D{Match the task}
    D -->|Read-only question| E[Investigation]
    D -->|Defect| F[Bug fix]
    D -->|New behavior| G[Feature]
    D -->|Structure only| H[Refactoring]
    D -->|Measured slowness| I[Perf issue]
    D -->|Large work or no match| J[figure-it-out]
    E --> K[Verify and report]
    F --> K
    G --> K
    H --> K
    I --> K
    J --> K
```

The diagram shows the common routes. There are also playbooks for hillclimbing a metric, diagnosing runtime symptoms and captured traces, prototypes, visual parity, authoring and evaluating skills, autonomous runs, babysitting a PR or stack to merge-ready, shipping a verified stack, running a PR queue on autopilot, orchestrating project-scale programs, session pickup, pausing safely, multi-phase plans, and worktree cleanup. The [playbook directory](../../skills/p3-mode/playbooks/) has the full set.

## Say the goal, not the ceremony

You don't write a spec. You say what's wrong or what you want, plus anything you already know that saves the agent time:

```text
/p3-mode users get two notifications after a retry. repro first, then fix and verify.
```

That's a Bug fix prompt. "repro first" is a real constraint, not politeness, and the playbook honors it. Watch the todo list fill with the Bug fix steps. A skipped step stays visible with `skip: <reason>`.

## What goes in a prompt

A useful prompt carries up to five things, and each one fits in a sentence:

- **The goal.** Say what's wrong, or what you want.
- **The done check.** It must be able to pass or fail. "Make it better" and "work on it for an hour" aren't checks.
- **The proof you want to see.** Ask for the real command output, a video of the flow, the stored value, or a before-and-after number.
- **What you already know.** A symptom, a repro step, a log line, or a link saves the agent a search.
- **The real constraints.** "repro first", "don't change any code yet", "zero behavior change", and "let me review before proceeding" each change what the agent does.

Here's one prompt with all five:

```text
/p3-mode the csv export drops its last row since yesterday's deploy. failing job id is 4812. repro first, then fix. done means the 60k-row fixture exports every row. show me the row counts before and after.
```

Two things are worth leaving out:

- **The how.** Say what to achieve, and leave the agent room to find a better path than the one you'd pick. The same goes for a list of skills, covered in the pitfall below.
- **Your theory of the cause, at first.** A stated guess narrows the search to wherever you pointed. Let the agent restate the problem before you share your hunch.

For a noisy report, such as a long thread or a vague bug, make the restatement the first step:

```text
/p3-mode read this thread. restate the underlying issue in your own words, in plain english. don't change any code yet.
```

A misreading shows up in the restatement, before any code exists. Correct it there, and it costs you one message instead of one wrong fix.

## Follow up short

When the conversation already carries the context, the prompt shrinks to almost nothing. All of these are enough:

```text
/p3-mode do it
```

```text
continue
```

```text
keep going until done
```

Short works because the playbook holds the structure, and `/p3-mode` stays on for the rest of the session. The hook that `./install.sh` installs into each Claude and Codex provider instance reminds the agent of the mode on every turn and has it re-read the skill after compaction. [Set up p3-stack](./01-setup.md#run-your-first-task) shows how to start one. Your words carry the intent, and the skill carries the rigor.

To end it, send `/p3-mode off` on its own. The agent confirms in one line and drops the mode for that session.

## Switch tasks with "new task"

A long chat accumulates context from the last task. When you change subjects, say so:

```text
/p3-mode new task. figure out why the cache entry survives logout. don't change any code yet.
```

"new task" tells `/p3-mode` to re-match rather than continue the prior playbook. "don't change any code yet" pins this one to Investigation. Without those two phrases, a mode mid-Feature tends to treat your question as the next feature step.

## Give parallel work its own worktree

If you run several agents against one repository on one computer, they will fight over the working tree, the ports, and the build output. Ask for a worktree up front:

```text
/p3-mode new task. branch off <base> in a fresh worktree, then port the parser change there.
```

Each task in its own branch and worktree means no agent stomps another's files. When a worker needs its own thread too, the parent launches it with `t3_thread_launch` and a `workspaceStrategy` of type `worktree`. T3 creates the worktree and branch, binds the new thread to it, and prepares it before the agent starts. One writer per worktree. Worktrees cost disk and machine resources, so a laptop runs only a handful at once. The [Opening a PR playbook](../../skills/p3-mode/playbooks/opening-a-pr.md) already works from a worktree for code changes, so mostly you only say this when a specific base or location matters.

Delegated workers stay in style without your help. `/p3-mode` opens every code-writing `delegate_task` brief with a line that points the child at [`agents/p3-agent.md`](../../agents/p3-agent.md). The same hook sees that line and keeps the child in the p3 worker role through every turn and compaction.

Worktrees accumulate. When disk gets tight, ask:

```text
/p3-mode what's eating my disk? prune the worktrees that are safe to prune.
```

The [Worktree cleanup playbook](../../skills/p3-mode/playbooks/worktree-cleanup.md) classifies every worktree by merge state, uncommitted and unpushed work, and which threads still touch it. It deletes only what that evidence clears and pauses for your call on anything holding uncommitted or unpushed work.

## Leave it running

When you step away, say what done means and go:

```text
/p3-mode im stepping away. keep going until the migration check reports zero old callers. log your decisions.
```

Work you'll review later routes through [`/figure-it-out`](../../skills/figure-it-out/SKILL.md), which designs the run's phases and keeps a [`/show-me-your-work`](../../skills/show-me-your-work/SKILL.md) decision log. [Run work while you sleep](./07-overnight.md) covers the full overnight contract.

**Pitfall:** don't enumerate skills in your prompt ("use /how, then /architect, then /arena..."). The playbook already sequences them, and a hand-written sequence usually reorders or drops steps the playbook would have kept. Name a skill only when you want to override a specific choice.

Read [`p3-mode`](../../skills/p3-mode/SKILL.md) itself for the full routing rules.

Next: [Understand the code](./03-understand.md).
