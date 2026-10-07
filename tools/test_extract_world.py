import collections
import unittest
from pathlib import Path

import extract_world

PICKLE = Path(__file__).resolve().parent.parent / "ExtranautPython" / "data" / "zorta.xn0"


class ExtractWorldTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world = extract_world.convert(extract_world.load_planet(PICKLE))
        cls.rooms = {(r["x"], r["y"]): r for r in cls.world["rooms"]}

    def test_has_every_room_once(self):
        self.assertEqual(len(self.world["rooms"]), 100)
        self.assertEqual(set(self.rooms), {(x, y) for x in range(10) for y in range(10)})

    def test_start_state(self):
        self.assertEqual(self.world["start_room"], [4, 2])
        self.assertEqual(
            self.world["player"],
            {"max_hp": 5, "max_fuel": 2000, "gun_level": 1, "artifacts": 0},
        )

    def test_sheets(self):
        self.assertEqual(len(self.world["sheets"]), 11)
        self.assertEqual(self.world["sheets"], sorted(self.world["sheets"]))
        self.assertIn("greenRocksDark", self.world["sheets"])

    def test_tiles_are_in_bounds_and_counted(self):
        total = 0
        for room in self.world["rooms"]:
            for layer in ("background", "midground", "foreground"):
                for tx, ty, sheet, ax, ay in room["layers"][layer]:
                    total += 1
                    self.assertTrue(0 <= tx < 30 and 0 <= ty < 24)
                    self.assertTrue(0 <= sheet < 11)
                    self.assertTrue(0 <= ax < 8 and 0 <= ay < 8)
        self.assertEqual(total, 81015)

    def test_walls(self):
        walls = [w for room in self.world["rooms"] for w in room["walls"]]
        self.assertEqual(len(walls), 4665)
        for wall in walls:
            self.assertEqual(len(wall), 4)
            for value in wall:
                self.assertIsInstance(value, int)
                self.assertEqual(value % 32, 0)

    def test_monsters(self):
        counts = collections.Counter(
            m[0] for room in self.world["rooms"] for m in room["monsters"]
        )
        self.assertEqual(sum(counts.values()), 428)
        self.assertEqual(len(counts), 25)
        self.assertEqual(counts["AimerTurret"], 79)
        self.assertEqual(counts["SavePoint"], 10)
        self.assertEqual(counts["AlienArtifact"], 4)

    def test_animated_tiles(self):
        animated = [a for room in self.world["rooms"] for a in room["animated"]]
        self.assertEqual(len(animated), 130)
        for a in animated:
            self.assertIn(a["layer"], ("background", "midground", "foreground"))
            self.assertIn(a["sheet"], ("animations", "ruinsAnimated"))
            self.assertTrue(0 <= a["row"] < 4)

    def test_start_room_contents(self):
        room = self.rooms[(4, 2)]
        self.assertEqual(room["music"], "zortaSurface")
        self.assertEqual(room["player_start"], [480, 352])
        self.assertEqual(room["monsters"], [["SavePoint", 272, 432]])

    def test_rooms_without_player_start(self):
        with_start = [r for r in self.world["rooms"] if r["player_start"] is not None]
        self.assertEqual(len(with_start), 31)


if __name__ == "__main__":
    unittest.main()
