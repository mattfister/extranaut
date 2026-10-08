# Planet Korvax Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a generated second campaign planet, Korvax, selectable on the title screen with its own save slots.

**Architecture:** A seeded Python generator writes `tools/korvax.json` in the format of `tools/zorta.json`. The existing Godot importer turns each planet's JSON into room scenes. A planet registry tells saves, the campaign and the title which planet they are dealing with.

**Tech Stack:** Godot 4.7 GDScript, headless `--script` tests, Python 3 standard library with `unittest`.

**Spec:** `docs/superpowers/specs/2026-10-08-planet-korvax-design.md`

---

## Conventions

```bash
GODOT="/c/Users/mattf/Desktop/godot47/Godot_v4.7-stable_win64_console.exe"
# A Godot test:
"$GODOT" --headless --path . --script res://tools/test_save.gd
# Python tests, from the tools folder:
cd tools && python -m unittest test_generate_planet -v
```

Work happens on branch `planet-korvax`. Each task ends with a commit of only
the files it names, plus the `.uid` file Godot writes beside each new script.

## Facts from Zorta's data that the generator relies on

- Monster positions are body centres. A radius-16 body resting on a floor whose
  top is at y has centre y - 16.
- The five rock sheets share one layout. With U, R, D, L meaning "the
  neighbour in that direction is solid":

  | Empty neighbours | Tile |
  |---|---|
  | none | (2, 2) |
  | up | (2, 1) |
  | down | (2, 3) |
  | left | (1, 2) |
  | right | (3, 2) |
  | up and left | (1, 1) |
  | up and right | (3, 1) |
  | down and left | (1, 3) |
  | down and right | (3, 3) |
  | slope rising to the right (empty up and left) | (2, 5) |
  | slope falling to the right (empty up and right) | (4, 5) |

  Any other combination picks the row by up/down (up wins) and the column by
  left/right (both empty gives column 2).
- Background sheets are filled with tile (2, 2).
- Doors have radius 32 and are wedged in passages two cells (64 px) high.
- `monster_door_2` opens when exactly two monster-class entities remain in the
  room. Powerups, save points, hover blocks and doors all count.
- Exit thresholds: x >= 943, x < 17, y >= 742, y < 27, measured at the
  player's centre. The player's radius is 13, so a wall on the room border is
  never touched.
- Entering a room from below places the player at y = 720; from above, y = 16.
- Jetpack: a full 2000-fuel tank lifts the player about 11 cells.

## File structure

| File | Responsibility |
|---|---|
| `tools/planet_gen/__init__.py` | empty |
| `tools/planet_gen/reach.py` | the player movement model: what can be reached in a cell grid |
| `tools/planet_gen/worldmap.py` | the 10x10 maze, zones, ranks, where progression items go |
| `tools/planet_gen/room.py` | carving one room's cells, gadgets (vault, gate), monster placement |
| `tools/planet_gen/render.py` | cells to walls and tiles |
| `tools/generate_planet.py` | entry point: assembles the world and writes `tools/korvax.json` |
| `tools/test_generate_planet.py` | unittest for all of the above |
| `world/planets.gd` | the planet registry |
| `save/settings.gd` | remembers the last planet chosen |

