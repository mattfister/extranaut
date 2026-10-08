"""Tests for the Planet Korvax generator.

Usage, from the tools folder: python -m unittest test_generate_planet -v
"""
import collections
import json
import random
import unittest
from pathlib import Path

import generate_planet
from planet_gen import reach, render, worldmap
from planet_gen import room as roomgen

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

    def test_powerups_fill_the_dead_ends_of_their_zone(self):
        w = self.world
        powerups = ("GunPowerup", "HpPowerup", "FuelPowerup")
        ends = worldmap.dead_ends(w)
        self.assertGreaterEqual(len(ends), 3)
        for zone in range(len(worldmap.ZONES)):
            held = [at for at, name in w.treasure.items() if name in powerups and w.zone[at] == zone]
            zone_ends = [at for at in ends if w.zone[at] == zone]
            tucked = [at for at in held if at in zone_ends]
            self.assertEqual(len(tucked), min(len(held), len(zone_ends)), worldmap.ZONES[zone]["name"])

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
        for feature in worldmap.FEATURES:
            self.assertEqual(kinds[feature], worldmap.FEATURE_ROUNDS, feature)
        for at in w.save_points:
            self.assertIn(w.kind[at], ("start", "normal"))

    def test_same_seed_same_world(self):
        again = worldmap.build(random.Random(2026))
        self.assertEqual(again.links, self.world.links)
        self.assertEqual(again.kind, self.world.kind)


class RoomTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world = worldmap.build(random.Random(2026))
        cls.rooms = {at: roomgen.build(cls.world, at, 2026 * 100 + at[0] * 10 + at[1]) for at in sorted(cls.world.links)}

    def test_every_room_is_sound(self):
        for at, built in self.rooms.items():
            self.assertEqual(roomgen.check(self.world, at, built), [], at)

    def test_rooms_are_the_right_shape(self):
        for at, built in self.rooms.items():
            self.assertEqual(len(built.rows), 24)
            self.assertTrue(all(len(r) == 30 for r in built.rows))

    def test_start_room_is_safe(self):
        built = self.rooms[worldmap.START]
        self.assertIsNotNone(built.player_start)
        self.assertEqual([m[0] for m in built.monsters], ["SavePoint"])

    def test_vaults_open_when_the_room_is_cleared(self):
        for at, kind in self.world.kind.items():
            if kind not in ("vault", "boss"):
                continue
            names = [m[0] for m in self.rooms[at].monsters]
            self.assertEqual(names.count("MonsterDoor2"), 1, at)
            self.assertEqual(names.count(self.world.treasure[at]), 1, at)
            permanent = [n for n in names if n in roomgen.UNKILLABLE]
            self.assertEqual(sorted(permanent), sorted(["MonsterDoor2", self.world.treasure[at]]), at)

    def test_bosses_are_in_their_rooms(self):
        for at, boss in self.world.bosses.items():
            names = [m[0] for m in self.rooms[at].monsters]
            self.assertEqual(names.count(boss), 1, at)

    def test_infested_rooms_swarm_with_balls(self):
        for at, kind in self.world.kind.items():
            if kind == "infested":
                balls = [m for m in self.rooms[at].monsters if m[0] == "BallMonster"]
                self.assertGreaterEqual(len(balls), 25, at)

    def test_harder_than_zorta(self):
        counts = [
            sum(1 for m in built.monsters if m[0] in roomgen.COST)
            for at, built in self.rooms.items()
            if self.world.kind[at] == "normal"
        ]
        self.assertGreaterEqual(sum(counts) / len(counts), 6.0)

    def _count(self, at, *names):
        return sum(1 for m in self.rooms[at].monsters if m[0] in names)

    def test_each_zone_has_its_own_hostiles(self):
        seen = collections.defaultdict(collections.Counter)
        for at, built in self.rooms.items():
            zone = worldmap.ZONES[self.world.zone[at]]
            if self.world.kind[at] not in ("normal", "vault", "boss", "infested", "gate", "final"):
                continue
            for name, _, _ in built.monsters:
                if name in roomgen.COST and name not in roomgen.ELITES:
                    self.assertIn(name, zone["roster"], (at, zone["name"]))
                    seen[zone["name"]][name] += 1
        # No two zones are led by the same pair of hostiles.
        leaders = {name: tuple(sorted(n for n, _ in counts.most_common(2))) for name, counts in seen.items()}
        self.assertEqual(len(leaders), len(worldmap.ZONES))
        self.assertEqual(len(set(leaders.values())), len(worldmap.ZONES), leaders)

    def test_set_pieces_are_what_they_claim(self):
        hostile = tuple(roomgen.HOSTILE)
        for at, kind in self.world.kind.items():
            if kind == "sanctuary":
                self.assertEqual(self._count(at, *hostile), 0, at)
                self.assertGreaterEqual(self._count(at, "BallMonster"), 3, at)
            elif kind == "gallery":
                self.assertGreaterEqual(self._count(at, "AimerTurret"), 5, at)
                self.assertEqual(self._count(at, *hostile), self._count(at, "AimerTurret"), at)
            elif kind == "spikes":
                self.assertGreaterEqual(self._count(at, "SpikyBallMonster"), 8, at)
            elif kind == "hoverfield":
                self.assertGreaterEqual(self._count(at, "HoverBlock"), 6, at)
                self.assertGreaterEqual(self._count(at, "FlyBot", "Flyer"), 4, at)
            elif kind == "arena":
                self.assertGreaterEqual(self._count(at, "HandBot"), 3, at)
            elif kind == "den":
                self.assertEqual(self._count(at, "BossBot1", "BossBot2"), 2, at)
            elif kind == "honeycomb":
                blocks = sum(row.count(".##.") for row in self.rooms[at].rows)
                self.assertGreaterEqual(blocks, 8, at)
            elif kind == "shaft":
                # Some column is open for most of the room's height.
                tallest = max(sum(row[x] == "." for row in self.rooms[at].rows) for x in range(30))
                self.assertGreaterEqual(tallest, 16, at)

    def test_doors_only_count_what_can_be_cleared(self):
        for at, kind in self.world.kind.items():
            if kind in ("vault", "boss"):
                self.assertEqual(self._count(at, "HoverBlock", "BallMonster"), 0, at)

    def test_treasure_and_save_points_are_placed(self):
        for at, name in self.world.treasure.items():
            self.assertEqual([m[0] for m in self.rooms[at].monsters].count(name), 1, at)
        for at in self.world.links:
            saves = [m for m in self.rooms[at].monsters if m[0] == "SavePoint"]
            self.assertEqual(len(saves), 1 if at in self.world.save_points else 0, at)

    def test_the_gate_holds_the_artifact_door(self):
        names = [m[0] for m in self.rooms[self.world.gate].monsters]
        self.assertEqual(names.count("ArtifactDoor"), 1)

    def test_only_the_final_room_has_a_hole(self):
        for at, built in self.rooms.items():
            self.assertEqual(built.hole is not None, at == self.world.final)

    def test_only_known_monsters_are_used(self):
        scenes = TOOLS.parent / "entities" / "monsters"
        for built in self.rooms.values():
            for name, x, y in built.monsters:
                snake = "".join("_" + c.lower() if c.isupper() or c.isdigit() else c for c in name).lstrip("_")
                self.assertTrue((scenes / (snake + ".tscn")).exists(), name)
                self.assertTrue(0 < x < 960 and 0 < y < 768, (name, x, y))


