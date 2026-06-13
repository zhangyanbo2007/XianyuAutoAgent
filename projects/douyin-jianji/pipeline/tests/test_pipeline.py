"""Tests for batch pipeline script collection."""

import unittest
from pathlib import Path

from pipeline import collect_input_scripts, make_output_slug


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parent


class PipelineIntegrationTest(unittest.TestCase):
    def test_collect_demand_directory_returns_four_scripts(self):
        scripts = collect_input_scripts(PROJECT / "demand")

        self.assertEqual(len(scripts), 4)
        self.assertEqual([script["block_index"] for script in scripts], [0, 0, 1, 2])

    def test_output_slugs_are_stable_and_unique(self):
        scripts = collect_input_scripts(PROJECT / "demand")
        slugs = [make_output_slug(script) for script in scripts]

        self.assertEqual(len(slugs), len(set(slugs)))
        self.assertTrue(any("618" in slug for slug in slugs))
        self.assertTrue(any("光伏前期手续" in slug for slug in slugs))


if __name__ == "__main__":
    unittest.main()