Each room in `korvax.json` carries three keys beyond Zorta's format, ignored
by the importer and used by tests and debugging: `cells` (24 strings of 30
characters, `#` solid, `.` empty, `/` and `\` slopes), `links` (a map from
`"N"`, `"E"`, `"S"`, `"W"` to the opening's position) and `kind`
(`"start"`, `"normal"`, `"infested"`, `"vault"`, `"boss"`, `"gate"`,
`"final"`).

---

### Task 1: Reachability model

**Files:**
- Create: `tools/planet_gen/__init__.py`, `tools/planet_gen/reach.py`
- Test: `tools/test_generate_planet.py`

Interface:

```python
W, H = 30, 24
BUDGET = 8.0          # cells of climb from a full base tank, conservative
CEILING_RESERVE = 2.0 # left over after reaching a ceiling opening

def parse(rows): ...            # list of 24 strings -> set of solid (x, y)
def standable(solid, cell): ... # empty, in the grid, with solid below
def fly(solid, start, spent=0.0):
    """Cells reachable in one flight from start, as {cell: cheapest cost}.
    Moving up costs 1, sideways 0.5, down or diagonally down 0. Only moves
    into empty in-grid cells; a diagonal needs both orthogonal cells empty."""
def reachable(solid, starts):
    """All cells the player can be in, starting from (cell, spent) pairs:
    fly, then from every standable cell reached, fly again with spent 0."""
def entry(link_dir, pos): ...   # the (cell, spent) a player arrives with
def exit_cells(link_dir, pos):  # cells that count as having left that way
```

Openings: `"W"`/`"E"` position is the floor row f; the opening is rows f-3 to
f-1 of column 0 or 29. `"N"`/`"S"` position is the left column c; the opening
is columns c to c+2 of row 0 or 23.

- Entry W: `((0, f-1), 0)`. Entry E: `((29, f-1), 0)`.
- Entry N: `((c+1, 0), BUDGET)`, falling with no fuel assumed.
- Entry S: `((c+1, 22), BUDGET - CEILING_RESERVE)`.
- Exit W/E: any opening cell. Exit S: any hole cell in row 23.
- Exit N: a hole cell in row 0 reached in a flight at cost
  <= `BUDGET - CEILING_RESERVE`. `reachable` therefore returns
  `{cell: best cost on arrival}` and `can_leave(solid, reach, dir, pos)` tests
  the rule.

- [ ] **Step 1: Write the failing tests**

```python
import unittest
from planet_gen import reach


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
        self.assertIn((1, 4), got)       # 8 up
        self.assertNotIn((1, 2), got)    # 10 up

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

    def test_ceiling_opening_needs_a_reserve(self):
        near = room(".." + "#" * 28, *["..##" for _ in range(5)], "####")
        far = room(".." + "#" * 28, *["..##" for _ in range(7)], "####")
        for solid, ok in ((near, True), (far, False)):
            start = max(y for (x, y) in [(0, y) for y in range(24)] if (0, y) not in solid)
            got = reach.reachable(solid, [((0, start), 0.0)])
            self.assertEqual(reach.can_leave(got, "N", 0), ok)
```

- [ ] **Step 2: Run to see them fail**

Run: `cd tools && python -m unittest test_generate_planet -v`
Expected: `ModuleNotFoundError: No module named 'planet_gen'`.

- [ ] **Step 3: Implement `reach.py`**

`fly` is Dijkstra over cells with the costs above, stopping at `BUDGET`.
`reachable` keeps a best-cost map and a work list: every time a standable
cell is first reached, or reached more cheaply, it is flown from again with
spent 0.

- [ ] **Step 4: Run the tests, expect all to pass**

- [ ] **Step 5: Commit**

```bash
git add tools/planet_gen tools/test_generate_planet.py
git commit -m "Add the player reachability model for the planet generator"
```

---

### Task 2: World map

**Files:**
- Create: `tools/planet_gen/worldmap.py`
- Test: `tools/test_generate_planet.py`

Interface:

```python
START = (2, 0)
ZONES = [  # midground sheet, background sheet, tint, music
    ("rocks", "bgRocks", [0.75, 0.6, 1.0], "zortaSurface"),
    ("rocksBlue", "rockBg", [0.6, 1.0, 0.85], "gravitorZone"),
    ("yellowRocks", "bgYellowRocks", [1.0, 0.6, 0.45], "pyriteZone"),
    ("greenRocks", "greenRocksDark", [0.6, 0.85, 1.0], "emeraldOrbit"),
    ("grayRocks", "redRocksBg", [1.0, 0.55, 0.6], "boilingPoint"),
]

class WorldMap:
    links        # {(x, y): {"N"|"E"|"S"|"W": position}}, symmetric
    depth        # {(x, y): steps from START along links}
    rank         # {(x, y): depth / max depth, 0 to 1}
    zone         # {(x, y): index into ZONES}
    kind         # {(x, y): room kind}
    gate         # the artifact door room
    gate_dir     # the link of the gate room that leads to the final stretch
    final        # the row-9 room with the open floor
    behind_gate  # set of rooms only reachable through the gate
    bosses       # {(x, y): boss class name}
    treasure     # {(x, y): "AlienArtifact"|"GunPowerup"|"HpPowerup"|"FuelPowerup"}
    save_points  # set of rooms

def build(rng) -> WorldMap
```

Algorithm:

1. Spanning tree by randomised depth-first search from `START`.
2. `final` is the deepest row-9 room. Walking back from it toward `START`,
   the gate is the first room that has exactly two tree links and at least
   three rooms behind it; `behind_gate` is the subtree on the far side. Retry
   the tree if none qualifies or if `behind_gate` holds more than 12 rooms.
3. Add 14 extra links between adjacent unlinked rooms, never touching the gate
   and never joining the two sides of it.
4. Link positions: side links get a floor row from 6 to 20; vertical links a
   left column from 4 to 23. In the gate room, a vertical link is placed in
   columns 2 to 8 or 20 to 26 according to which half it belongs to.
5. Zones: `START` and four rooms chosen farthest-first seed a multi-source
   breadth-first search over links.
6. Bosses: four tree leaves outside `behind_gate`, chosen farthest-first from
   each other and at least 5 steps from `START`. Kind `boss`, treasure
   `AlienArtifact`.
7. Gun and HP powerups: six more rooms outside `behind_gate`, not the start,
   gate or a boss room, spread evenly through the rooms sorted by rank, guns
   and HP alternating. Kind `vault`.
8. Fuel powerups: six rooms chosen the same way from what is left. Their kind
   stays `normal` or `infested`.
9. Save points: `START` first, then farthest-first among rooms of kind
   `normal`, until there are 8 and no room is more than 6 steps from one, to a
   limit of 10.
10. Infestations: one in eight of the remaining `normal` rooms without a save
    point become `infested`.

- [ ] **Step 1: Write the failing tests**

```python
import random
from planet_gen import worldmap

OPPOSITE = {"N": "S", "S": "N", "E": "W", "W": "E"}
STEP = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0)}


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

    def test_progression_counts(self):
        w = self.world
        got = collections.Counter(w.treasure.values())
        self.assertEqual(got, {"AlienArtifact": 4, "GunPowerup": 3, "HpPowerup": 3, "FuelPowerup": 6})
        self.assertEqual(sorted(w.bosses.values()), ["FallenExtranaut", "HeadBoss", "OctoBoss", "OrbBoss"])
        for at in list(w.treasure) + list(w.bosses):
            self.assertNotIn(at, w.behind_gate)
        for at in w.bosses:
            self.assertEqual(w.treasure[at], "AlienArtifact")

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
```

- [ ] **Step 2: Run to see them fail** (`No module named ... worldmap`)
- [ ] **Step 3: Implement `worldmap.py`** as described, with `distance(world, a, b)` a breadth-first search over links.
- [ ] **Step 4: Run the tests, expect all to pass**
- [ ] **Step 5: Commit** `git add tools/planet_gen/worldmap.py tools/test_generate_planet.py && git commit -m "Generate the Korvax world map: maze, zones and progression"`

---

### Task 3: Room carving, gadgets and monsters

**Files:**
- Create: `tools/planet_gen/room.py`
- Test: `tools/test_generate_planet.py`

Interface:

```python
class Room:
    rows         # 24 strings: '#', '.', '/', '\\'
    monsters     # [[class name, x, y], ...] in pixels, body centres
    player_start # [x, y] or None

