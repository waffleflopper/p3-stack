---
name: setup-p3
description: Configure which models p3-stack uses per role, drawn only from a pool of models you name. Resolves them against your available models and writes p3-models.md, which overrides the skill defaults. Use for /setup-p3, "configure p3 models", or changing p3-stack's model choices.
---

# Setup p3

Write `p3-models.md`, a file that sets p3-stack's model per role. Ask whether it goes in the current project root or in `~/.agents/p3-models.md` (global). Every reader looks in the project root first, else the global file, so a project file wins.

## Steps

### 1. Load current state

The roles are the labels shown in step 5. If `p3-models.md` already exists at the chosen location, read it and treat its `# pool:` line and its role values as the current choices. A line whose role is not in step 5, such as `how critics`, is from a retired role. Drop it. Drop a `# budget:` line too.

### 2. Ask for the pool

Ask plainly in the thread which models p3-stack may use, each with a reasoning level. For example: "Opus 5.5 High, GPT Sol 6.1 XHigh, Sonnet 5.5 High, DeepSeek V4.1 Flash Max". Plain names or exact ids are both fine. The same model at two reasoning levels is two pool entries. On a re-run, offer the recorded pool as the current answer. Every model this skill writes comes from this list. Never add, swap, or upgrade a model the user did not name.

### 3. Resolve the pool

Call `orchestrator_capabilities`. It lists the provider instances and models you can pass to `delegate_task` in this session, custom models included, with each model's reasoning options. That is the only source. If it returns nothing, stop and tell the user. Resolve each entry to one provider instance, one model id, and one reasoning value.

- **Version.** Match the version the user named exactly. "V4.1 Flash" never resolves to `V4 Flash`. A name that matches nothing, or matches several versions, gets asked about with the candidates listed.
- **Instance.** One model can appear under several instances, such as GPT Sol under both `codex` and `opencode` (prefixed `openai/`). Prefer the maker's native instance over an aggregator, and say which you picked. Two instances of one provider, such as `claudeAgent` and a second Claude instance, are separate accounts and a real choice. Ask once and apply the answer to every entry from that provider.
- **Reasoning.** The option id differs per provider (`effort`, `reasoningEffort`, `variant`), and so does the spelling of its values (`xhigh`, `Xhigh`). Match the level case-insensitively and write the value as the catalog spells it. If the model lacks the named level, flag it and list the levels it has. Never move it to a neighbor silently. A model with no reasoning options takes no effort token.
- **Confirm.** Show the resolved pool in the entry format from step 5. Ask only about flagged entries.

### 4. Map roles and confirm

Fill every role from the pool alone. On a re-run, keep each role whose value is still in the pool. Otherwise recommend:

- `judgment and prose`, `hardest tasks`, `how explainer`, `why synthesizer`, `reflect judgment, divergent, synthesizer`: the strongest entry.
- `feature, refactoring`, `bug-fix`, `perf-issue`, `hillclimb`, `how explorer`, `why investigators`, `swarm workers`, `reflect tooling`: the fast strong coder.
- `arena runners`, `architect runners`, `interrogate reviewers`: one entry per distinct provider in the pool, up to three. The model's maker counts as the provider, so Opus and Sonnet are one. For `arena cross-judge pool`, favor providers the user does not usually run parent threads on, and keep at least two.

Show every role with its value, and list each line step 1 dropped. Ask whether to accept as-is or change specific roles, offering the pool entries plus `inherit-parent` (the role runs on the parent thread's model, so omit the model in `delegate_task`). For panel roles (arena runners, architect runners, interrogate reviewers) the value is a list, and one `delegate_task` runs per entry, `inherit-parent` entries included, so the list length sets the count. `arena cross-judge pool` is also a list, but Arena selects one value from it whose provider differs from the parent's when possible. `swarm workers` is the default model for every worker unless a race or comparison assigns another model per arm.

### 5. Validate and write the file

Every real entry written must be in the `orchestrator_capabilities` result, under the provider instance it resolved to, with a reasoning value that model exposes. `inherit-parent` always passes. If a chosen entry is not available, stop and ask again. Then write `p3-models.md` with a `# pool:` line listing the resolved pool entries, comma separated, and one line per role, using the same labels p3-mode uses. Write each entry as `<providerInstanceId>/<model> (<effort>)`, leaving off the effort when the model has no reasoning options. Overwrite the whole file so re-runs stay idempotent. Shape:

```
# p3 model configuration. One line per role. Delete a line to fall back to the skill default.
# `inherit-parent` as a value: the role runs on the parent thread's model (omit the delegate_task model). Entries in a panel list still count toward its fan-out.
# pool: <entry>, <entry>, <entry>
feature, refactoring: <entry>
bug-fix: <entry>
perf-issue: <entry>
hillclimb: <entry>
judgment and prose: <entry>
hardest tasks: <entry>
how explorer: <entry>
how explainer: <entry>
why investigators: <entry>
why synthesizer: <entry>
reflect tooling: <entry>
reflect judgment, divergent, synthesizer: <entry>
arena runners: <entry>, <entry>, <entry>
arena cross-judge pool: <entry>, <entry>
swarm workers: <entry>
architect runners: <entry>, <entry>, <entry>
interrogate reviewers: <entry>, <entry>, <entry>
```

### 6. Confirm

Tell the user the file was written, where, and that it applies to new sessions. Re-running this skill updates it.

### 7. Offer a verification skill (optional)

Check whether the project has a way to drive the real app for proof (a `verify-*` skill, or an existing harness). If not, offer once: "want a project-local verification skill, so agents can drive the app the way a user does and prove changes work? I can generate one with /create-verification-skill." On yes, invoke `/create-verification-skill`. On no, move on without pushing.
