"""Tests for the Planet Korvax generator.

Usage, from the tools folder: python -m unittest test_generate_planet -v
"""
import collections
import json
import random
import unittest
from pathlib import Path

from planet_gen import reach

TOOLS = Path(__file__).resolve().parent


def room(*rows):
    """A 30x24 room from a short picture: rows are padded with rock."""
    rows = [r.ljust(30, "#") for r in rows]
    rows += ["#" * 30] * (24 - len(rows))
    return reach.parse(rows)


class ReachTest(unittest.TestCase):
    def test_walks_along_a_floor(self):
        solid = room("#" * 30, "#" + "." * 28 + "#")
        got = reach.reachable(solid, [((1, 1), 0.0)])
        self.assertIn((28, 1), got)

    def test_climbs_eight_cells_but_not_ten(self):
        shaft = ["#" * 30] + ["#.###" for _ in range(11)] + ["#...#"]
        solid = room(*shaft)
        got = reach.reachable(solid, [((3, 12), 0.0)])
        self.assertIn((1, 4), got)  # 8 up
        self.assertNotIn((1, 2), got)  # 10 up

    def test_a_ledge_restarts_the_climb(self):
        rows = ["#" * 30] + ["#..##" for _ in range(6)] + ["#.###" for _ in range(6)] + ["#...#"]
        solid = room(*rows)
        got = reach.reachable(solid, [((3, 13), 0.0)])
        self.assertIn((1, 1), got)

    def test_falling_is_free(self):
        rows = ["#" * 30] + ["#.#" for _ in range(20)]
        solid = room(*rows)
        got = reach.reachable(solid, [((1, 1), reach.BUDGET)])
        self.assertIn((1, 20), got)
        self.assertNotIn((1, 0), got)

    def test_ceiling_opening_needs_a_reserve(self):
        near = room(".." + "#" * 28, *["..##" for _ in range(5)], "####")
        far = room(".." + "#" * 28, *["..##" for _ in range(7)], "####")
        for solid, ok in ((near, True), (far, False)):
            start = max(y for y in range(24) if (0, y) not in solid)
            got = reach.reachable(solid, [((0, start), 0.0)])
            self.assertEqual(reach.can_leave(got, "N", 0), ok)

    def test_entries_and_exits(self):
        self.assertEqual(reach.entry("W", 10), ((0, 9), 0.0))
        self.assertEqual(reach.entry("E", 10), ((29, 9), 0.0))
        self.assertEqual(reach.entry("N", 5), ((6, 0), reach.BUDGET))
        self.assertEqual(reach.entry("S", 5), ((6, 22), reach.BUDGET - reach.CEILING_RESERVE))
        self.assertEqual(reach.exit_cells("W", 10), [(0, 7), (0, 8), (0, 9)])
        self.assertEqual(reach.exit_cells("S", 5), [(5, 23), (6, 23), (7, 23)])


if __name__ == "__main__":
    unittest.main()