def build(world, at, seed) -> Room
def check(world, at, room) -> list[str]   # problems; empty means sound
```

`build` tries seeds `seed, seed+1, ...` until `check` returns nothing, and
raises after 400 tries.

Carving, on a grid that starts solid:

1. Openings. W/E: carve columns 0 to 3 of rows f-3 to f-1 and protect the
   floor cells beneath. N: carve columns c to c+2 of rows 0 to 3, and protect
   a three-cell ledge at row 6 on one side of the hole. S: carve columns c to
   c+2 of rows 20 to 23.
2. Gadgets, placed before the caves so their rock is protected:
   - Vault: an 8x4 block. Rows 1 and 2 of it form a tunnel six cells long,
     open at one end (the mouth) and closed at the other. The door stands at
     the boundary between the tunnel's first and second cell, the treasure in
     its fifth. A 3x3 porch is carved outside the mouth with a floor under it.
   - Gate: columns 12 to 17 are protected rock for the full height, with one
     tunnel two cells high through them holding the artifact door. Openings
     on the far side of `gate_dir` connect only to the far half.
3. Caves. A hub is picked near the middle (one per half in a gate room). From
   each opening, porch and tunnel mouth a drunkard's walk with a 3x3 brush
   heads for its hub. Two to four ellipses are carved along the way. Boss
   rooms carve one large ellipse instead, at least 16 cells wide and 10 high.
4. Platforms: one-cell-thick ledges three to six cells long are added in open
   air where there are three empty cells above and two below.
5. Border: every border cell is solid except opening cells. The final room
   gets a three-cell hole in row 23.
6. Slopes: an unprotected solid cell with empty cells above and to one side,
   and solid below and on the other side, becomes a slope with probability
   0.35.

Monsters:

- Costs: JumpBot 1, Flyer 1, SpikyBallMonster 2, DefenseTurretVertical 2,
  FlyBot 3, AimerTurret 3, HandBot 4, BossBot1 6, BossBot2 7, BossBot3 9.
- Budget: `8 + 14 * rank`, jittered by up to 3 either way; rooms behind the
  gate add 6. Monsters are drawn at random from those that fit the remaining
  budget. Elites need rank >= 0.6, at most one per room.
- Ground monsters go on standable cells (HandBot needs a 2x2 space), flyers
  and fly bots in air cells with air all round, aimer turrets and Flyers in an
  air cell under a ceiling. Nothing hostile is placed within 5 cells of an
  entry cell or the player start, inside a vault, or in a gadget tunnel.
- Normal rooms also get zero to four HoverBlocks in open air (a 5x5 empty
  neighbourhood). Vault and boss rooms get none.
- `start`: a SavePoint, a player start, no hostiles.
- `infested`: 25 to 40 BallMonsters on standable and air cells, plus hostiles
  worth a quarter of the usual budget.
- `boss`: the boss in the middle of the large cave, plus hostiles worth half
  the usual budget, and the artifact in the vault.
- Fuel powerups stand on the highest standable cell at least 8 cells from
  every entry.
- Save points stand on a standable cell near the hub.

`check` reports:

- an opening from which another opening cannot be left;
- a treasure or save point the player cannot reach from every entry, or
  cannot leave from;
- a vault whose treasure is reachable while the door cells are solid;
- a gate room whose far openings are reachable while the door cells are solid;
- a hostile within 5 cells of an entry cell;
- a room where fewer than 120 cells are empty.

- [ ] **Step 1: Write the failing tests**

```python
from planet_gen import room as roomgen


class RoomTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world = worldmap.build(random.Random(2026))
        cls.rooms = {at: roomgen.build(cls.world, at, 2026 * 1000 + at[0] * 10 + at[1]) for at in cls.world.links}

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

    def test_the_gate_holds_the_artifact_door(self):
        names = [m[0] for m in self.rooms[self.world.gate].monsters]
        self.assertEqual(names.count("ArtifactDoor"), 1)

    def test_only_known_monsters_are_used(self):
        scenes = Path(__file__).resolve().parent.parent / "entities" / "monsters"
        for built in self.rooms.values():
            for name, x, y in built.monsters:
                snake = "".join("_" + c.lower() if c.isupper() or c.isdigit() else c for c in name).lstrip("_")
                self.assertTrue((scenes / (snake + ".tscn")).exists(), name)
                self.assertTrue(0 < x < 960 and 0 < y < 768, (name, x, y))
```

- [ ] **Step 2: Run to see them fail**
- [ ] **Step 3: Implement `room.py`**, carving in the order above. Print a few rooms as text while developing to judge the shapes.
- [ ] **Step 4: Run the tests, expect all to pass**
- [ ] **Step 5: Commit** `git add tools/planet_gen/room.py tools/test_generate_planet.py && git commit -m "Carve Korvax rooms and place vaults, the gate and monsters"`

---

### Task 4: Walls, tiles and the JSON file

**Files:**
- Create: `tools/planet_gen/render.py`, `tools/generate_planet.py`, `tools/korvax.json` (generated)
- Test: `tools/test_generate_planet.py`

Interface:

```python
# render.py
def walls(rows, open_floor=None) -> list[[x1, y1, x2, y2]]
def tiles(rows, sheet_index) -> list[[cx, cy, sheet, tx, ty]]
def background(sheet_index) -> list[[cx, cy, sheet, 2, 2]]   # 720 cells

# generate_planet.py
SEED = 2026
def generate(seed=SEED) -> dict
def main()   # writes tools/korvax.json
```

- `walls`: unit edges between a solid and an empty cell inside the grid,
  merged into the longest straight runs; a slope cell contributes one diagonal
  in place of its exposed top and side; four border segments, the bottom one
  split around `open_floor` (the final room's hole columns).
- `tiles`: the table under "Facts" above, with cells outside the grid counted
  as solid.
- `generate` copies `sheets` and `player` from `tools/zorta.json`, so tile
  source ids match the shared tile set, sets `start_room` to `[2, 0]`, and
  writes rooms sorted by (x, y), each with `x`, `y`, `music`, `player_start`,
  `layers` (`background`, `midground`, empty `foreground`), empty `animated`,
  `walls`, `monsters`, `tint`, `cells`, `links`, `kind`.
- `main` writes with `json.dump(world, file, separators=(",", ":"))`.

- [ ] **Step 1: Write the failing tests**

```python
import json
from planet_gen import render
import generate_planet

