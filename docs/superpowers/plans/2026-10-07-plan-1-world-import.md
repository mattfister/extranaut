# Extranaut Port, Plan 1: Project Foundation and World Import

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the original `zorta.xn0` world pickle into 100 Godot room scenes that can be browsed in a viewer, on top of a configured project with all assets in place.

**Architecture:** A Python 3 script unpickles the Python 2 world with stub classes and writes JSON. A headless Godot script reads that JSON, builds one shared `TileSet`, and saves one `.tscn` per room containing tile layers, animated tiles, wall collision and monster spawn markers. A headless smoke test checks every generated room against the JSON, and a small viewer scene shows rooms on screen.

**Tech Stack:** Godot 4.7 (GDScript, Compatibility renderer), Python 3 standard library (`pickle`, `json`, `unittest`).

**Spec:** `docs/superpowers/specs/2026-10-07-extranaut-godot-port-design.md`

**This is plan 1 of 7.** The spec's build order maps to one plan each: (1) importer and room scenes, (2) player, walls and room transitions, (3) monsters and projectiles, (4) saves, HUD, map and menus, (5) Chaosnaut, (6) juice, (7) web export. Each later plan is written when the one before it is done.

---

## Conventions for every task

- Shell is Git Bash. Run commands from the repository root, `C:/Users/mattf/Documents/Godot/extranaut`.
- Godot binary:

```bash
GODOT="/c/Users/mattf/Desktop/godot47/Godot_v4.7-stable_win64_console.exe"
```

- GDScript files are indented with tabs.
- Commit messages end with this trailer:

```
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

## Facts about the source data

These were measured from `ExtranautPython/data/zorta.xn0` and are used as test expectations.

- 10x10 rooms, indexed `rooms[x][y]`. A room is 30x24 tiles of 32 px (960x768).
- 81,027 tiles in total, all 32x32 and grid-aligned, from 11 sheets. 12 of them lie outside the room bounds and are dropped, leaving 81,015.
- Tile sheets are 128x128 PNGs of 16 px tiles (8x8 cells). The game scales art 2x on load, so the rects in the pickle are in 2x pixels: atlas cell = rect / 32.
- 130 animated tiles, each 4 frames, on sheets `animations` and `ruinsAnimated` (64x64 PNGs, 16 px frames, one animation per row).
- 4,665 wall segments with endpoints on the 32 px grid.
- 428 monster spawns across 25 class names. Room (4, 2) has exactly one: `SavePoint` at (272, 432).
- Room (4, 2) is the start room, has music `zortaSurface` and `playerTestPosition` (480, 352). Only 31 rooms have a `playerTestPosition`.

## File structure

| Path | Responsibility |
| --- | --- |
| `.gitignore`, `project.godot` | Repository and project settings |
| `ExtranautPython/.gdignore` | Stops Godot importing the reference source |
| `assets/sprites`, `assets/animations`, `assets/sounds`, `assets/fonts` | Game assets copied from the original |
| `tools/extract_world.py` | Pickle to JSON |
| `tools/test_extract_world.py` | Unit tests for the extractor |
| `tools/zorta.json` | Extracted world (generated, committed) |
| `world/room.gd` | Room root script: grid position, music, player start |
| `world/animated_tile.gd` | Frame cycling for animated tiles |
| `world/monster_spawn.gd` | Placeholder marker for a monster whose scene does not exist yet |
| `tools/import_world.gd` | JSON to `world/tileset.tres` and `world/rooms/room_X_Y.tscn` |
| `tools/smoke_test.gd` | Loads every room and checks it against the JSON |
| `scenes/room_viewer.tscn`, `scenes/room_viewer.gd` | Temporary viewer, replaced by the real game in plan 2 |

---

### Task 1: Repository and project settings

**Files:**
- Modify: `.gitignore`
- Modify: `project.godot`
- Create: `ExtranautPython/.gdignore`
- Delete: `ExtranautPython/**/*.import` (stale files Godot generated before the folder was ignored)

- [ ] **Step 1: Replace `.gitignore`**

```gitignore
# Godot 4+ specific ignores
.godot/
/android/

# Builds
/build/
/ExtranautPython/dist/

