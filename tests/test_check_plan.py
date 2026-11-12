import os
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
CHECKER = os.path.join(ROOT, "skills", "p3-mode", "scripts", "check-plan.mjs")
RULE = "Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked."
LANES = "\n".join(f"- [ ] Lane {i}. Save `lane-{i}.png`. Pass when evidence exists." for i in range(1, 10)) + "\n- [ ] Lane 10. Regression lane against trunk. Save `lane-10.png`. Pass when trunk and head match."
VALID_PLAN = f"""# Demo

## How to read this
One box is one unit of work and names the evidence. Check a box only when its evidence exists.
The program runs `skills/p3-mode/playbooks/autopilot-full.md`. {RULE}

## Program checklist
### Arm the program
### Spawn owners
### PR mechanics
### Verdict and merge
### Boot recipe
`git show origin/main:` `watch_pull_request` status message `link_pull_request`

## PR 1
**Depends on.** None.
**Files.**
- [ ] Do the thing.
**Build.**
- [ ] Do the thing.
**You see.**
- [ ] Do the thing.
**Verify, unit.** {RULE}
- [ ] Check the thing.
**Verify, live.** {RULE} Ten lanes on the `swarm workers` role at the PR head.
{LANES}
**Verify, perf.** {RULE}
- [ ] Metric. Recorded.
- [ ] Probe. Recorded.
- [ ] Baseline. Recorded.
- [ ] Rule. Recorded.
**Review gate.** None.
**Merge.**
- [ ] Merge when approved.

## Close the program
Close.

## Appendix Prototype evidence
Recorded.
"""
STRAY_HEADING = '"## Example only" after Close the program is not an appendix'


def run_plan(example):
    with tempfile.TemporaryDirectory() as directory:
        path = os.path.join(directory, "plan.md")
        with open(path, "w") as f:
            f.write(VALID_PLAN + example)
        return subprocess.run(["node", CHECKER, path], capture_output=True, text=True)


class CheckPlanFenceTest(unittest.TestCase):
    def assertClean(self, example):
        result = run_plan(example)
        self.assertEqual((result.returncode, result.stdout), (0, ""), example)

    def assertFlags(self, example, message):
        result = run_plan(example)
        self.assertEqual(result.returncode, 1, example)
        self.assertIn(message, result.stdout)

    def test_the_base_plan_is_clean(self):
        self.assertClean("")

    def test_accepts_indented_and_longer_closing_fences(self):
        for indent in ["", " ", "  ", "   "]:
            self.assertClean(f"{indent}```markdown\n## Example only\n{indent}```\n")
        self.assertClean("```markdown\n## Example only\n````\n")

    def test_accepts_nested_backticks_and_tilde_fences(self):
        self.assertClean("````markdown\n```markdown\n## Example only\n```\n````\n")
        self.assertClean("~~~markdown `info`\n## Example only\n ~~~\n")

    def test_keeps_mismatched_shorter_and_suffixed_closers_inside_the_fence(self):
        self.assertClean("````markdown\n~~~\n## Example only\n````\n")
        self.assertClean("````markdown\n```\n## Example only\n````\n")
        self.assertClean("````markdown\n``` info\n## Example only\n````\n")

    def test_rejects_headings_after_a_closer_with_trailing_whitespace(self):
        for suffix in ["  ", "\t"]:
            self.assertFlags(f"```markdown\n## Example only\n```{suffix}\n## Example only\n", STRAY_HEADING)

    def test_checks_prose_outside_the_fence(self):
        self.assertFlags("```markdown\nA colon: inside code\n```\nA colon: outside code.\n", "mid-sentence colon")

    def test_rejects_backtick_info_strings_containing_a_backtick(self):
        self.assertFlags("```markdown `invalid`\n## Example only\n```\n", STRAY_HEADING)

    def test_ignores_punctuation_inside_multi_backtick_spans(self):
        for count in [2, 3, 4]:
            delimiter = "`" * count
            self.assertClean(f"Use {delimiter}echo `x`: “quoted” — example{delimiter}.\n")

    def test_flags_placeholders_inside_multi_backtick_spans(self):
        self.assertFlags("Run ``<command>`` here.\n", "unfilled placeholder")
        self.assertFlags("Run `<command>` here.\n", "unfilled placeholder")
        self.assertClean("Run ``echo `x` `` here.\n")

    def test_checks_prose_after_a_multi_backtick_span_and_unmatched_delimiters(self):
        self.assertFlags("Use ``echo `x`: y``. Bad: prose.\n", "mid-sentence colon")
        self.assertFlags("Use ``unclosed: bad` here.\n", "mid-sentence colon")


if __name__ == "__main__":
    unittest.main()