TOOLS = Path(__file__).resolve().parent


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

    def test_a_slope_is_one_diagonal(self):
        rows = ["#" * 30] + ["#" + "." * 28 + "#"] * 21 + ["#" + "." * 10 + "/" + "#" * 18] + ["#" * 30]
        got = [tuple(w) for w in render.walls(rows)]
        self.assertIn((352, 736, 384, 704), got)

    def test_edge_tiles(self):
        rows = ["#" * 30] + ["#" + "." * 28 + "#"] * 22 + ["#" * 30]
        got = {(t[0], t[1]): (t[3], t[4]) for t in render.tiles(rows, 7)}
        self.assertEqual(got[(5, 0)], (2, 3))    # ceiling: empty below
        self.assertEqual(got[(5, 23)], (2, 1))   # floor: empty above
        self.assertEqual(got[(0, 5)], (3, 2))    # left wall: empty to the right
        self.assertEqual(got[(29, 5)], (1, 2))


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
        self.assertTrue(set(self.zorta["rooms"][0]) <= set(self.world["rooms"][0]))

    def test_tiles_exist_and_are_not_blank(self):
        used = set()
        for r in self.rooms.values():
            self.assertEqual(len(r["layers"]["background"]), 720)
            for layer in r["layers"].values():
                for t in layer:
                    used.add((self.world["sheets"][t[2]], t[3], t[4]))
        for sheet, tx, ty in used:
            self.assertFalse(generate_planet.tile_is_blank(sheet, tx, ty), (sheet, tx, ty))

    def test_every_room_has_a_tint_and_music(self):
        sounds = TOOLS.parent / "assets" / "sounds"
        for r in self.rooms.values():
            self.assertEqual(len(r["tint"]), 3)
            self.assertTrue((sounds / (r["music"] + ".ogg")).exists())

    def test_one_room_has_an_open_floor(self):
        finals = [r for r in self.rooms.values() if r["kind"] == "final"]
        self.assertEqual(len(finals), 1)
        self.assertEqual(finals[0]["y"], 9)
        self.assertIn(".", finals[0]["cells"][23])
```

`tile_is_blank` reads the PNG with the standard library (`zlib` and the
`struct` module, as `make_monster_scenes.py` reads PNG headers) and reports
whether a 16x16 tile is fully transparent. If a sheet lacks a slope tile, the
generator leaves slopes out of rooms in that zone.

- [ ] **Step 2: Run to see them fail**
- [ ] **Step 3: Implement `render.py` and `generate_planet.py`**
- [ ] **Step 4: Generate the file** — `python tools/generate_planet.py`, expect `wrote tools/korvax.json: 100 rooms`.
- [ ] **Step 5: Run every Python test, expect all to pass**
- [ ] **Step 6: Commit** `git add tools/planet_gen/render.py tools/generate_planet.py tools/korvax.json tools/test_generate_planet.py && git commit -m "Render Korvax rooms to walls and tiles and write korvax.json"`

---

### Task 5: Planet registry, importer and smoke test

**Files:**
- Create: `world/planets.gd`
- Modify: `tools/import_world.gd`, `tools/smoke_test.gd`
- Generated: `world/rooms_korvax/room_X_Y.tscn`

- [ ] **Step 1: Create `world/planets.gd`**

```gdscript
extends RefCounted
## The campaign planets: where each one's rooms and saves live.

const Progress := preload("res://save/progress.gd")

const ZORTA := "zorta"
const KORVAX := "korvax"
## Order shown on the title screen.
const ORDER := [ZORTA, KORVAX]

const DATA := {
	ZORTA: {
		"name": "Planet Zorta",
		"label": "classic",
		"rooms_dir": "res://world/rooms",
		"world_json": "res://tools/zorta.json",
		"save_prefix": "save_",
		"start_room": Vector2i(4, 2),
	},
	KORVAX: {
		"name": "Planet Korvax",
		"label": "new - 2026",
		"rooms_dir": "res://world/rooms_korvax",
		"world_json": "res://tools/korvax.json",
		"save_prefix": "save_korvax_",
		"start_room": Vector2i(2, 0),
	},
}