# Python
__pycache__/
```

- [ ] **Step 2: Ignore the reference source in Godot and remove stale import files**

```bash
touch ExtranautPython/.gdignore
find ExtranautPython -name '*.import' -delete
find ExtranautPython -name '*.import' | wc -l
```

Expected: `0`

- [ ] **Step 3: Replace `project.godot`**

```ini
; Engine configuration file.
; It's best edited using the editor UI and not directly,
; since the parameters that go here are not all obvious.
;
; Format:
;   [section] ; section goes between []
;   param=value ; assign values to parameters

config_version=5

[application]

config/name="Extranaut"
config/features=PackedStringArray("4.7", "GL Compatibility")
config/icon="res://icon.svg"

[display]

window/size/viewport_width=1024
window/size/viewport_height=768
window/stretch/mode="canvas_items"
window/stretch/aspect="keep"

[physics]

2d/default_gravity=900.0
3d/physics_engine="Jolt Physics"

[rendering]

textures/canvas_textures/default_texture_filter=0
rendering_device/driver.windows="d3d12"
renderer/rendering_method="gl_compatibility"
renderer/rendering_method.mobile="gl_compatibility"
```

- [ ] **Step 4: Verify the project still opens**

```bash
"$GODOT" --headless --path . --import; echo "exit=$?"
```

Expected: `exit=0`, and no errors mentioning `project.godot`.

- [ ] **Step 5: Commit the settings and the original source**

```bash
git add .gitignore .gitattributes .editorconfig project.godot icon.svg icon.svg.import ExtranautPython
git status --short | grep -c "ExtranautPython/dist" 
git commit -m "Configure project and add original Python source for reference

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

Expected: the `grep -c` prints `0` (nothing from `dist/` is staged), then the commit succeeds.

---

### Task 2: Copy assets

**Files:**
- Create: `assets/sprites/*.png` (29 files), `assets/animations/*.png` (26 files), `assets/sounds/*.ogg` (24 files), `assets/fonts/*`

- [ ] **Step 1: Copy the files**

```bash
mkdir -p assets/sprites assets/animations assets/sounds assets/fonts
cp ExtranautPython/graphics/sprites/*.png assets/sprites/
cp ExtranautPython/graphics/animations/*.png assets/animations/
cp ExtranautPython/sounds/*.ogg assets/sounds/
cp ExtranautPython/graphics/fonts/* assets/fonts/
ls assets/sprites/*.png | wc -l; ls assets/animations/*.png | wc -l; ls assets/sounds/*.ogg | wc -l; ls assets/fonts
```

Expected: `29`, `26`, `24`, then a listing that includes `KARNIVOR.ttf` and the font's licence text file.

- [ ] **Step 2: Import them**

```bash
"$GODOT" --headless --path . --import; echo "exit=$?"
ls assets/sprites/*.import | wc -l
```

Expected: `exit=0` and `29`.

- [ ] **Step 3: Commit**

```bash
git add assets
git commit -m "Add art, sound and font assets

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: World extractor

**Files:**
- Create: `tools/extract_world.py`
- Create: `tools/test_extract_world.py`
- Create: `tools/zorta.json` (generated)

Output format of `tools/zorta.json`:

```json
{
  "start_room": [4, 2],
  "player": {"max_hp": 5, "max_fuel": 2000, "gun_level": 1, "artifacts": 0},
  "sheets": ["bgRocks", "..."],
  "rooms": [
    {
      "x": 0, "y": 0,
      "music": "zortaSurface",
      "player_start": [480, 352],
      "layers": {
        "background": [[tx, ty, sheet_index, atlas_x, atlas_y]],
        "midground": [],
        "foreground": []
      },
      "animated": [{"layer": "background", "sheet": "animations", "row": 3, "pos": [64, 128]}],
      "walls": [[x1, y1, x2, y2]],
      "monsters": [["SavePoint", 272, 432]]
    }
  ]
}
```

`music` and `player_start` are `null` when the room has none. `tx`/`ty` are tile coordinates (0 to 29, 0 to 23). `atlas_x`/`atlas_y` are cells in the 16 px source sheet. `pos`, walls and monster positions are in room pixels.

- [ ] **Step 1: Write the failing tests**

Create `tools/test_extract_world.py`:

```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
python -m unittest discover -s tools -p "test_*.py"
```

Expected: an error, `ModuleNotFoundError: No module named 'extract_world'`.

- [ ] **Step 3: Write the extractor**

Create `tools/extract_world.py`:

```python
"""Convert the original Extranaut world pickle to JSON for the Godot importer.

The pickle was written by Python 2 and references the game's own classes and
pygame. Stub classes stand in for all of them, so nothing but the standard
library is needed.

Usage: python tools/extract_world.py
"""
import json
import pickle
from pathlib import Path

