# The p3-stack guide

p3-stack works best when you stop micromanaging the agent. You describe what you want and how you'll know it's done. `/p3-mode` picks the playbook, runs the other skills as the steps need them, and shows you the evidence. This guide teaches that habit with realistic prompts.

p3-stack adapts [pstack](https://github.com/cursor/plugins/tree/main/pstack) by Lauren Tan for T3 Code.

Here's what you'll learn:

1. [Set up p3-stack](./01-setup.md). Run `./install.sh` and pick your models with `/setup-p3`.
2. [Route work through `/p3-mode`](./02-p3-mode.md). Give it a goal and watch it pick a playbook.
3. [Understand the code](./03-understand.md). A read-only investigation, then `/how`, `/why`, `/teach`, and `/recall` before you edit anything.
4. [Design the change](./04-design.md). `/architect`, `/arena`, `/swarm`, `/interrogate`, prototypes, and plans before code locks in a shape.
5. [Build and clean the change](./05-build-and-clean.md). The build playbooks, `/tdd`, `/unslop`, and `/no-comments`.
6. [Verify and ship](./06-verify-and-ship.md). Prove behavior on the real app, vet numbers with `/benchmark-checklist`, then open a focused PR and drive it to merged.
7. [Run work while you sleep](./07-overnight.md). Trust before loops, an overnight contract, a decision log you can audit, and threads and scheduled tasks that scale past one agent.
8. [Steer with principle names](./08-principles.md). The 24 names that redirect an agent mid-task.
9. [Make it yours](./09-make-it-yours.md). Your own mode, `/correct` for repeated mistakes, and how to test a skill change.
10. [Recipes and pitfalls](./10-recipes-and-pitfalls.md). Prompts to copy and mistakes to skip.

Read the pages in order the first time. After that, each page stands alone.

When you're stuck, or can't tell which skill fits, type [`/p3-help`](../../skills/p3-help/SKILL.md) with your question:

```text
/p3-help which skill should i use to review this branch?
```

It answers, hands you a prompt to send, and links the skill or guide page the answer came from. It doesn't start the work, because a p3-stack run spends real tokens, so you send the prompt when you're ready.

## If you only remember one thing

Give the agent a goal and a way to check it, in your own words:

```text
/p3-mode the export writes duplicate rows when a retry lands mid-run. repro first, then fix and verify.
```

You don't need to name a playbook or list skills. "repro first" and a checkable outcome are all the routing signal `/p3-mode` needs. It matches the [Bug fix](../../skills/p3-mode/playbooks/bug-fix.md) playbook, copies the steps into a todo list, and calls the right skills as each step fires.

Next: [Set up p3-stack](./01-setup.md).