static func exists(planet: String) -> bool:
	return DATA.has(planet)


## The name as the title screen shows it, such as "Planet Zorta (classic)".
static func title(planet: String) -> String:
	return "%s (%s)" % [DATA[planet].name, DATA[planet].label]


static func room_path(planet: String, at: Vector2i) -> String:
	return "%s/room_%d_%d.tscn" % [DATA[planet].rooms_dir, at.x, at.y]


## A new game's progress on a planet.
static func new_progress(planet: String) -> RefCounted:
	var progress := Progress.new()
	progress.checkpoint = DATA[planet].start_room
	return progress
```

- [ ] **Step 2: Extend the smoke test first.** In `tools/smoke_test.gd`, replace `WORLD_JSON` with a loop over `Planets.ORDER`, load rooms through `Planets.room_path`, and add to `_check_room`:

```gdscript
	var tint := Color.WHITE
	if data.has("tint"):
		tint = Color(data.tint[0], data.tint[1], data.tint[2])
	for layer_name in LAYERS:
		_expect(room.get_node(layer_name.capitalize()).modulate.is_equal_approx(tint), "%s %s tint" % [path, layer_name])
		_expect(room.get_node(layer_name.capitalize() + "Animated").modulate.is_equal_approx(tint), "%s %s animated tint" % [path, layer_name])
```

and after the rooms of each planet:

```gdscript
		var start := Vector2i(int(world.start_room[0]), int(world.start_room[1]))
		_expect(Planets.DATA[planet].start_room == start, "%s start room is %s" % [planet, start])
```

- [ ] **Step 3: Run it, expect failures** for every missing `rooms_korvax` scene.

- [ ] **Step 4: Make the importer build every planet.** In `tools/import_world.gd`, `_run` builds the tile set from the first planet's sheets, then for each planet reads its JSON, fails if its `sheets` differ, and saves to `Planets.room_path(planet, at)` after `DirAccess.make_dir_recursive_absolute(rooms_dir)`. In `_build_room`, after the layer and its animated holder are created:

```gdscript
		if data.has("tint"):
			var tint := Color(data.tint[0], data.tint[1], data.tint[2])
			layer.modulate = tint
			animated.modulate = tint
```

- [ ] **Step 5: Import** — `"$GODOT" --headless --path . --script res://tools/import_world.gd`. Expect `imported 100 rooms` twice. Check `git status world/rooms` shows no change to Zorta's rooms.
- [ ] **Step 6: Run the smoke test, expect** `smoke test passed: 200 rooms`.
- [ ] **Step 7: Commit** `world/planets.gd`, its uid, `tools/import_world.gd`, `tools/smoke_test.gd`, `world/rooms_korvax`.

---

### Task 6: Saves and progress per planet

**Files:**
- Modify: `save/save_game.gd`, `save/progress.gd`, `tools/test_save.gd`

- [ ] **Step 1: Update `tools/test_save.gd`.** A fresh `Progress.new()` no longer knows a start room, so replace the first assertion with:

```gdscript
	_expect(Planets.new_progress("zorta").checkpoint == Vector2i(4, 2), "a new Zorta game starts in room 4,2")
	_expect(Planets.new_progress("korvax").checkpoint == Vector2i(2, 0), "a new Korvax game starts in room 2,0")
```

Give every `SaveGame` call in `_test_save_files` a first argument `"zorta"`, and add:

```gdscript
	_expect(SaveGame.path("zorta", 1).ends_with("save_1.json"), "Zorta keeps the original file names")
	_expect(SaveGame.path("korvax", 1).ends_with("save_korvax_1.json"), "Korvax has its own files")
	SaveGame.write("korvax", 1, Planets.new_progress("korvax"))
	_expect(SaveGame.exists("korvax", 1) and not SaveGame.exists("zorta", 1), "planets do not share slots")
	SaveGame.delete("korvax", 1)
```

- [ ] **Step 2: Run, expect a parse error** (too many arguments).
- [ ] **Step 3: Implement.** In `save/save_game.gd` every function takes `planet: String` first, and:

```gdscript
static func path(planet: String, slot: int) -> String:
	return "%s%s%d.json" % [directory, Planets.DATA[planet].save_prefix, slot]
```

with `const Planets := preload("res://world/planets.gd")`. `planets.gd` preloads `progress.gd` and `save_game.gd` preloads both, so there is no cycle. In `save/progress.gd` remove `START_ROOM` and declare `var checkpoint := Vector2i.ZERO`.

