"""Tests for the Planet Korvax generator.

Usage, from the tools folder: python -m unittest test_generate_planet -v
"""
import collections
import json
import random
import unittest
from pathlib import Path

from planet_gen import reach, worldmap

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

STEP = worldmap.STEP
OPPOSITE = worldmap.OPPOSITE


def walk(world, start, blocked=()):
    seen, todo = {start}, [start]
    while todo:
        x, y = todo.pop()
        for d in world.links[(x, y)]:
            nxt = (x + STEP[d][0], y + STEP[d][1])
            if nxt not in seen and nxt not in blocked:
                seen.add(nxt)
                todo.append(nxt)
    return seen


class WorldMapTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world = worldmap.build(random.Random(2026))

    def test_every_room_is_linked_both_ways(self):
        w = self.world
        self.assertEqual(len(w.links), 100)
        for (x, y), links in w.links.items():
            for d, pos in links.items():
                other = (x + STEP[d][0], y + STEP[d][1])
                self.assertEqual(w.links[other][OPPOSITE[d]], pos)
        self.assertEqual(len(walk(w, worldmap.START)), 100)

    def test_the_gate_is_the_only_way_to_the_final_stretch(self):
        w = self.world
        self.assertEqual(w.final[1], 9)
        self.assertIn(w.final, w.behind_gate)
        self.assertEqual(len(w.links[w.gate]), 2)
        self.assertEqual(walk(w, worldmap.START, blocked={w.gate}) & w.behind_gate, set())
        self.assertEqual(sorted(w.gate_sides.values()), ["L", "R"])

    def test_progression_counts(self):
        w = self.world
        got = collections.Counter(w.treasure.values())
        self.assertEqual(got, {"AlienArtifact": 4, "GunPowerup": 3, "HpPowerup": 3, "FuelPowerup": 6})
        self.assertEqual(sorted(w.bosses.values()), ["FallenExtranaut", "HeadBoss", "OctoBoss", "OrbBoss"])
        for at in list(w.treasure) + list(w.bosses):
            self.assertNotIn(at, w.behind_gate)
        for at in w.bosses:
            self.assertEqual(w.treasure[at], "AlienArtifact")
            self.assertEqual(len(w.links[at]), 1)

    def test_save_points_are_never_far(self):
        w = self.world
        self.assertIn(worldmap.START, w.save_points)
        self.assertTrue(8 <= len(w.save_points) <= 10)
        for at in w.links:
            nearest = min(worldmap.distance(w, at, s) for s in w.save_points)
            self.assertLessEqual(nearest, 6)

    def test_zones_and_kinds(self):
        w = self.world
        self.assertEqual(set(w.zone.values()), set(range(5)))
        kinds = collections.Counter(w.kind.values())
        self.assertEqual(kinds["start"], 1)
        self.assertEqual(kinds["gate"], 1)
        self.assertEqual(kinds["final"], 1)
        self.assertEqual(kinds["boss"], 4)
        self.assertEqual(kinds["vault"], 6)
        self.assertGreaterEqual(kinds["infested"], 6)
        for at in w.save_points:
            self.assertIn(w.kind[at], ("start", "normal"))

    def test_same_seed_same_world(self):
        again = worldmap.build(random.Random(2026))
        self.assertEqual(again.links, self.world.links)
        self.assertEqual(again.kind, self.world.kind)


if __name__ == "__main__":
    unittest.main()
