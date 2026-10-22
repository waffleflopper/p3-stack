---
name: ship-it
description: Carry a change from finished work to a merged PR without the human. Use only when the user's own message asks to ship it ("$ship-it", "/ship-it", "ship it"), with or without an issue.
---

# Ship it

**The user's own "ship it" is the authorization. Prove the change, get an independent review, open the PR, clear the bots, start CI, merge on green.** It closes out whatever the rest of the request built: a feature, a fix, a perf repair, an investigation that ended in a change. No issue is needed; the request is the spec.

## What the grant covers

Invoking this skill authorizes, for this change only: commit, push a new branch, open a PR, reply to and resolve its review threads, add the repository's CI-start label, merge the PR once it is green and clean, and sync the local base branch.

It does not authorize: deploys or previews, anything touching a production database or a remote migration, force-pushing a branch you did not create, overriding branch protection, closing issues the PR does not complete, or merging an integration branch into trunk. A later request stays a new request; shipping one change does not ship the next.

The repository's own instructions (AGENTS.md, CLAUDE.md, its PR and verification skills, its CI docs) set the gates: which checks run, which verification proves behavior, which label starts CI, how PR bodies read. This skill supplies the authorization and the loop. Where the two disagree on a gate, the repository wins; on authorization, this skill does.

## Base branch

Trunk unless the request names another base. "Ship it into `feat/x`" targets the integration branch: each PR merges there, the integration branch stays synced with trunk, and the final integration PR into trunk is the human's unless they ship that one too.

## Steps

1. **Finish and prove the change.** Run the repository's local checks on the committed head and its verification for every behavior the change touches. When the change alters how a feature works, update the affected verification recipes in the same change and prove each changed step. Batch everything into one commit series before the first push. Every push costs a bot review and, once labeled, a CI run.
2. **Independent review before the first push.** Delegate one review of the full diff against the request to a model family other than the author's (`delegate_task`, resolved from the `interrogate reviewers` line in `p3-models.md` (project root, else `~/.agents/p3-models.md`), else `orchestrator_capabilities`). The brief carries the request, the diff range, the repository's review guidelines, and the verification evidence. Fix real findings and re-run only the affected checks. Bots on the PR are a second net, not the first.
3. **CodeRabbit CLI, once, never waiting.** If `coderabbit` is installed, check `coderabbit usage`. If a review is available, run `coderabbit review --agent --committed --base <base>` and triage the findings like any other review. If it reports a rate limit or no remaining reviews, skip it and continue. Never sleep for quota, retry, or spend usage credits.
4. **Open the PR.** Push, open it ready (not draft) against the base, and `link_pull_request` it. Write the body per the repository's PR rules. Attach screenshots for visible UI changes. With no issue, the body states the request in a sentence. Grep the body for `close[sd]?|fix(e[sd])?|resolve[sd]?` before an issue number and keep only references the PR fully completes.
5. **Clear the review bots.** Bots that review on open and on push are the loop. Arm `watch_pull_request`, plus a 20-minute fallback wake for a bot that stays silent (a background `sleep 1200` where the harness wakes on exit, else a `schedule_task` interval deleted on the next wake), and end the turn. On each wake, read every thread with `gh` and triage skeptically per `../p3-mode/references/bugbot-triage.md`: fix real defects, dismiss noise with a concrete reason on the thread. Batch all fixes from a round into one push, then reply and resolve. A fix push that no bot reviews gets the step 2 reviewer on the fix range before it can merge. A bot that posts "rate limited", "review skipped" or nothing within about 20 minutes of a push is absent for that head. Never re-request it or wait for it. Clean means every bot that did review the current head has no actionable findings.
6. **Start CI.** If the repository gates CI behind a label, add it now, not before review is clean. Follow the repository's rule for later pushes (for example, remove the label before a fix push and re-add it once that round is clean). If the repository runs CI on every push, there is nothing to add. Watch with `watch_pull_request`. Classify a failure before acting: a failure in the diff's code gets a fix, which is a new head and returns to step 5; infrastructure or flake gets one rerun; a second identical failure gets diagnosed, not retried.
7. **Merge.** Recheck right before merging: head SHA unchanged since CI ran, required checks green on that head, `gh pr view` mergeable, no unresolved actionable thread, and any repository pre-merge obligation met (for example, telling the human a schema change needs a separately run migration). Merge with the repository's method, defaulting to `gh pr merge <pr> --squash --match-head-commit <sha>`. Confirm the merged state and intended issue closures, fast-forward the local base branch when the checkout is clean, `unwatch_pull_request`, and report.

## Delegated workers

A delegated child cannot watch a PR, and the T3 harness forbids it to poll. A child that ships runs steps 1 to 4, then returns the PR URL, head SHA and pending review and check state. Its parent owns steps 5 to 7 and sends any fix round back as a new brief. Never sleep-poll a PR from a child.

## Stop and report

Stop before merging, with the PR ready, when a genuine product decision no text settles appears, when a review finding needs scope the request did not grant, when CI fails in code the diff does not touch and the base is current, or when a repository gate requires the human. Say exactly what remains.

When a tool only the human can fix is down (a design app, an auth session, a quota they control), tell them in one line right away and continue with what does not need it.

**Reply:** the PR link and its final head SHA, what each review round found and how it was resolved, CI result, merge state and local sync, and anything left for the human.
