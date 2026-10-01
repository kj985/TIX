import unittest

from gigtool.config import Project
from gigtool.projects import detect_project, normalise

PROJECTS = [
    Project("The Superjesus", ["Superjesus", "Super Jesus"]),
    Project("Sarah & Mick", ["Sarah & Mick", "Sarah and Mick", "Sarah + Mick"]),
    Project("Sarah McLeod", ["solo"]),
]


def detect(title="", lineup=None, description="", fallback="Sarah McLeod"):
    return detect_project(title, lineup or ["Sarah McLeod"], description, PROJECTS, fallback)


class DetectProjectTests(unittest.TestCase):
    def test_normalise_treats_ampersand_plus_and_as_same(self):
        self.assertEqual(normalise("Sarah & Mick!"), "sarah and mick")
        self.assertEqual(normalise("Sarah+Mick"), "sarah and mick")

    def test_title_match(self):
        self.assertEqual(detect("The Superjesus - Live").project, "The Superjesus")
        self.assertEqual(detect("Sarah + Mick").project, "Sarah & Mick")
        self.assertEqual(detect("Sarah and Mick Duo Tour").project, "Sarah & Mick")

    def test_lineup_match(self):
        d = detect(lineup=["Sarah McLeod", "The Superjesus"])
        self.assertEqual(d.project, "The Superjesus")
        self.assertIn("lineup", d.reason)

    def test_description_match(self):
        self.assertEqual(detect(description="With The Superjesus").project, "The Superjesus")

    def test_title_beats_description(self):
        d = detect("Sarah & Mick", description="Supporting The Superjesus")
        self.assertEqual(d.project, "Sarah & Mick")

    def test_whole_words_only(self):
        self.assertEqual(detect("Solomon Festival", fallback=None).project, None)

    def test_fallback(self):
        d = detect("Sarah McLeod & Band")
        self.assertEqual(d.project, "Sarah McLeod")
        self.assertIn("default", d.reason)
        self.assertIsNone(detect("Something", fallback=None).project)


if __name__ == "__main__":
    unittest.main()
