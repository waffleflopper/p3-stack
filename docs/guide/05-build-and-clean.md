# Build the change and clean the diff

The build playbooks share one discipline. Say what you observed, let the playbook demand the evidence. This page shows what to put in the prompt for each common build task, then the cleanup habit that keeps diffs reviewable.

## Prompt each build playbook with what you know

A bug prompt states the symptom and asks for a reproduction first:

```text
/p3-mode this command emits two records after a retry. repro first, then fix and verify.
```

A feature prompt states the behavior and what must not change:

```text
/p3-mode add a --json flag. text output stays byte-identical. verify both forms.
```

A refactoring prompt pins behavior before structure moves:

```text
/p3-mode move parsing into one module, zero behavior change. record the current output first and prove it's unchanged after.
```

A perf prompt states the measurement, not a vibe:

```text
/p3-mode startup takes 1.8s on this fixture. trace it, fix the measured cause, show me before and after.
```

Each of these routes to its playbook ([Bug fix](../../skills/p3-mode/playbooks/bug-fix.md), [Feature](../../skills/p3-mode/playbooks/feature.md), [Refactoring](../../skills/p3-mode/playbooks/refactoring.md), [Perf issue](../../skills/p3-mode/playbooks/perf-issue.md)), and the playbook supplies the steps you didn't type: reproduce before fixing, name the data shape before implementing, pin behavior before restructuring, profile before optimizing. The playbook hands the code to a `delegate_task` worker on the matching role from `p3-models.md` (`bug-fix`, `feature, refactoring`, or `perf-issue`) and stays in the lead to review and verify.

For sustained improvement of one number, there's the [Hillclimb playbook](../../skills/p3-mode/playbooks/hillclimb.md). Give it the metric, a target, and a floor on attempts, and it loops one hypothesis at a time with a frozen measurement harness. It keeps wins and reverts everything else.

Both perf playbooks run [`/benchmark-checklist`](../../skills/benchmark-checklist/SKILL.md) on their numbers. Perf issue vets its baseline and every number after it, and Hillclimb vets its harness before freezing it. [Verify and ship](./06-verify-and-ship.md#vet-a-measured-number-with-benchmark-checklist) shows when to type it yourself.

Sometimes you want the cause before any fix. For a live symptom, such as a leak, an idle CPU spin, or a visual glitch, the [Runtime forensics playbook](../../skills/p3-mode/playbooks/runtime-forensics.md) instruments the running process through the `preview_*` or `device_*` tools. For a profile you already captured, the [Trace forensics playbook](../../skills/p3-mode/playbooks/trace-forensics.md) reads the artifact and maps the hot frame to source. Both return a diagnosis, not a fix:

```text
/p3-mode here's a cpuprofile from the slow startup. tell me where the time goes and which source lines own it. no fix yet.
```

## Write the failing test first with `/tdd`

When a bug has a cheap local test path, the whole prompt can be two words:

```text
/tdd implement
```

In context, that's enough. [`/tdd`](../../skills/tdd/SKILL.md) writes the smallest test that fails for the intended reason, then the fix, then reruns the test. If a test would need broad harness setup or brittle mocks, the skill says so and uses the closest executable check instead. Don't force a test where a real command is stronger evidence.

## Load the TypeScript rules by name

[`typescript-best-practices`](../../skills/typescript-best-practices/SKILL.md) turns the type-system principles into concrete rules: discriminated unions, `unknown` at boundaries, exhaustive variants, schema-derived types. It doesn't load on its own, so type `/typescript-best-practices` when a task touches `.ts` or `.tsx` files.

## Clean before you commit

The [Opening a PR playbook](../../skills/p3-mode/playbooks/opening-a-pr.md) runs [`/unslop`](../../skills/unslop/SKILL.md) over the diff before each commit. It writes the PR title, PR description, and commit bodies with [`/technical-writing`](../../skills/technical-writing/SKILL.md), then applies `/unslop` to them too.

For prose, `/unslop` takes a target and any extra rules you have:

```text
/unslop the readme changes, no emdashes
```

You'll develop your own shorthand. The skill reads intent fine from terse prompts like `unslop that, tighten it`.

## Strip the comments with `/no-comments`

Comments need their own pass, and not from the agent that wrote them. An author defends its comments the way you'd defend yours. So before review, hand them to fresh eyes:

```text
/no-comments the diff
```

[`/no-comments`](../../skills/no-comments/SKILL.md) hands the diff to [Comment Sicko](../../agents/comment-sicko.md) in a `delegate_task` on your `judgment and prose` model. Comment Sicko is a read-only reviewer that gets only its brief and the scope, with a short keep list: license headers, doc comments on a public API, links that explain what code can't, behavior forced by an external dependency you can't reshape. Everything else goes. A surprise in your own code gets no such pass. The comment comes back as a refactor flag, and `/no-comments` fixes the flags it accepts at the root cause. When a comment claims a constraint, "do not remove", the skill offers to encode the claim as a type, test, or lint, and waits for your answer in the thread. Either way, the comment comes out.

The division of labor is worth keeping straight. `/unslop` cleans slop out of the diff and the prose, `/technical-writing` sets the standard for docs and PR text, and `/no-comments` hands the comments to a reviewer who didn't write them.

**Pitfall:** cleanup is not optional polish. A diff with narrating comments and defensive dead weight reads as unfinished to reviewers, and the extra code is where the next bug hides. If the diff feels padded, say `unslop the diff` before you commit, not after review calls it out.

Next: [Verify and ship](./06-verify-and-ship.md).
