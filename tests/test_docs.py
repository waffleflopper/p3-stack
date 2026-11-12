import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

# Named only to say p3-stack has no such command.
ABSENT = {"loop"}

SMALL = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
# "The twenty-three playbooks" claims the whole set. "Three playbooks scale it up" names a subset, so it is not checked.
CLAIM = re.compile(r"\b(?:(all|has|of|ships|the|with) )?(\d+|[a-z]+(?:-[a-z]+)?) (short |principle )?(skills|principles|playbooks|agents)\b", re.I)
SLASH = re.compile(r"(?:^|(?<=[\s`(|\"']))/([a-z][a-z0-9-]*)(?![\w/<-])", re.M)
LINK = re.compile(r"\]\(<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\)")
FENCE = re.compile(r"^\s*(```|~~~)")
HEADING = re.compile(r"^#{1,6}\s+(.*?)\s*$")


def names(path, keep):
    if not os.path.isdir(path):
        return []
    return sorted(n for n in os.listdir(path) if keep(os.path.join(path, n)))


def is_skill(path):
    return os.path.exists(os.path.join(path, "SKILL.md"))


def is_markdown(path):
    return path.endswith(".md") and os.path.isfile(path)


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def to_number(word):
    if word.isdigit():
        return int(word)
    tens, _, unit = word.lower().partition("-")
    if not unit and tens in SMALL:
        return SMALL.index(tens)
    if tens in TENS[2:] and (unit == "" or unit in SMALL[1:10]):
        return TENS.index(tens) * 10 + (SMALL.index(unit) if unit else 0)
    return None


def anchors(rel):
    seen = {}
    found = set()
    fenced = False
    for line in read(rel).split("\n"):
        if FENCE.match(line):
            fenced = not fenced
        heading = None if fenced else HEADING.match(line)
        if not heading:
            continue
        plain = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", heading.group(1)).replace("`", "").replace("*", "")
        slug = re.sub(r"\s", "-", re.sub(r"[^\w\s-]", "", plain.strip().lower()))
        repeat = seen.get(slug, 0)
        seen[slug] = repeat + 1
        found.add(f"{slug}-{repeat}" if repeat else slug)
    return found


def line_of(text, index):
    return text.count("\n", 0, index) + 1


def collect():
    skills = names(os.path.join(ROOT, "skills"), is_skill)
    principles = [s for s in skills if s.startswith("principle-")]
    commands = [s for s in skills if not s.startswith("principle-")]
    playbooks = [n[:-3] for n in names(os.path.join(ROOT, "skills", "p3-mode", "playbooks"), is_markdown)]
    agents = [n[:-3] for n in names(os.path.join(ROOT, "agents"), is_markdown)]
    guide = [f"docs/guide/{n}" for n in names(os.path.join(ROOT, "docs", "guide"), is_markdown)]
    return skills, principles, commands, playbooks, agents, ["README.md"] + guide


class DocsMatchTreeTest(unittest.TestCase):
    def setUp(self):
        self.skills, self.principles, self.commands, self.playbooks, self.agents, self.docs = collect()

    def test_slash_references_name_a_skill_folder(self):
        bad = []
        for doc in self.docs:
            text = read(doc)
            for m in SLASH.finditer(text):
                if m.group(1) not in self.skills and m.group(1) not in ABSENT:
                    bad.append(f"{doc}:{line_of(text, m.start())} names /{m.group(1)}, which no skills/ folder provides")
        self.assertEqual(bad, [])

    def test_relative_links_and_anchors_resolve(self):
        bad = []
        for doc in self.docs:
            text = read(doc)
            for m in LINK.finditer(text):
                href = m.group(1)
                if re.match(r"^[a-z][a-z0-9+.-]*:", href, re.I):
                    continue
                target, _, anchor = href.partition("#")
                path = os.path.normpath(os.path.join(os.path.dirname(doc), target)) if target else doc
                where = f"{doc}:{line_of(text, m.start())} links to {href}"
                if not os.path.exists(os.path.join(ROOT, path)):
                    bad.append(f"{where}, which does not exist")
                elif anchor and path.endswith(".md") and anchor not in anchors(path):
                    bad.append(f"{where}, but {path} has no heading with that anchor")
        self.assertEqual(bad, [])

    def test_readme_skill_list_names_every_skill_folder(self):
        section = re.search(r"^## Skills\n(.*?)(?=^## )", read("README.md"), re.M | re.S)
        self.assertIsNotNone(section, "README.md has no Skills section")
        listed = set(re.split(r"[,\s.]+", section.group(1).strip()))
        missing = [s for s in self.commands if s not in listed]
        self.assertEqual(missing, [], "README.md Skills section does not list these skill folders")

    def test_counts_match_the_tree(self):
        expected = {
            "skills": [len(self.skills), len(self.commands)],
            "principles": [len(self.principles)],
            "playbooks": [len(self.playbooks)],
            "agents": [len(self.agents)],
        }
        bad = []
        for doc in self.docs:
            text = read(doc)
            for m in CLAIM.finditer(text):
                whole, word, qualifier, noun = m.groups()
                claimed = to_number(word)
                kind = "principles" if qualifier else noun.lower()
                if (whole or qualifier) and claimed is not None and claimed not in expected[kind]:
                    bad.append(f'{doc}:{line_of(text, m.start())} says "{m.group(0)}", but the tree has {expected[kind]}')
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
