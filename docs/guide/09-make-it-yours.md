# Make it yours

p3-mode is one person's style. The machinery underneath, playbooks, routing, model roles, works just as well wearing yours. This page covers editing the stack itself, generating a personal mode, capturing lessons from a session, fixing the repo so agents stop repeating mistakes, authoring a focused skill, and testing a skill change before you trust it.

Start smaller than you think. You don't need many skills on day one, or even this whole repo. Prompt plainly, watch where agents fail, and add a skill or a check when the same failure shows up twice.

## Edit the stack in place

p3-stack is a git repo you cloned, so fork it or edit your clone directly. `./install.sh` symlinks each `skills/*` directory, so an edit to an existing skill is live in the next session with no reinstall. A new skill directory isn't linked until you rerun `./install.sh`.

Models are config, not code. Rerun [`/setup-p3`](../../skills/setup-p3/SKILL.md) to change them. It offers your recorded pool as the current answer, so you add or drop entries, then remap any role. It rewrites `p3-models.md` in the project root or at `~/.agents/p3-models.md`, and the change applies to new sessions.

Recurring work is `schedule_task`, on an interval, at a fixed time on chosen weekdays, or on each request to a webhook. Runs return to the thread that scheduled them unless you ask for a fresh thread per run.

## Generate your own mode with `/automate-me`

```text
/automate-me
```

You don't describe your style, because [`/automate-me`](../../skills/automate-me/SKILL.md) reads it out of your history. It mines this project's recent threads with `t3_thread_search` and `t3_thread_read` for repeated preferences, in how you like replies, delegation, verification, code, prose, and process, then asks you which patterns are really you. It drafts `.agents/skills/<your-name>-mode/SKILL.md` through the [Authoring or modifying a skill playbook](../../skills/p3-mode/playbooks/authoring-a-skill.md), runs the draft through [`/unslop`](../../skills/unslop/SKILL.md), and opens a PR from a worktree so you review it like any other change.

Run it again whenever your habits drift:

```text
/automate-me update my mode skill with everything since its last edit
```

Update mode mines only the history since the skill last changed. It keeps rules you haven't contradicted, revises the ones with new evidence, and adds sections only for genuinely new patterns.

## Capture a session's lessons with `/reflect`

Right after a task that taught you something, run:

```text
/reflect that took way too long. capture what we learned so the next run doesn't repeat it.
```

[`/reflect`](../../skills/reflect/SKILL.md) sends the thread to three parallel reviewers, then a synthesizer sorts the proposals into `Accepted`, `Rejected`, and `Backlog` and waits for your approval before any skill changes. Approve a proposal only if it would change a future decision. One weird session is an anecdote, not a rule.

## Fix the environment with `/correct`

When you correct agents for the same mistake again and again, the fix belongs in the repo, not in your next prompt. Rank the options by how well they hold:

1. Make the mistake impossible with architecture or a better data structure.
2. Block it with types, or with a lint or CI check whose error names the fix.
3. Catch it with a test.
4. Write it down as a doc or agent rule. Nothing fails when an agent skips a rule, so this comes last.

Human review isn't on the list. A reviewer who must catch the same mistake on every PR is the problem this fixes. [`/correct`](../../skills/correct/SKILL.md) does the work:

```text
/correct agents keep calling the database client directly instead of going through the repository layer
```

It reads recent commits, reverts, review comments, and comments that explain workarounds, then groups the mistakes into classes. A class counts once it has happened twice. It fixes the most frequent classes one commit each, at the highest level that works, and proves each new check fails on a real past mistake. It also keeps a table in the agent instruction file that pairs each rule with what enforces it, so a rule that nothing enforces shows up as a repeat. The reply lists each class with its evidence, the level chosen, and why a higher level didn't work.

