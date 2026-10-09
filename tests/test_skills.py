import glob
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


class ModelFileLookupTest(unittest.TestCase):
    def test_every_mention_of_the_model_file_names_where_it_lives(self):
        missing = []
        for path in sorted(glob.glob(os.path.join(ROOT, "skills", "**", "*.md"), recursive=True)):
            with open(path) as f:
                text = f.read()
            if "p3-models.md" in text and "~/.agents/p3-models.md" not in text:
                missing.append(os.path.relpath(path, ROOT))
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