- [ ] **Step 4: Run `test_save.gd`, expect** `save test passed`.
- [ ] **Step 5: Commit** (the campaign, main and title do not compile until Task 7; commit Tasks 6 and 7 together if a broken commit is unwanted).

---

### Task 7: Campaign and screen flow per planet

**Files:**
- Modify: `scenes/campaign.gd`, `scenes/main.gd`, `scenes/title.gd` (signal arguments only), `tools/test_campaign.gd`, `tools/test_main.gd`

- [ ] **Step 1: Add to `tools/test_campaign.gd`** a check run after `_check_win`:

```gdscript
## Korvax starts in its own start room, on the ground, and leads somewhere.
func _check_korvax() -> void:
	var campaign: Node2D = load("res://scenes/campaign.tscn").instantiate()
	campaign.planet = "korvax"
	root.add_child(campaign)
	var player: RigidBody2D = campaign.get_node("Player")
	await _frames(120)
	_expect(campaign.grid == Vector2i(2, 0), "Korvax starts in room 2,0, grid %s" % campaign.grid)
	_expect(campaign.room.scene_file_path.contains("rooms_korvax"), "Korvax loads its own rooms")
	_expect(player.linear_velocity.length() < 5.0, "the player rests in the Korvax start room")
	_expect(player.hp == player.max_hp, "the Korvax start room is safe, hp %d" % player.hp)
	var world = JSON.parse_string(FileAccess.get_file_as_string("res://tools/korvax.json"))
	for data in world.rooms:
		if int(data.x) == 2 and int(data.y) == 0:
			_expect(data.links.size() > 0, "the start room has a way out")
	root.remove_child(campaign)
	campaign.free()
```

and give the existing `SaveGame` calls the `"zorta"` argument, and replace `Progress.new()` with `Planets.new_progress("zorta")`.

- [ ] **Step 2: Update `tools/test_main.gd`**: `SaveGame` calls take `"zorta"`; delete both planets' slots at the start and end; after the Chaosnaut check add:

```gdscript
	# The planet switch shows the other planet's slots and starts its campaign.
	SaveGame.write("zorta", 3, Planets.new_progress("zorta"))
	_main.show_title()
	await _settle()
	_expect(_button("Slot3Continue") != null, "Zorta's slot 3 is in use")
	_button("PlanetNext").pressed.emit()
	await _settle()
	_expect(_main.screen.planet == "korvax", "the switch moves to Korvax")
	_expect(_main.screen.find_child("PlanetLabel", true, false).text == "Planet Korvax (new - 2026)", "the label names the planet")
	_expect(_button("Slot3New") != null, "Korvax's slot 3 is empty")
	_button("Slot3New").pressed.emit()
	await _settle()
	_expect(SaveGame.exists("korvax", 3), "a Korvax new game writes a Korvax slot")
	_press_key(KEY_SPACE)
	await _settle()
	_expect(_is(CampaignScript) and _main.screen.planet == "korvax", "the Korvax campaign starts")
	if _is(CampaignScript):
		_expect(_main.screen.grid == Vector2i(2, 0), "Korvax starts in room 2,0")
		_main.screen.quit_to_title.emit()
	await _settle()
	_expect(_main.screen.planet == "korvax", "the title remembers the last planet")
	_button("PlanetPrev").pressed.emit()
	await _settle()
	_expect(_main.screen.planet == "zorta", "the switch moves back to Zorta")
```

The title parts of this pass after Task 8.

- [ ] **Step 3: Implement.**

`scenes/campaign.gd`:

```gdscript
const Planets := preload("res://world/planets.gd")

## Which planet's rooms and saves to use. Set before adding to the tree.
var planet := Planets.ZORTA
```

In `_ready`, `progress = Planets.new_progress(planet)`. In `load_room`, `load(Planets.room_path(planet, at))`. In `_write_slot`, `SaveGame.write(planet, slot, progress)`.

`scenes/main.gd`: read `--planet=ID` (ignored unless `Planets.exists`), which also skips the title; then

```gdscript
func _on_new_game(planet: String, slot: int) -> void:
	SaveGame.write(planet, slot, Planets.new_progress(planet))
	_show_image(IntroImage, _start_campaign.bind(planet, slot))
	get_tree().call_group("audio", "play", "intro")


## slot 0 plays without saving.
func _start_campaign(planet: String, slot: int) -> void:
	var campaign := CampaignScene.instantiate()
	campaign.planet = planet
	campaign.slot = slot
	if slot > 0:
		campaign.progress = SaveGame.read(planet, slot)
	...
```