class RenderTest(unittest.TestCase):
    def test_a_box_has_four_inner_walls_and_a_border(self):
        rows = ["#" * 30] + ["#" + "." * 28 + "#"] * 22 + ["#" * 30]
        got = sorted(tuple(w) for w in render.walls(rows))
        inner = [(32, 32, 928, 32), (32, 32, 32, 736), (32, 736, 928, 736), (928, 32, 928, 736)]
        border = [(0, 0, 960, 0), (0, 0, 0, 768), (0, 768, 960, 768), (960, 0, 960, 768)]
        self.assertEqual(got, sorted(inner + border))

    def test_an_open_floor_splits_the_bottom_border(self):
        rows = ["#" * 30] + ["#" + "." * 28 + "#"] * 22 + ["#" * 10 + "..." + "#" * 17]
        got = [tuple(w) for w in render.walls(rows, open_floor=(10, 12))]
        self.assertIn((0, 768, 320, 768), got)
        self.assertIn((416, 768, 960, 768), got)
        self.assertNotIn((0, 768, 960, 768), got)

    def test_a_slope_is_one_diagonal(self):
        rows = ["#" * 30] + ["#" + "." * 28 + "#"] * 21 + ["#" + "." * 10 + "/" + "#" * 18] + ["#" * 30]
        got = [tuple(w) for w in render.walls(rows)]
        self.assertIn((352, 736, 384, 704), got)
        self.assertIn((384, 704, 928, 704), got)  # the floor beyond starts after the slope
        self.assertNotIn((352, 704, 352, 736), got)  # no step in front of it

    def test_edge_tiles(self):
        rows = ["#" * 30] + ["#" + "." * 28 + "#"] * 22 + ["#" * 30]
        got = {(t[0], t[1]): (t[3], t[4]) for t in render.tiles(rows, 7)}
        self.assertEqual(got[(5, 0)], (2, 3))  # ceiling: empty below
        self.assertEqual(got[(5, 23)], (2, 1))  # floor: empty above
        self.assertEqual(got[(0, 5)], (3, 2))  # left wall: empty to the right
        self.assertEqual(got[(29, 5)], (1, 2))
        self.assertEqual(got[(0, 0)], (2, 2))
        self.assertEqual(len(render.background(3)), 720)


class PlanetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world = generate_planet.generate()
        cls.rooms = {(r["x"], r["y"]): r for r in cls.world["rooms"]}
        cls.zorta = json.loads((TOOLS / "zorta.json").read_text())

    def test_is_repeatable(self):
        self.assertEqual(json.dumps(generate_planet.generate()), json.dumps(self.world))

    def test_matches_the_committed_file(self):
        saved = json.loads((TOOLS / "korvax.json").read_text())
        self.assertEqual(saved, json.loads(json.dumps(self.world)))

    def test_has_the_shape_of_zorta(self):
        self.assertEqual(set(self.rooms), {(x, y) for x in range(10) for y in range(10)})
        self.assertEqual(self.world["sheets"], self.zorta["sheets"])
        self.assertEqual(self.world["start_room"], [2, 0])
        self.assertEqual(self.world["player"], self.zorta["player"])
        self.assertTrue(set(self.zorta["rooms"][0]) <= set(self.world["rooms"][0]))

    def test_tiles_exist_and_are_not_blank(self):
        used = set()
        for r in self.rooms.values():
            self.assertEqual(len(r["layers"]["background"]), 720)
            for layer in r["layers"].values():
                for t in layer:
                    used.add((self.world["sheets"][t[2]], t[3], t[4]))
        for sheet, tx, ty in sorted(used):
            self.assertFalse(generate_planet.tile_is_blank(sheet, tx, ty), (sheet, tx, ty))
        self.assertTrue(generate_planet.tile_is_blank("rocks", 0, 0))

    def test_every_room_has_a_tint_music_and_a_player_start(self):
        sounds = TOOLS.parent / "assets" / "sounds"
        for r in self.rooms.values():
            self.assertEqual(len(r["tint"]), 3)
            self.assertTrue((sounds / (r["music"] + ".ogg")).exists())
            self.assertEqual(len(r["player_start"]), 2)

    def test_one_room_has_an_open_floor(self):
        finals = [r for r in self.rooms.values() if r["kind"] == "final"]
        self.assertEqual(len(finals), 1)
        self.assertEqual(finals[0]["y"], 9)
        self.assertIn(".", finals[0]["cells"][23])
        for r in self.rooms.values():
            whole = [0, 768, 960, 768] in r["walls"]
            self.assertEqual(whole, r["kind"] != "final", (r["x"], r["y"]))

    def test_some_rooms_are_infested_with_balls(self):
        infested = [r for r in self.rooms.values() if r["kind"] == "infested"]
        self.assertGreaterEqual(len(infested), 6)
        for r in infested:
            self.assertGreaterEqual(sum(1 for m in r["monsters"] if m[0] == "BallMonster"), 25)


if __name__ == "__main__":
    unittest.main()