Run it with no argument and it finds the classes from history on its own. `/reflect` and `/correct` split the work. `/reflect` improves skills from one session. `/correct` changes the repo so a mistake class can't come back. Pair it with `/architect` when the fix is a new boundary. [Run many programs in parallel](./07-overnight.md#run-many-programs-in-parallel) has a prompt that does both across a whole repo.

## Author a focused skill

When you already know the workflow you want to capture:

```text
/p3-mode write a skill for verifying database migrations in this repo
```

Writing a skill matches the [Authoring or modifying a skill playbook](../../skills/p3-mode/playbooks/authoring-a-skill.md), which writes a thin `SKILL.md` with `name` and `description` frontmatter, tests the description trigger, validates the frontmatter and links, and ships the result through the [Opening a PR playbook](../../skills/p3-mode/playbooks/opening-a-pr.md). Agent-facing prose has a higher bar than human prose, because an unhelpful sentence becomes an instruction some future agent follows. Let the playbook hold that bar rather than writing a `SKILL.md` freehand.

If the skill lands in your p3-stack clone, rerun `./install.sh` so it gets linked.

One special case has its own generator. A skill that must drive your app and prove behavior is a verification skill, so use [`/create-verification-skill`](../../skills/create-verification-skill/SKILL.md) and [`/maintain-verification-skill`](../../skills/maintain-verification-skill/SKILL.md) instead. [Verify and ship](./06-verify-and-ship.md#create-a-project-verification-skill) covers both.

## Write docs to a standard with `/technical-writing`

Skills aren't the only prose you ship. For docs, RFCs, readmes, PR descriptions, and commit messages:

```text
/technical-writing review the readme changes
```

[`/technical-writing`](../../skills/technical-writing/SKILL.md) applies a layered standard with one goal, prose a tired engineer understands on the first read. It picks the document's mode first (tutorial, how-to, reference, or explanation), then works sentence by sentence: who does what, one thought per sentence, nothing readable two ways. Use it to review what you or an agent just wrote, or name it up front when you ask for a doc.

## Test a skill change blind

A skill edit affects every future session, so test it like the experiment it is. The same goes for adopting someone else's skill. Check that it makes the agent better on your work before you keep it.

```text
/p3-mode run the eval playbook on this skill change. same task for both variants, candidates stay blind.
```

When a skill keeps missing and you know what it should do, change and test it in one task:

```text
/p3-mode update the review skill so it flags missing migrations, and eval the change.
```

Asking for the eval up front keeps the edit honest. A fix written from one bad session tends to overfit that session, and over many edits the skill drifts. The eval catches the drift before it ships.

The [Eval playbook](../../skills/p3-mode/playbooks/eval.md) is built around one failure mode, the observer effect. An agent that knows it's being evaluated behaves differently. So candidate agents get an organic-looking task in sanitized directories, never the words "eval" or "candidate", and never each other's existence. Each candidate is its own `delegate_task` with a self-contained brief, and gets only that brief. One judge on a different model family scores all outputs under neutral labels, and chain-following gets graded from which files each candidate actually read, checked in its thread with `t3_thread_read`, not from what it claims.

Read every output yourself before accepting the verdict. If you disagree with the judge, suspect the rubric before you suspect your judgment.

## Build a bot UI with `/make-bot-ui`

One situational skill builds your own controls for the agent. [`/make-bot-ui`](../../skills/make-bot-ui/SKILL.md) builds a small page whose buttons wake the agent over a webhook task, a `schedule_task` with a `{"type":"webhook"}` schedule. For example, you could swipe through a review queue and have each swipe ask the agent to act on that item. A server on your machine holds the webhook URL, which is the credential, so it never reaches the browser or the chat. Any signing secret comes in through `request_secret`, never pasted into chat. The skill also covers exposing the page on Tailscale.

**Pitfall:** don't edit a skill mid-task because it's misbehaving. Fix it in its own PR and keep the task moving. A skill edit that ships tangled into feature work is invisible to review and impossible to evaluate.

Next: [Recipes and pitfalls](./10-recipes-and-pitfalls.md).