TILE = 32
ROOM_TILES_X = 30
ROOM_TILES_Y = 24
LAYERS = ("background", "midground", "foreground")

ROOT = Path(__file__).resolve().parent.parent
PICKLE_PATH = ROOT / "ExtranautPython" / "data" / "zorta.xn0"
JSON_PATH = ROOT / "tools" / "zorta.json"


class _Stub:
    def __init__(self, *args, **kwargs):
        pass

    def __setstate__(self, state):
        self.__dict__.update(state)


class _Unpickler(pickle.Unpickler):
    def __init__(self, file):
        super().__init__(file, encoding="latin1")
        self._classes = {}

    def find_class(self, module, name):
        key = (module, name)
        if key not in self._classes:
            self._classes[key] = type(name, (_Stub,), {})
        return self._classes[key]


def load_planet(path):
    with open(path, "rb") as file:
        return _Unpickler(file).load()


def _sheet_names(planet):
    names = set()
    for column in planet.rooms:
        for room in column:
            for layer in LAYERS:
                for tile in getattr(room, layer + "Tiles"):
                    names.add(tile.sheetSprite.spriteSheetName)
    return sorted(names)


def _convert_layer(tiles, sheet_index):
    converted = []
    for tile in tiles:
        tx = tile.pos[0] // TILE
        ty = tile.pos[1] // TILE
        if not (0 <= tx < ROOM_TILES_X and 0 <= ty < ROOM_TILES_Y):
            continue
        rect = tile.sheetSprite.rect
        converted.append(
            [tx, ty, sheet_index[tile.sheetSprite.spriteSheetName], rect[0] // TILE, rect[1] // TILE]
        )
    return converted


def _convert_room(room, x, y, sheet_index):
    animated = []
    for layer in LAYERS:
        for tile in getattr(room, "animated" + layer.capitalize() + "Tiles"):
            animated.append(
                {
                    "layer": layer,
                    "sheet": tile.animationSprite.animationSheetName,
                    "row": tile.animationSprite.row,
                    "pos": [int(tile.pos[0]), int(tile.pos[1])],
                }
            )
    start = room.playerTestPosition
    return {
        "x": x,
        "y": y,
        "music": room.music,
        "player_start": None if start is None else [int(start[0]), int(start[1])],
        "layers": {
            layer: _convert_layer(getattr(room, layer + "Tiles"), sheet_index) for layer in LAYERS
        },
        "animated": animated,
        "walls": [
            [int(a[0]), int(a[1]), int(b[0]), int(b[1])] for a, b in room.uninitializedWallSegments
        ],
        "monsters": [
            [cls.__name__, int(pos[0]), int(pos[1])] for cls, pos in room.uninitializedMonsters
        ],
    }


def convert(planet):
    sheets = _sheet_names(planet)
    sheet_index = {name: i for i, name in enumerate(sheets)}
    rooms = []
    for x, column in enumerate(planet.rooms):
        for y, room in enumerate(column):
            rooms.append(_convert_room(room, x, y, sheet_index))
    return {
        "start_room": list(planet.playerCheckPointRoom),
        "player": {
            "max_hp": planet.playerMaxHp,
            "max_fuel": planet.playerMaxJetpackFuel,
            "gun_level": planet.playerGunLevel,
            "artifacts": planet.playerArtifactsGathered,
        },
        "sheets": sheets,
        "rooms": rooms,
    }


def main():
    world = convert(load_planet(PICKLE_PATH))
    with open(JSON_PATH, "w", newline="\n") as file:
        json.dump(world, file, separators=(",", ":"))
    print("Wrote %s (%d rooms)" % (JSON_PATH, len(world["rooms"])))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
python -m unittest discover -s tools -p "test_*.py"
```

Expected: `Ran 9 tests` and `OK`.

- [ ] **Step 5: Generate the JSON**

```bash
python tools/extract_world.py && ls -la tools/zorta.json
```

Expected: `Wrote ...zorta.json (100 rooms)` and a file of roughly 1 to 2 MB.

- [ ] **Step 6: Commit**

```bash
git add tools/extract_world.py tools/test_extract_world.py tools/zorta.json
git commit -m "Extract the Zorta world pickle to JSON

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Room support scripts

**Files:**
- Create: `world/room.gd`
- Create: `world/animated_tile.gd`
- Create: `world/monster_spawn.gd`

These are attached to nodes by the importer in Task 5.

- [ ] **Step 1: Create `world/room.gd`**

```gdscript
class_name Room
extends Node2D
## Root of a generated room scene. See tools/import_world.gd.

const SIZE := Vector2(960, 768)

@export var grid_pos := Vector2i.ZERO
## Track name in assets/sounds, or empty to keep whatever is playing.
@export var music := ""
@export var has_player_start := false
@export var player_start := Vector2.ZERO
```

- [ ] **Step 2: Create `world/animated_tile.gd`**

```gdscript
class_name AnimatedTile
extends Sprite2D
## Cycles through the frames of one row of an animation sheet.

const FRAME_TIME := 0.09

var _elapsed := 0.0


func _process(delta: float) -> void:
	_elapsed += delta
	if _elapsed >= FRAME_TIME:
		_elapsed -= FRAME_TIME
		frame_coords.x = (frame_coords.x + 1) % hframes
```

- [ ] **Step 3: Create `world/monster_spawn.gd`**

```gdscript
class_name MonsterSpawn
extends Marker2D
## Stands in for a monster whose scene does not exist yet. The importer
## replaces these with real instances once entities/monsters/<kind>.tscn exists.

@export var kind := ""
```

- [ ] **Step 4: Check the scripts parse**

```bash
"$GODOT" --headless --path . --import 2>&1 | grep -i -E "error|parse" ; echo "grep_exit=$?"
```

Expected: no matching lines and `grep_exit=1`.

- [ ] **Step 5: Commit**

```bash
git add world
git commit -m "Add room, animated tile and monster spawn scripts

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: World importer and smoke test

**Files:**
- Create: `tools/smoke_test.gd`
- Create: `tools/import_world.gd`
- Create: `world/tileset.tres` (generated)
- Create: `world/rooms/room_X_Y.tscn` for X, Y in 0 to 9 (generated)

Generated room scene tree, in draw order:

```
Room_X_Y (Node2D, room.gd)
  Background (TileMapLayer, scale 2)
  BackgroundAnimated (Node2D)   AnimatedTile sprites
  Midground (TileMapLayer, scale 2)
  MidgroundAnimated (Node2D)
  Entities (Node2D)             monster instances or MonsterSpawn markers
  Foreground (TileMapLayer, scale 2)
  ForegroundAnimated (Node2D)
  Walls (StaticBody2D)          one CollisionShape2D with a SegmentShape2D per wall
```

The tile set uses 16 px tiles and the layers are scaled 2x, which reproduces the original's 2x art scaling without resampling the sheets.

- [ ] **Step 1: Write the smoke test**

Create `tools/smoke_test.gd`:

```gdscript
extends SceneTree
## Loads every generated room and checks it against tools/zorta.json.
## Run: godot --headless --path . --script res://tools/smoke_test.gd

const WORLD_JSON := "res://tools/zorta.json"
const LAYERS := ["background", "midground", "foreground"]

var _failures := 0


func _initialize() -> void:
	_run()


func _run() -> void:
	var world = JSON.parse_string(FileAccess.get_file_as_string(WORLD_JSON))
	if world == null:
		_fail("could not read %s" % WORLD_JSON)
		quit(1)
		return
	for data in world.rooms:
		await _check_room(data)
	if _failures == 0:
		print("smoke test passed: %d rooms" % world.rooms.size())
	else:
		print("smoke test FAILED: %d failures" % _failures)
	quit(1 if _failures > 0 else 0)


func _check_room(data: Dictionary) -> void:
	var x := int(data.x)
	var y := int(data.y)
	var path := "res://world/rooms/room_%d_%d.tscn" % [x, y]
	if not ResourceLoader.exists(path):
		_fail("%s is missing" % path)
		return
	var room: Node2D = load(path).instantiate()
	root.add_child(room)
	await physics_frame
	await physics_frame

	_expect(room.grid_pos == Vector2i(x, y), "%s grid_pos is %s" % [path, room.grid_pos])
	var music: String = "" if data.music == null else data.music
	_expect(room.music == music, "%s music is '%s'" % [path, room.music])
	_expect(room.has_player_start == (data.player_start != null), "%s has_player_start" % path)

	var animated_by_layer := {}
	for a in data.animated:
		animated_by_layer[a.layer] = animated_by_layer.get(a.layer, 0) + 1
	for layer_name in LAYERS:
		var layer: TileMapLayer = room.get_node(layer_name.capitalize())
		_expect(
			layer.get_used_cells().size() == data.layers[layer_name].size(),
			"%s %s has %d cells" % [path, layer_name, layer.get_used_cells().size()]
		)
		var animated := room.get_node(layer_name.capitalize() + "Animated")
		_expect(
			animated.get_child_count() == animated_by_layer.get(layer_name, 0),
			"%s %s animated count is %d" % [path, layer_name, animated.get_child_count()]
		)
	_expect(
		room.get_node("Walls").get_child_count() == data.walls.size(),
		"%s wall count is %d" % [path, room.get_node("Walls").get_child_count()]
	)
	_expect(
		room.get_node("Entities").get_child_count() == data.monsters.size(),
		"%s entity count is %d" % [path, room.get_node("Entities").get_child_count()]
	)

	root.remove_child(room)
	room.free()


func _expect(condition: bool, message: String) -> void:
	if not condition:
		_fail(message)


func _fail(message: String) -> void:
	_failures += 1
	printerr("FAIL: " + message)
```

- [ ] **Step 2: Run the smoke test to verify it fails**

```bash
"$GODOT" --headless --path . --script res://tools/smoke_test.gd 2>&1 | tail -5; echo "exit=${PIPESTATUS[0]}"
```

Expected: `FAIL: res://world/rooms/room_... is missing` lines, `smoke test FAILED: 100 failures`, and `exit=1`.

- [ ] **Step 3: Write the importer**

Create `tools/import_world.gd`:

```gdscript
extends SceneTree
## Builds world/tileset.tres and world/rooms/room_X_Y.tscn from tools/zorta.json.
## Re-running overwrites the generated scenes.
## Run: godot --headless --path . --script res://tools/import_world.gd

const WORLD_JSON := "res://tools/zorta.json"
const TILESET_PATH := "res://world/tileset.tres"
const ROOMS_DIR := "res://world/rooms"
const MONSTER_SCENE := "res://entities/monsters/%s.tscn"
const SRC_TILE := 16
const ART_SCALE := Vector2(2, 2)
const LAYERS := ["background", "midground", "foreground"]

const RoomScript := preload("res://world/room.gd")
const AnimatedTileScript := preload("res://world/animated_tile.gd")
const MonsterSpawnScript := preload("res://world/monster_spawn.gd")


func _init() -> void:
	quit(_run())


func _run() -> int:
	var world = JSON.parse_string(FileAccess.get_file_as_string(WORLD_JSON))
	if world == null:
		printerr("could not read %s" % WORLD_JSON)
		return 1
	DirAccess.make_dir_recursive_absolute(ROOMS_DIR)
	var tileset := _build_tileset(world.sheets)
	for data in world.rooms:
		var room := _build_room(data, tileset)
		var packed := PackedScene.new()
		var err := packed.pack(room)
		if err == OK:
			err = ResourceSaver.save(packed, "%s/room_%d_%d.tscn" % [ROOMS_DIR, int(data.x), int(data.y)])
		room.free()
		if err != OK:
			printerr("failed to save room %d,%d: %s" % [int(data.x), int(data.y), error_string(err)])
			return 1
	print("imported %d rooms" % world.rooms.size())
	return 0


func _build_tileset(sheets: Array) -> TileSet:
	var tileset := TileSet.new()
	tileset.tile_size = Vector2i(SRC_TILE, SRC_TILE)
	for i in sheets.size():
		var source := TileSetAtlasSource.new()
		source.texture = load("res://assets/sprites/%s.png" % sheets[i])
		source.texture_region_size = Vector2i(SRC_TILE, SRC_TILE)
		var grid := source.get_atlas_grid_size()
		for y in grid.y:
			for x in grid.x:
				source.create_tile(Vector2i(x, y))
		tileset.add_source(source, i)
	ResourceSaver.save(tileset, TILESET_PATH)
	# Reload so room scenes reference the saved file instead of embedding a copy.
	return load(TILESET_PATH)


func _build_room(data: Dictionary, tileset: TileSet) -> Node2D:
	var room := Node2D.new()
	room.set_script(RoomScript)
	room.name = "Room_%d_%d" % [int(data.x), int(data.y)]
	room.grid_pos = Vector2i(int(data.x), int(data.y))
	room.music = "" if data.music == null else data.music
	room.has_player_start = data.player_start != null
	if data.player_start != null:
		room.player_start = Vector2(data.player_start[0], data.player_start[1])

	for layer_name in LAYERS:
		var layer := TileMapLayer.new()
		layer.name = layer_name.capitalize()
		layer.tile_set = tileset
		layer.scale = ART_SCALE
		for t in data.layers[layer_name]:
			layer.set_cell(Vector2i(int(t[0]), int(t[1])), int(t[2]), Vector2i(int(t[3]), int(t[4])))
		_add(room, room, layer)

		var animated := Node2D.new()
		animated.name = layer_name.capitalize() + "Animated"
		_add(room, room, animated)
		for a in data.animated:
			if a.layer == layer_name:
				_add(room, animated, _build_animated_tile(a))

		if layer_name == "midground":
			_add(room, room, _build_entities(room, data.monsters))

	_add(room, room, _build_walls(room, data.walls))
	return room


func _build_animated_tile(a: Dictionary) -> Sprite2D:
	var sprite := Sprite2D.new()
	sprite.set_script(AnimatedTileScript)
	var texture: Texture2D = load("res://assets/animations/%s.png" % a.sheet)
	sprite.texture = texture
	sprite.centered = false
	sprite.hframes = texture.get_width() / SRC_TILE
	sprite.vframes = texture.get_height() / SRC_TILE
	sprite.frame_coords = Vector2i(0, int(a.row))
	sprite.scale = ART_SCALE
	sprite.position = Vector2(a.pos[0], a.pos[1])
	sprite.name = "%s_%d_%d" % [a.sheet, int(a.pos[0]), int(a.pos[1])]
	return sprite


func _build_entities(room: Node2D, monsters: Array) -> Node2D:
	var entities := Node2D.new()
	entities.name = "Entities"
	for i in monsters.size():
		var kind: String = monsters[i][0]
		var scene_path := MONSTER_SCENE % kind.to_snake_case()
		var node: Node2D
		if ResourceLoader.exists(scene_path):
			node = load(scene_path).instantiate()
		else:
			node = Marker2D.new()
			node.set_script(MonsterSpawnScript)
			node.kind = kind
		node.name = "%s%d" % [kind, i]
		node.position = Vector2(monsters[i][1], monsters[i][2])
		entities.add_child(node)
	# Owners are assigned once Entities is in the room, in _add.
	return entities


func _build_walls(room: Node2D, walls: Array) -> StaticBody2D:
	var body := StaticBody2D.new()
	body.name = "Walls"
	var material := PhysicsMaterial.new()
	material.friction = 0.5
	body.physics_material_override = material
	for w in walls:
		var segment := SegmentShape2D.new()
		segment.a = Vector2(w[0], w[1])
		segment.b = Vector2(w[2], w[3])
		var shape := CollisionShape2D.new()
		shape.shape = segment
		body.add_child(shape, true)
	return body


## Adds node under parent and makes it, and any children it already has,
## owned by the room so that PackedScene.pack() saves them.
func _add(room: Node2D, parent: Node, node: Node) -> void:
	parent.add_child(node, true)
	node.owner = room
	for child in node.get_children():
		child.owner = room
```

- [ ] **Step 4: Run the importer**

```bash
"$GODOT" --headless --path . --script res://tools/import_world.gd 2>&1 | tail -5; echo "exit=${PIPESTATUS[0]}"
ls world/rooms/*.tscn | wc -l
```

Expected: `imported 100 rooms`, `exit=0`, and `100`.

- [ ] **Step 5: Run the smoke test to verify it passes**

```bash
"$GODOT" --headless --path . --script res://tools/smoke_test.gd 2>&1 | tail -5; echo "exit=${PIPESTATUS[0]}"
```

Expected: `smoke test passed: 100 rooms` and `exit=0`.

- [ ] **Step 6: Confirm rooms reference the shared tile set**

```bash
grep -c 'path="res://world/tileset.tres"' world/rooms/room_4_2.tscn
grep -c "TileSetAtlasSource" world/rooms/room_4_2.tscn
```

Expected: `1`, then `0` (the tile set is an external resource, not embedded).

- [ ] **Step 7: Commit**

```bash
git add tools/import_world.gd tools/smoke_test.gd world
git commit -m "Import the world into room scenes with a smoke test

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Room viewer

**Files:**
- Create: `scenes/room_viewer.gd`
- Create: `scenes/room_viewer.tscn`
- Modify: `project.godot` (add the main scene)

A temporary main scene for checking rooms by eye. Arrow keys move between rooms. Wall collision is drawn. It can also save a screenshot and quit, which is how this task is verified.

- [ ] **Step 1: Create `scenes/room_viewer.gd`**

```gdscript
extends Node2D
## Temporary viewer for checking imported rooms. Arrow keys change room.
## To save a screenshot and quit:
##   godot --path . -- --room=4,2 --shot=C:/some/file.png

var _grid := Vector2i(4, 2)
var _room: Node2D
var _shot_path := ""

@onready var _label: Label = $Label


func _ready() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--room="):
			var parts := arg.trim_prefix("--room=").split(",")
			_grid = Vector2i(int(parts[0]), int(parts[1]))
		elif arg.begins_with("--shot="):
			_shot_path = arg.trim_prefix("--shot=")
	get_tree().debug_collisions_hint = true
	_show_room()
	if _shot_path != "":
		await RenderingServer.frame_post_draw
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png(_shot_path)
		get_tree().quit()


func _unhandled_key_input(event: InputEvent) -> void:
	if not event.pressed:
		return
	var step := Vector2i.ZERO
	match event.keycode:
		KEY_LEFT:
			step = Vector2i.LEFT
		KEY_RIGHT:
			step = Vector2i.RIGHT
		KEY_UP:
			step = Vector2i.UP
		KEY_DOWN:
			step = Vector2i.DOWN
	if step != Vector2i.ZERO:
		_grid = (_grid + step).clamp(Vector2i.ZERO, Vector2i(9, 9))
		_show_room()


func _show_room() -> void:
	if _room != null:
		_room.queue_free()
	_room = load("res://world/rooms/room_%d_%d.tscn" % [_grid.x, _grid.y]).instantiate()
	add_child(_room)
	move_child(_room, 0)
	_label.text = "%d,%d\n%s" % [_grid.x, _grid.y, _room.music]
```

- [ ] **Step 2: Create `scenes/room_viewer.tscn`**

```
[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scenes/room_viewer.gd" id="1"]

[node name="RoomViewer" type="Node2D"]
script = ExtResource("1")

[node name="Label" type="Label" parent="."]
offset_left = 962.0
offset_top = 4.0
offset_right = 1022.0
offset_bottom = 200.0
theme_override_font_sizes/font_size = 10
autowrap_mode = 1
```

- [ ] **Step 3: Set the main scene**

In `project.godot`, add this line in the `[application]` section, directly after `config/name="Extranaut"`:

```ini
run/main_scene="res://scenes/room_viewer.tscn"
```

- [ ] **Step 4: Save screenshots of three rooms**

```bash
mkdir -p build/shots
for r in 4,2 0,0 5,5; do
  "$GODOT" --path . -- --room=$r --shot="$(pwd -W)/build/shots/room_${r/,/_}.png" 2>&1 | grep -i error
done
ls -la build/shots
```

Expected: three PNG files, each larger than 10 KB, and no error lines. (`build/` is git-ignored.)

- [ ] **Step 5: Compare room 4,2 with the original by eye**

Open `build/shots/room_4_2.png`. Check all of the following:

- Rock tiles form a coherent room: edges line up, with no scrambled or offset tiles.
- Collision lines (drawn by the debug overlay) follow the edges of the solid rock.
- The area right of x = 960 is empty apart from the label reading `4,2` and `zortaSurface`.

If tiles look scrambled, the atlas coordinates are wrong: re-check `rect / 32` in `tools/extract_world.py` against the 16 px cell size in `tools/import_world.gd`.

- [ ] **Step 6: Run the full checks again**

```bash
python -m unittest discover -s tools -p "test_*.py" 2>&1 | tail -3
"$GODOT" --headless --path . --script res://tools/smoke_test.gd 2>&1 | tail -2
```

Expected: `OK`, and `smoke test passed: 100 rooms`.

- [ ] **Step 7: Commit**

```bash
git add scenes project.godot
git commit -m "Add a room viewer as the temporary main scene

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Done when

- `python -m unittest discover -s tools -p "test_*.py"` reports 9 passing tests.
- The smoke test reports `smoke test passed: 100 rooms`.
- Running the project opens the viewer on room 4,2, and the arrow keys move between rooms.
- The screenshot of room 4,2 shows correctly assembled tiles with collision lines along the rock edges.