Add `--planet=ID` to the header comment.

- [ ] **Step 4: Run `test_campaign.gd`, expect** `campaign test passed`.
- [ ] **Step 5: Commit** together with Task 6 if it was held back.

---

### Task 8: Title screen planet switch

**Files:**
- Create: `save/settings.gd`
- Modify: `scenes/title.gd`

- [ ] **Step 1: Create `save/settings.gd`**

```gdscript
extends RefCounted
## Small choices remembered between runs. Lives beside the save slots.

const SaveGame := preload("res://save/save_game.gd")
const Planets := preload("res://world/planets.gd")


static func path() -> String:
	return SaveGame.directory + "settings.json"


## The planet last chosen on the title, or Zorta.
static func last_planet() -> String:
	if not FileAccess.file_exists(path()):
		return Planets.ZORTA
	var data = JSON.parse_string(FileAccess.get_file_as_string(path()))
	if data is Dictionary and data.get("planet") is String and Planets.exists(data.planet):
		return data.planet
	return Planets.ZORTA


static func set_last_planet(planet: String) -> void:
	var file := FileAccess.open(path(), FileAccess.WRITE)
	if file != null:
		file.store_string(JSON.stringify({"planet": planet}))
```

- [ ] **Step 2: Change `scenes/title.gd`.**

```gdscript
signal new_game(planet: String, slot: int)
signal continue_game(planet: String, slot: int)

const PLANET_Y := 344.0
const ARROW_BUTTON := Vector2(34, 20)
const PLANET_LABEL_WIDTH := 300.0

## The planet whose save slots are shown.
var planet := Planets.ZORTA
var _planet_label: Label
```

In `_ready`, before `_build_slots()`:

```gdscript
	planet = Settings.last_planet()
	var half := PLANET_LABEL_WIDTH / 2.0
	var prev := _add_planet_button("PlanetPrev", "<", CENTER_X - half - ARROW_BUTTON.x, -1)
	var next := _add_planet_button("PlanetNext", ">", CENTER_X + half, 1)
	_planet_label = UiKit.make_label("")
	_planet_label.name = "PlanetLabel"
	_planet_label.position = Vector2(CENTER_X - half, PLANET_Y)
	_planet_label.size = Vector2(PLANET_LABEL_WIDTH, ARROW_BUTTON.y)
	_planet_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_planet_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	add_child(_planet_label)
```

```gdscript
func _add_planet_button(node_name: String, text: String, x: float, step: int) -> Button:
	var button := UiKit.make_button(text, ARROW_BUTTON)
	button.name = node_name
	button.position = Vector2(x, PLANET_Y)
	button.pressed.connect(_step_planet.bind(step))
	add_child(button)
	return button


func _step_planet(step: int) -> void:
	var index := Planets.ORDER.find(planet)
	planet = Planets.ORDER[posmod(index + step, Planets.ORDER.size())]
	Settings.set_last_planet(planet)
	_build_slots()
```

`_build_slots` sets `_planet_label.text = Planets.title(planet)`, passes `planet` to every `SaveGame` call and signal, and labels an empty slot `"New Game %d" % slot`. `_delete_slot` passes `planet`.

- [ ] **Step 3: Run `test_main.gd`, expect** `main test passed`.
- [ ] **Step 4: Run every suite** (`test_save`, `test_campaign`, `test_main`, `test_monsters`, `test_chaosnaut`, `test_effects`, `test_jetpack`, `smoke_test`, and the Python tests).
- [ ] **Step 5: Commit.**

---

### Task 9: Look at it and tune

- [ ] **Step 1:** Screenshot the title and one room from each zone:

```bash
"$GODOT" --path . -- --shot=C:/Users/mattf/AppData/Local/Temp/korvax_title.png
"$GODOT" --path . -- --planet=korvax --room=2,0 --shot=C:/Users/mattf/AppData/Local/Temp/korvax_2_0.png
```

- [ ] **Step 2:** Adjust zone tints in `worldmap.ZONES`, cave sizes and monster budgets where a screenshot shows a room that is ugly, cramped or empty. Regenerate, re-import, re-run the Python tests and the smoke test.
- [ ] **Step 3:** Commit the tuned generator, `korvax.json` and rooms.
