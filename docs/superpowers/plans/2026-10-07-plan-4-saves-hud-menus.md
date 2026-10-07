# Extranaut Port, Plan 4: Saves, HUD, Map and Menus

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A complete game loop: a title screen with three save slots, an intro, the campaign with a real HUD, minimap and pause menu, progress saved to disk, and an ending.

**Architecture:** A `Progress` object holds everything a slot remembers and converts to and from a dictionary; `SaveGame` reads and writes it as JSON under `user://`. A `Main` scene swaps one child screen at a time (title, image screen, campaign). The campaign takes a slot and a `Progress`, updates it as rooms are entered and save events fire, and writes it. The HUD and map are custom-drawn `Control`s fed by the campaign.

**Tech Stack:** Godot 4.7 GDScript, headless `--script` tests.

**Spec:** `docs/superpowers/specs/2026-10-07-extranaut-godot-port-design.md`

**This is plan 4 of 7.** Out of scope: Chaosnaut and its title button (plan 5); sound, music and effects (plan 6); web export (plan 7).

---

## Conventions for every task

- Shell is Git Bash. Run commands from the repository root.
- Godot binary:

```bash
GODOT="/c/Users/mattf/Desktop/godot47/Godot_v4.7-stable_win64_console.exe"
```

- GDScript files are indented with tabs.
- Work on branch `plan-4-saves-hud-menus`.
- Commit messages end with the attribution trailer lines in force for the session.
- Every whole-file code block is introduced by ``Create `path`:`` or ``Replace `path` with:``. Write the block to that path exactly.
- Each test command also counts `SCRIPT ERROR` lines in its output, and that count must be 0.

## Facts from the original

- Title screen (`titleMenu.py`): background `titleTerrainSmall` at 2x; the animated title `extranautTitleAnimated` (4 frames of 144x32, 60 ms each) drawn at 4x at (250, 50); credit strips `kopa` at 2x at (80, 250) and `matt` at 2x at (300, 300). Buttons are black with a 1 px white border, 20 px tall, in the KARNIVOR font at size 13. Slot rows sit at y = 384, 444 and 504.
- Intro and ending are single images (`intro`, `ending`, 512x384 at 2x) dismissed by any key, click or button.
- HUD (`playerCharacter.py`): HP pips stack upward from the bottom of the screen at x = 960; fuel pips do the same at x = 992, one per 500 fuel. Both come from `bars.png`: the HP pip is the 16 px cell at (0, 0) and the fuel pip is the cell at (16, 0), drawn at 2x.
- `options.png` holds four 16 px icons: sound off (0, 0), sound on (16, 0), windowed (0, 16), fullscreen (16, 16).
- The game is won when the player falls out of the bottom of a row-9 room.
- A new game writes its save immediately, so the slot shows as in use straight away.
- Player stats are saved only at save points and powerups. Dying returns to the checkpoint.

## Decisions

- Progress is also written each time a room is entered, so the explored map survives quitting. Stats and checkpoint still only change at save points and powerups, so this cannot be used to skip back.
- A save file that cannot be read is treated as an empty slot.
- Pause is P, Enter or gamepad Start. A focused menu button consumes Enter, so Enter resumes through the Resume button without also toggling pause.
- The credit strip no longer opens a web page.
- The version label reads `Version 2.0`.
- `--room=X,Y` on the command line skips the title and starts an unsaved campaign in that room; `--shot=path` saves a screenshot after one second and quits. Both are for development.
- In debug builds only, F9 raises gun level, F10 adds 500 max fuel, F11 adds 1 max HP and F12 adds an artifact, as the original's cheat keys did.

## Save format

`user://save_N.json` for N in 1 to 3:

```json
{
  "version": 1,
  "checkpoint": [4, 2],
  "max_hp": 5,
  "max_fuel": 2000.0,
  "gun_level": 1,
  "artifacts": 0,
  "powerups_taken": [[0, 0]],
  "visited": [[4, 2], [5, 2]],
  "save_points": [[4, 2]]
}
```

## File structure

| Path | Responsibility |
| --- | --- |
| `save/progress.gd` | What a slot remembers; dictionary conversion |
| `save/save_game.gd` | Slot files: read, write, delete |
| `ui/ui_kit.gd` | Font, label and button styling shared by all screens |
| `ui/map_view.gd` | Draws the 10x10 room map at any cell size |
| `ui/hud.gd` | HUD strip: HP, fuel, artifacts, "saved" notice |
| `ui/pause_menu.gd` | Pause overlay with the large map |
| `scenes/image_screen.gd` | Full-screen image dismissed by any input |
| `scenes/title.gd` | Title screen and slot buttons |
| `scenes/main.gd`, `main.tscn` | Screen flow; the project's main scene |
| `scenes/campaign.gd`, `campaign.tscn` | Uses Progress, saves, HUD, pause, win |
| `input/controls.gd` | Adds the pause action |
| `entities/monsters/monster.gd`, `tools/make_monster_scenes.py` | `is_save_point` flag |
| `tools/test_save.gd`, `tools/test_main.gd`, `tools/test_campaign.gd` | Tests |

---

### Task 1: Progress and save files

**Files:**
- Create: `tools/test_save.gd`
- Create: `save/progress.gd`
- Create: `save/save_game.gd`

- [ ] **Step 1: Write the failing test**

Create `tools/test_save.gd`:

```gdscript
extends SceneTree
## Tests for Progress and SaveGame.
## Run: godot --headless --path . --script res://tools/test_save.gd

const Progress := preload("res://save/progress.gd")
const SaveGame := preload("res://save/save_game.gd")

var _failures := 0


func _init() -> void:
	_test_progress()
	_test_save_files()
	print("save test passed" if _failures == 0 else "save test FAILED: %d failures" % _failures)
	quit(1 if _failures > 0 else 0)


func _test_progress() -> void:
	var fresh := Progress.new()
	_expect(fresh.checkpoint == Vector2i(4, 2), "a new game starts in room 4,2")
	_expect(fresh.max_hp == 5 and fresh.max_fuel == 2000.0, "a new game has 5 hp and 2000 fuel")
	_expect(fresh.gun_level == 1 and fresh.artifacts == 0, "a new game has gun level 1 and no artifacts")

	var progress := Progress.new()
	progress.checkpoint = Vector2i(7, 3)
	progress.max_hp = 7
	progress.max_fuel = 3500.0
	progress.gun_level = 3
	progress.artifacts = 2
	progress.powerups_taken[Vector2i(0, 0)] = true
	progress.visited[Vector2i(4, 2)] = true
	progress.visited[Vector2i(5, 2)] = true
	progress.save_points[Vector2i(4, 2)] = true
	# Through JSON text, as a real save goes.
	var copy = Progress.from_dict(JSON.parse_string(JSON.stringify(progress.to_dict())))
	_expect(copy != null, "a saved dictionary loads")
	if copy != null:
		_expect(copy.checkpoint == Vector2i(7, 3), "checkpoint survives")
		_expect(copy.max_hp == 7 and copy.max_fuel == 3500.0, "hp and fuel survive")
		_expect(copy.gun_level == 3 and copy.artifacts == 2, "gun level and artifacts survive")
		_expect(copy.powerups_taken.has(Vector2i(0, 0)) and copy.powerups_taken.size() == 1, "powerups taken survive")
		_expect(copy.visited.has(Vector2i(5, 2)) and copy.visited.size() == 2, "visited rooms survive")
		_expect(copy.save_points.has(Vector2i(4, 2)), "save points survive")

	_expect(Progress.from_dict({}) == null, "an empty dictionary is rejected")
	var broken := progress.to_dict()
	broken["checkpoint"] = "nowhere"
	_expect(Progress.from_dict(broken) == null, "a malformed checkpoint is rejected")


func _test_save_files() -> void:
	SaveGame.directory = "user://test_saves/"
	DirAccess.make_dir_recursive_absolute(SaveGame.directory)
	for slot: int in SaveGame.SLOTS:
		SaveGame.delete(slot)
	_expect(not SaveGame.exists(1), "an unused slot does not exist")
	_expect(SaveGame.read(1) == null, "an unused slot reads as null")

	var progress := Progress.new()
	progress.artifacts = 3
	_expect(SaveGame.write(2, progress), "writing a slot succeeds")
	_expect(SaveGame.exists(2) and not SaveGame.exists(1), "only the written slot exists")
	var loaded = SaveGame.read(2)
	_expect(loaded != null and loaded.artifacts == 3, "a written slot reads back")

	var file := FileAccess.open(SaveGame.path(3), FileAccess.WRITE)
	file.store_string("{ this is not json")
	file.close()
	_expect(SaveGame.read(3) == null, "a corrupt slot reads as null")

	SaveGame.delete(2)
	SaveGame.delete(3)
	_expect(not SaveGame.exists(2), "a deleted slot is gone")


func _expect(condition: bool, message: String) -> void:
	if not condition:
		_failures += 1
		printerr("FAIL: " + message)
```

- [ ] **Step 2: Run it to verify it fails**

```bash
"$GODOT" --headless --path . --script res://tools/test_save.gd 2>&1 | grep -c "Preload file"
```

Expected: `2` (both preloads are missing).

- [ ] **Step 3: Write Progress**

Create `save/progress.gd`:

```gdscript
extends RefCounted
## Everything a save slot remembers.

const VERSION := 1
const START_ROOM := Vector2i(4, 2)

## The room the player respawns in. Set by save points and powerups.
var checkpoint := START_ROOM
var max_hp := 5
var max_fuel := 2000.0
var gun_level := 1
var artifacts := 0
## Sets of rooms, stored as Vector2i keys with the value true.
var powerups_taken := {}
var visited := {}
var save_points := {}


func to_dict() -> Dictionary:
	return {
		"version": VERSION,
		"checkpoint": [checkpoint.x, checkpoint.y],
		"max_hp": max_hp,
		"max_fuel": max_fuel,
		"gun_level": gun_level,
		"artifacts": artifacts,
		"powerups_taken": _cells_to_array(powerups_taken),
		"visited": _cells_to_array(visited),
		"save_points": _cells_to_array(save_points),
	}


## Returns a Progress, or null if data is not a valid save.
static func from_dict(data: Dictionary) -> RefCounted:
	for key in ["max_hp", "max_fuel", "gun_level", "artifacts"]:
		if not (data.get(key) is float or data.get(key) is int):
			return null
	for key in ["powerups_taken", "visited", "save_points"]:
		if not data.get(key) is Array:
			return null
	if not _is_cell(data.get("checkpoint")):
		return null
	var progress = new()
	progress.checkpoint = _to_cell(data["checkpoint"])
	progress.max_hp = int(data["max_hp"])
	progress.max_fuel = float(data["max_fuel"])
	progress.gun_level = int(data["gun_level"])
	progress.artifacts = int(data["artifacts"])
	progress.powerups_taken = _array_to_cells(data["powerups_taken"])
	progress.visited = _array_to_cells(data["visited"])
	progress.save_points = _array_to_cells(data["save_points"])
	return progress


static func _cells_to_array(cells: Dictionary) -> Array:
	var result := []
	for cell in cells:
		result.append([cell.x, cell.y])
	return result


static func _array_to_cells(array: Array) -> Dictionary:
	var result := {}
	for item in array:
		if _is_cell(item):
			result[_to_cell(item)] = true
	return result


static func _is_cell(value: Variant) -> bool:
	return value is Array and value.size() == 2 and (value[0] is float or value[0] is int) and (value[1] is float or value[1] is int)


static func _to_cell(value: Array) -> Vector2i:
	return Vector2i(int(value[0]), int(value[1]))
```

- [ ] **Step 4: Write SaveGame**

Create `save/save_game.gd`:

```gdscript
extends RefCounted
## Reads and writes save slots as JSON files.

const Progress := preload("res://save/progress.gd")
const SLOTS := [1, 2, 3]

## Where slot files live. Tests point this somewhere else.
static var directory := "user://"


static func path(slot: int) -> String:
	return "%ssave_%d.json" % [directory, slot]


static func exists(slot: int) -> bool:
	return FileAccess.file_exists(path(slot))


## Returns the slot's Progress, or null if the slot is empty or unreadable.
static func read(slot: int) -> RefCounted:
	if not exists(slot):
		return null
	var json := JSON.new()
	if json.parse(FileAccess.get_file_as_string(path(slot))) != OK:
		return null
	if not json.data is Dictionary:
		return null
	return Progress.from_dict(json.data)


static func write(slot: int, progress: RefCounted) -> bool:
	var file := FileAccess.open(path(slot), FileAccess.WRITE)
	if file == null:
		push_warning("could not write %s" % path(slot))
		return false
	file.store_string(JSON.stringify(progress.to_dict()))
	return true


static func delete(slot: int) -> void:
	if exists(slot):
		DirAccess.remove_absolute(path(slot))
```

- [ ] **Step 5: Run the test to verify it passes**

```bash
"$GODOT" --headless --path . --script res://tools/test_save.gd 2>&1 | tee /tmp/out.txt | tail -1; grep -c "SCRIPT ERROR" /tmp/out.txt
```

Expected: `save test passed` and `0`.

- [ ] **Step 6: Commit**

```bash
git add save tools/test_save.gd
git commit -m "Add Progress and save slot files"
```

---

### Task 2: UI kit, map view, HUD and pause menu

**Files:**
- Create: `ui/ui_kit.gd`, `ui/map_view.gd`, `ui/hud.gd`, `ui/pause_menu.gd`

These are exercised through the campaign in Task 4 and the main flow in Task 5.

- [ ] **Step 1: UI kit**

Create `ui/ui_kit.gd`:

```gdscript
extends RefCounted
## Shared look for menus and the HUD: the original's font, and its black
## buttons with a one-pixel border.

const FONT := preload("res://assets/fonts/KARNIVOR.ttf")
const FONT_SIZE := 13
const BORDER := Color.WHITE
const BORDER_FOCUS := Color(1.0, 0.85, 0.2)


static func make_label(text: String) -> Label:
	var label := Label.new()
	label.text = text
	label.add_theme_font_override("font", FONT)
	label.add_theme_font_size_override("font_size", FONT_SIZE)
	return label


static func make_button(text: String, button_size: Vector2) -> Button:
	var button := Button.new()
	button.text = text
	button.custom_minimum_size = button_size
	button.size = button_size
	button.add_theme_font_override("font", FONT)
	button.add_theme_font_size_override("font_size", FONT_SIZE)
	button.add_theme_stylebox_override("normal", _box(Color.BLACK, BORDER))
	button.add_theme_stylebox_override("hover", _box(Color.BLACK, BORDER_FOCUS))
	button.add_theme_stylebox_override("focus", _box(Color.BLACK, BORDER_FOCUS))
	button.add_theme_stylebox_override("pressed", _box(Color(0.25, 0.25, 0.25), BORDER_FOCUS))
	return button


static func _box(fill: Color, border: Color) -> StyleBoxFlat:
	var box := StyleBoxFlat.new()
	box.bg_color = fill
	box.border_color = border
	box.set_border_width_all(1)
	return box
```

- [ ] **Step 2: Map view**

Create `ui/map_view.gd`:

```gdscript
extends Control
## Draws the 10x10 room map: explored rooms, known save points and the
## current room, which blinks.

enum Cell { UNKNOWN, VISITED, SAVE_POINT, CURRENT }

const GRID := Vector2i(10, 10)
const BLINK_PERIOD := 0.6
const COLORS := {
	Cell.UNKNOWN: Color(0.13, 0.13, 0.15),
	Cell.VISITED: Color(0.45, 0.45, 0.52),
	Cell.SAVE_POINT: Color(0.3, 0.6, 1.0),
	Cell.CURRENT: Color.WHITE,
}

## Pixels per room, including a one-pixel gap.
@export var cell_size := 6.0

var _visited := {}
var _save_points := {}
var _current := Vector2i(-1, -1)
var _blink := 0.0


static func cell_state(cell: Vector2i, visited: Dictionary, save_points: Dictionary, current: Vector2i) -> Cell:
	if cell == current:
		return Cell.CURRENT
	if not visited.has(cell):
		return Cell.UNKNOWN
	return Cell.SAVE_POINT if save_points.has(cell) else Cell.VISITED


## progress is a save/progress.gd object.
func show_progress(progress: RefCounted, current: Vector2i) -> void:
	_visited = progress.visited
	_save_points = progress.save_points
	_current = current
	queue_redraw()


func _process(delta: float) -> void:
	var was_lit := _is_lit()
	_blink = fmod(_blink + delta, BLINK_PERIOD)
	if was_lit != _is_lit():
		queue_redraw()


func _is_lit() -> bool:
	return _blink < BLINK_PERIOD / 2.0


func _draw() -> void:
	for y in GRID.y:
		for x in GRID.x:
			var cell := Vector2i(x, y)
			var state := cell_state(cell, _visited, _save_points, _current)
			if state == Cell.CURRENT and not _is_lit():
				# Blink to what the room would otherwise show.
				state = cell_state(cell, _visited, _save_points, Vector2i(-1, -1))
			draw_rect(Rect2(Vector2(cell) * cell_size, Vector2(cell_size - 1.0, cell_size - 1.0)), COLORS[state])
```

- [ ] **Step 3: HUD**

Create `ui/hud.gd`:

```gdscript
extends Control
## The strip down the right of the screen: HP and fuel pips stacked from the
## bottom, artifacts collected, and a notice when the game saves. The minimap
## is a child node.

const UiKit := preload("res://ui/ui_kit.gd")
const BarsTexture := preload("res://assets/sprites/bars.png")
const CollectiblesTexture := preload("res://assets/animations/collectibles.png")

const STRIP := Rect2(960, 0, 64, 768)
const PIP_SIZE := 32.0
const HP_REGION := Rect2(0, 0, 16, 16)
const FUEL_REGION := Rect2(16, 0, 16, 16)
const ARTIFACT_REGION := Rect2(0, 16, 16, 16)
const FUEL_PER_PIP := 500.0
const ARTIFACTS_TOP := 72.0
const SAVED_NOTICE_TIME := 1.5

var _hp := 0
var _fuel_pips := 0
var _artifacts := 0
var _saved_timer := 0.0
var _saved_label: Label


static func fuel_pips(fuel: float) -> int:
	return int(fuel / FUEL_PER_PIP)


func _ready() -> void:
	_saved_label = UiKit.make_label("SAVED")
	_saved_label.position = Vector2(STRIP.position.x, ARTIFACTS_TOP + PIP_SIZE * 2.0 + 8.0)
	_saved_label.size = Vector2(STRIP.size.x, 20.0)
	_saved_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_saved_label.hide()
	add_child(_saved_label)


func set_status(hp: int, fuel: float, artifacts: int) -> void:
	var pips := fuel_pips(fuel)
	if hp != _hp or pips != _fuel_pips or artifacts != _artifacts:
		_hp = hp
		_fuel_pips = pips
		_artifacts = artifacts
		queue_redraw()


func show_saved() -> void:
	_saved_label.show()
	_saved_timer = SAVED_NOTICE_TIME


func _process(delta: float) -> void:
	if _saved_timer > 0.0:
		_saved_timer -= delta
		if _saved_timer <= 0.0:
			_saved_label.hide()


func _draw() -> void:
	draw_rect(STRIP, Color.BLACK)
	var bottom := STRIP.position.y + STRIP.size.y
	for i in _hp:
		var at := Vector2(STRIP.position.x, bottom - PIP_SIZE * (i + 1))
		draw_texture_rect_region(BarsTexture, Rect2(at, Vector2(PIP_SIZE, PIP_SIZE)), HP_REGION)
	for i in _fuel_pips:
		var at := Vector2(STRIP.position.x + PIP_SIZE, bottom - PIP_SIZE * (i + 1))
		draw_texture_rect_region(BarsTexture, Rect2(at, Vector2(PIP_SIZE, PIP_SIZE)), FUEL_REGION)
	for i in _artifacts:
		var at := Vector2(STRIP.position.x + PIP_SIZE * (i % 2), ARTIFACTS_TOP + PIP_SIZE * (i / 2))
		draw_texture_rect_region(CollectiblesTexture, Rect2(at, Vector2(PIP_SIZE, PIP_SIZE)), ARTIFACT_REGION)
```

- [ ] **Step 4: Pause menu**

Create `ui/pause_menu.gd`:

```gdscript
extends CanvasLayer
## The pause overlay: a large map with Resume and Quit to Title.

signal resume_pressed
signal quit_pressed

const UiKit := preload("res://ui/ui_kit.gd")
const MapView := preload("res://ui/map_view.gd")

const SCREEN := Vector2(1024, 768)
const MAP_CELL := 24.0
const BUTTON_SIZE := Vector2(140, 20)

var _map: Control
var _resume: Button


func _ready() -> void:
	var dim := ColorRect.new()
	dim.color = Color(0, 0, 0, 0.8)
	dim.size = SCREEN
	add_child(dim)

	var heading := UiKit.make_label("PAUSED")
	heading.position = Vector2(0, 80)
	heading.size = Vector2(SCREEN.x, 20)
	heading.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(heading)

	_map = Control.new()
	_map.set_script(MapView)
	_map.cell_size = MAP_CELL
	_map.position = Vector2((SCREEN.x - MAP_CELL * 10.0) / 2.0, 130)
	_map.size = Vector2(MAP_CELL * 10.0, MAP_CELL * 10.0)
	add_child(_map)

	_resume = _add_button("Resume", "Resume Game", 420.0)
	_resume.pressed.connect(func() -> void: resume_pressed.emit())
	var quit := _add_button("Quit", "Quit to Title", 470.0)
	quit.pressed.connect(func() -> void: quit_pressed.emit())


## progress is a save/progress.gd object.
func open(progress: RefCounted, current: Vector2i) -> void:
	_map.show_progress(progress, current)
	_resume.grab_focus()


func _add_button(node_name: String, text: String, y: float) -> Button:
	var button := UiKit.make_button(text, BUTTON_SIZE)
	button.name = node_name
	button.position = Vector2((SCREEN.x - BUTTON_SIZE.x) / 2.0, y)
	add_child(button)
	return button
```

- [ ] **Step 5: Check they parse**

```bash
"$GODOT" --headless --path . --import 2>&1 | grep -i -E "parse error|SCRIPT ERROR"; echo "grep_exit=$?"
```

Expected: no matching lines and `grep_exit=1`.

- [ ] **Step 6: Commit**

```bash
git add ui
git commit -m "Add the UI kit, map view, HUD and pause menu"
```

---

### Task 3: Pause action and save-point flag

**Files:**
- Modify: `input/controls.gd`
- Modify: `entities/monsters/monster.gd`
- Modify: `tools/make_monster_scenes.py`
- Regenerate: `entities/monsters/save_point.tscn`

- [ ] **Step 1: Add the pause action**

In `input/controls.gd`, add this entry to `ACTIONS` directly after the `"fire"` entry:

```gdscript
	"pause": {
		"keys": [KEY_P, KEY_ENTER],
		"buttons": [JOY_BUTTON_START],
	},
```

- [ ] **Step 2: Flag save points**

In `entities/monsters/monster.gd`, add directly after the line `@export var is_powerup := false`:

```gdscript
## Marks the room on the map once the player has been there.
@export var is_save_point := false
```

In `tools/make_monster_scenes.py`, change the save point row to:

```python
    monster("save_point", "save_point", "animations/savePoint", is_save_point=True, **HEAVY),
```

- [ ] **Step 3: Regenerate and verify**

```bash
python tools/make_monster_scenes.py
grep -c "is_save_point = true" entities/monsters/save_point.tscn
git status --short entities/monsters | wc -l
"$GODOT" --headless --path . --script res://tools/test_monsters.gd 2>&1 | tail -1
```

Expected: `Wrote 25 monster scenes`, `1`, `2` (only `monster.gd` and `save_point.tscn` changed), and `monster test passed`.

- [ ] **Step 4: Commit**

```bash
git add input entities/monsters tools/make_monster_scenes.py
git commit -m "Add the pause action and flag save points"
```

---

### Task 4: Campaign uses Progress, saves, HUD, pause and win

**Files:**
- Modify: `tools/test_campaign.gd`
- Modify: `scenes/campaign.gd`
- Modify: `scenes/campaign.tscn`

- [ ] **Step 1: Update the test for the new API and add the new checks**

Make these edits to `tools/test_campaign.gd`.

Add two constants directly after the `CampaignScript` constant:

```gdscript
const Progress := preload("res://save/progress.gd")
const SaveGame := preload("res://save/save_game.gd")
```

In `_run`, replace the two lines

```gdscript
	var campaign: Node2D = load("res://scenes/campaign.tscn").instantiate()
	root.add_child(campaign)
```

with

```gdscript
	SaveGame.directory = "user://test_saves/"
	DirAccess.make_dir_recursive_absolute(SaveGame.directory)
	SaveGame.delete(3)
	var campaign: Node2D = load("res://scenes/campaign.tscn").instantiate()
	campaign.slot = 3
	root.add_child(campaign)
```

In `_run`, replace the line `	_check_powerups_taken(campaign)` with:

```gdscript
	_check_powerups_taken(campaign)
	await _check_saving_map_and_pause(campaign, player)
```

In `_run`, replace the line `	await _check_one_tile_shaft()` with:

```gdscript
	await _check_one_tile_shaft()
	await _check_win()
	SaveGame.delete(3)
```

Replace every `campaign.checkpoint` with `campaign.progress.checkpoint`, and every `campaign.powerups_taken` with `campaign.progress.powerups_taken`.

In `_check_one_tile_shaft`, replace the line `		campaign.grid = Vector2i(3, 2)` with:

```gdscript
		campaign.progress = Progress.new()
		campaign.progress.checkpoint = Vector2i(3, 2)
```

Add these functions directly before `func _check_exit_rules() -> void:`:

```gdscript
## Runs in room (4, 2) after the save point there has been activated, in a
## campaign using slot 3 that has also visited room (5, 2).
func _check_saving_map_and_pause(campaign: Node2D, player: RigidBody2D) -> void:
	var saved = SaveGame.read(3)
	_expect(saved != null, "the campaign writes its slot")
	if saved != null:
		_expect(saved.checkpoint == Vector2i(4, 2), "the save holds the checkpoint")
		_expect(saved.visited.has(Vector2i(4, 2)) and saved.visited.has(Vector2i(5, 2)), "the save holds visited rooms")
		_expect(saved.save_points.has(Vector2i(4, 2)), "the save holds discovered save points")
		_expect(not saved.save_points.has(Vector2i(5, 2)), "rooms without a save point are not marked")

	# Stats are captured at save events.
	player.max_hp = 6
	player.artifacts = 2
	campaign.room.get_node("Entities").get_child(0).activated = false
	campaign.room.get_node("Entities").get_child(0).hit()
	saved = SaveGame.read(3)
	_expect(saved != null and saved.max_hp == 6 and saved.artifacts == 2, "a save point saves the player's stats")

	var hud: Control = campaign.get_node("Hud/Strip")
	_expect(hud.fuel_pips(2000.0) == 4 and hud.fuel_pips(499.0) == 0, "one fuel pip per 500 fuel")
	var map: Control = campaign.get_node("Hud/Strip/MiniMap")
	_expect(map.cell_state(Vector2i(4, 2), campaign.progress.visited, campaign.progress.save_points, Vector2i(4, 2)) == map.Cell.CURRENT, "the current room is marked")
	_expect(map.cell_state(Vector2i(4, 2), campaign.progress.visited, campaign.progress.save_points, Vector2i(0, 0)) == map.Cell.SAVE_POINT, "a visited save room is marked")
	_expect(map.cell_state(Vector2i(5, 2), campaign.progress.visited, campaign.progress.save_points, Vector2i(0, 0)) == map.Cell.VISITED, "a visited room is marked")
	_expect(map.cell_state(Vector2i(9, 9), campaign.progress.visited, campaign.progress.save_points, Vector2i(0, 0)) == map.Cell.UNKNOWN, "an unvisited room is unknown")

	# Pause toggles with the pause action.
	var pause_menu: CanvasLayer = campaign.get_node("PauseMenu")
	_expect(not pause_menu.visible and not paused, "the game starts unpaused")
	_press("pause")
	await _frames(3)
	_expect(pause_menu.visible and paused, "the pause action opens the pause menu")
	_press("pause")
	await _frames(3)
	_expect(not pause_menu.visible and not paused, "the pause action closes the pause menu")

	# Resume and Quit buttons.
	_press("pause")
	await _frames(3)
	pause_menu.get_node("Resume").pressed.emit()
	await _frames(2)
	_expect(not pause_menu.visible and not paused, "Resume closes the pause menu")
	var quits := [0]
	campaign.quit_to_title.connect(func() -> void: quits[0] += 1)
	_press("pause")
	await _frames(3)
	pause_menu.get_node("Quit").pressed.emit()
	await _frames(2)
	_expect(quits[0] == 1, "Quit to Title is signalled")
	_expect(not paused, "quitting unpauses the tree")


func _check_win() -> void:
	var campaign: Node2D = load("res://scenes/campaign.tscn").instantiate()
	campaign.progress = Progress.new()
	campaign.progress.checkpoint = Vector2i(4, 9)
	root.add_child(campaign)
	var player: RigidBody2D = campaign.get_node("Player")
	var wins := [0]
	campaign.won.connect(func() -> void: wins[0] += 1)
	await _frames(5)
	_expect(wins[0] == 0, "standing in a bottom-row room does not win")
	player.global_position = campaign.room.position + Vector2(480, 790)
	await _frames(5)
	_expect(wins[0] == 1, "falling out of the bottom row wins once, count %d" % wins[0])
	root.remove_child(campaign)
	campaign.free()


func _press(action: String) -> void:
	var event := InputEventAction.new()
	event.action = action
	event.pressed = true
	Input.parse_input_event(event)


```

- [ ] **Step 2: Run it to verify it fails**

```bash
"$GODOT" --headless --path . --script res://tools/test_campaign.gd 2>&1 | grep -E "SCRIPT ERROR" | head -2
```

Expected: errors about `slot` or `progress` not existing on the campaign.

- [ ] **Step 3: Rewrite the campaign script**

Replace `scenes/campaign.gd` with:

```gdscript
extends Node2D
## The campaign: owns the current room, the player, shots and the camera,
## moves between rooms when the player crosses an edge, and records progress.
## Set slot and progress before adding it to the tree.

## The player fell out of the bottom of the world.
signal won
signal quit_to_title

const Controls := preload("res://input/controls.gd")
const Progress := preload("res://save/progress.gd")
const SaveGame := preload("res://save/save_game.gd")

const ROOM_SIZE := Vector2(960, 768)
const GRID_SIZE := Vector2i(10, 10)
## Camera centre relative to the room origin: the room fills the left 960 px
## of the 1024 px view and the HUD strip covers the rest.
const VIEW_CENTER := Vector2(512, 384)
const SLIDE_TIME := 0.35
## How far below a bottom-row room the player must fall to win.
const WIN_DEPTH := 16.0
const MAX_GUN_LEVEL := 4

## Save slot 1 to 3, or 0 to play without saving.
var slot := 0
## A save/progress.gd object. A fresh one is made if none is given.
var progress: RefCounted
var grid := Vector2i.ZERO
var room: Node2D

## False from a transition until the player has left every exit zone, so
## arriving inside the opposite zone does not bounce straight back.
var _exits_armed := false
var _sliding := false
var _finished := false

@onready var _world: Node2D = $World
@onready var _player: RigidBody2D = $Player
@onready var _shots: Node2D = $Shots
@onready var _camera: Camera2D = $Camera2D
@onready var _hud: Control = $Hud/Strip
@onready var _mini_map: Control = $Hud/Strip/MiniMap
@onready var _pause_menu: CanvasLayer = $PauseMenu


func _ready() -> void:
	Controls.setup()
	if progress == null:
		progress = Progress.new()
	grid = progress.checkpoint
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--room="):
			var parts := arg.trim_prefix("--room=").split(",")
			grid = Vector2i(int(parts[0]), int(parts[1]))

	_player.max_hp = progress.max_hp
	_player.hp = progress.max_hp
	_player.jetpack.max_fuel = progress.max_fuel
	_player.jetpack.fuel = progress.max_fuel
	_player.gun_level = progress.gun_level
	_player.artifacts = progress.artifacts
	_player.shot_fired.connect(_on_shot_fired)
	_player.died.connect(_respawn)
	_pause_menu.resume_pressed.connect(_set_pause_menu.bind(false))
	_pause_menu.quit_pressed.connect(_quit_to_title)

	room = load_room(grid)
	_world.add_child(room)
	_place_player_at_start()
	_note_room()


func _process(_delta: float) -> void:
	_hud.set_status(_player.hp, _player.jetpack.fuel, _player.artifacts)


func _physics_process(_delta: float) -> void:
	if _sliding or _finished:
		return
	var local := _player.global_position - room.position
	if grid.y == GRID_SIZE.y - 1 and local.y >= ROOM_SIZE.y + WIN_DEPTH:
		_finished = true
		won.emit()
		return
	var step := exit_step(local)
	if step == Vector2i.ZERO:
		_exits_armed = true
		return
	if not _exits_armed:
		return
	var next := grid + step
	if next.x < 0 or next.y < 0 or next.x >= GRID_SIZE.x or next.y >= GRID_SIZE.y:
		return
	_enter_room(next, step, local)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("pause") and not _sliding and not _finished:
		_set_pause_menu(not _pause_menu.visible)


## The original's cheat keys, in debug builds only.
func _unhandled_key_input(event: InputEvent) -> void:
	if not OS.is_debug_build() or not event.pressed or event.echo:
		return
	match event.keycode:
		KEY_F9:
			_player.gun_level = mini(_player.gun_level + 1, MAX_GUN_LEVEL)
		KEY_F10:
			_player.jetpack.max_fuel += 500.0
		KEY_F11:
			_player.max_hp += 1
			_player.hp += 1
		KEY_F12:
			_player.artifacts += 1


## Which way the player is leaving, given its centre in room coordinates.
## Thresholds are the original's, converted from sprite corner to centre. Many
## rooms have walls drawn on their borders to contain monsters and shots; the
## horizontal thresholds sit 1 px inside the point where the player touches
## such a wall, so it never blocks an exit.
static func exit_step(local: Vector2) -> Vector2i:
	if local.x >= 943.0:
		return Vector2i.RIGHT
	if local.x < 17.0:
		return Vector2i.LEFT
	if local.y >= 742.0:
		return Vector2i.DOWN
	if local.y < 27.0:
		return Vector2i.UP
	return Vector2i.ZERO


## Where the player appears in the next room after leaving in direction step.
static func entry_position(step: Vector2i, local: Vector2) -> Vector2:
	match step:
		Vector2i.RIGHT:
			return Vector2(17.0, local.y)
		Vector2i.LEFT:
			return Vector2(943.0, local.y)
		Vector2i.DOWN:
			return Vector2(local.x, 16.0)
		_:
			return Vector2(local.x, 720.0)


## Instantiates the room at a grid position, placed in world space, with its
## monsters wired to the campaign and any collected powerup removed.
func load_room(at: Vector2i) -> Node2D:
	var loaded: Node2D = load("res://world/rooms/room_%d_%d.tscn" % [at.x, at.y]).instantiate()
	loaded.position = Vector2(at) * ROOM_SIZE
	for entity in loaded.get_node("Entities").get_children():
		if entity.is_powerup and progress.powerups_taken.has(at):
			entity.free()
			continue
		entity.shot_fired.connect(_on_shot_fired)
		entity.save_requested.connect(_on_save_requested)
	return loaded


func _enter_room(next: Vector2i, step: Vector2i, local: Vector2) -> void:
	_sliding = true
	_exits_armed = false
	var old_room := room
	grid = next
	room = load_room(grid)
	_world.add_child(room)
	_clear_shots()
	_player.global_position = room.position + entry_position(step, local)
	_note_room()

	get_tree().paused = true
	var tween := create_tween()
	tween.set_pause_mode(Tween.TWEEN_PAUSE_PROCESS)
	tween.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tween.tween_property(_camera, "position", room.position + VIEW_CENTER, SLIDE_TIME)
	await tween.finished
	old_room.queue_free()
	get_tree().paused = false
	_sliding = false


## Reloads the checkpoint room and puts a revived player at its start.
func _respawn() -> void:
	_clear_shots()
	_world.remove_child(room)
	room.queue_free()
	grid = progress.checkpoint
	room = load_room(grid)
	_world.add_child(room)
	_player.revive()
	_place_player_at_start()
	_note_room()


func _place_player_at_start() -> void:
	var start: Vector2 = room.player_start if room.has_player_start else ROOM_SIZE / 2.0
	_player.global_position = room.position + start
	_camera.position = room.position + VIEW_CENTER
	_exits_armed = false


## Records the current room on the map and writes the slot, so the explored
## map survives quitting. Stats and checkpoint change only at save events.
func _note_room() -> void:
	progress.visited[grid] = true
	for entity in room.get_node("Entities").get_children():
		if entity.is_save_point:
			progress.save_points[grid] = true
	_mini_map.show_progress(progress, grid)
	_write_slot()


func _write_slot() -> void:
	if slot > 0:
		SaveGame.write(slot, progress)


func _clear_shots() -> void:
	for shot in _shots.get_children():
		shot.queue_free()


func _set_pause_menu(open: bool) -> void:
	_pause_menu.visible = open
	get_tree().paused = open
	if open:
		_pause_menu.open(progress, grid)


func _quit_to_title() -> void:
	_set_pause_menu(false)
	quit_to_title.emit()


func _on_shot_fired(shot: RigidBody2D) -> void:
	shot.bounds = Rect2(room.position, ROOM_SIZE)
	_shots.add_child(shot)


## A save point was activated or a powerup collected in the current room.
func _on_save_requested(source: Node) -> void:
	progress.checkpoint = grid
	_player.hp = _player.max_hp
	if source.is_powerup:
		progress.powerups_taken[grid] = true
	progress.max_hp = _player.max_hp
	progress.max_fuel = _player.jetpack.max_fuel
	progress.gun_level = _player.gun_level
	progress.artifacts = _player.artifacts
	_write_slot()
	_hud.show_saved()
```

- [ ] **Step 4: Rewrite the campaign scene**

Replace `scenes/campaign.tscn` with:

```
[gd_scene load_steps=6 format=3]

[ext_resource type="Script" path="res://scenes/campaign.gd" id="1"]
[ext_resource type="PackedScene" path="res://entities/player/player.tscn" id="2"]
[ext_resource type="Script" path="res://ui/hud.gd" id="3"]
[ext_resource type="Script" path="res://ui/map_view.gd" id="4"]
[ext_resource type="Script" path="res://ui/pause_menu.gd" id="5"]

[node name="Campaign" type="Node2D"]
process_mode = 3
script = ExtResource("1")

[node name="World" type="Node2D" parent="."]
process_mode = 1

[node name="Player" parent="." instance=ExtResource("2")]
process_mode = 1

[node name="Shots" type="Node2D" parent="."]
process_mode = 1

[node name="Camera2D" type="Camera2D" parent="."]

[node name="Hud" type="CanvasLayer" parent="."]

[node name="Strip" type="Control" parent="Hud"]
offset_right = 1024.0
offset_bottom = 768.0
mouse_filter = 2
script = ExtResource("3")

[node name="MiniMap" type="Control" parent="Hud/Strip"]
offset_left = 962.0
offset_top = 4.0
offset_right = 1022.0
offset_bottom = 64.0
mouse_filter = 2
script = ExtResource("4")

[node name="PauseMenu" type="CanvasLayer" parent="."]
layer = 2
visible = false
script = ExtResource("5")
```

- [ ] **Step 5: Run the test to verify it passes**

```bash
"$GODOT" --headless --path . --script res://tools/test_campaign.gd 2>&1 | tee /tmp/out.txt | grep -E "FAIL:|test passed|test FAILED"; grep -c "SCRIPT ERROR" /tmp/out.txt
```

Expected: `campaign test passed` and `0`.

- [ ] **Step 6: Commit**

```bash
git add scenes tools/test_campaign.gd
git commit -m "Campaign records progress, saves, and has a HUD, pause menu and win"
```

---

### Task 5: Title, image screens and the main flow

**Files:**
- Create: `tools/test_main.gd`
- Create: `scenes/image_screen.gd`, `scenes/title.gd`, `scenes/main.gd`, `scenes/main.tscn`
- Modify: `project.godot`

- [ ] **Step 1: Write the failing test**

Create `tools/test_main.gd`:

```gdscript
extends SceneTree
## Walks the screen flow: title, new game, intro, campaign, quit, continue,
## delete, ending.
## Run: godot --headless --path . --script res://tools/test_main.gd

const Progress := preload("res://save/progress.gd")
const SaveGame := preload("res://save/save_game.gd")
const TitleScript := preload("res://scenes/title.gd")
const ImageScreenScript := preload("res://scenes/image_screen.gd")
const CampaignScript := preload("res://scenes/campaign.gd")

var _failures := 0
var _main: Node


func _initialize() -> void:
	_run()


func _run() -> void:
	SaveGame.directory = "user://test_saves/"
	DirAccess.make_dir_recursive_absolute(SaveGame.directory)
	for slot: int in SaveGame.SLOTS:
		SaveGame.delete(slot)
	await process_frame
	_main = load("res://scenes/main.tscn").instantiate()
	root.add_child(_main)
	await _frames(3)

	_expect(_is(TitleScript), "the game opens on the title")
	_expect(_button("Slot1New") != null, "an empty slot offers New Game")
	_expect(_button("Slot1Continue") == null, "an empty slot does not offer Continue")

	# New game: writes the slot, shows the intro, then the campaign.
	_button("Slot1New").pressed.emit()
	await _frames(3)
	_expect(_is(ImageScreenScript), "New Game shows the intro")
	_expect(SaveGame.exists(1), "New Game writes the slot at once")
	_press_key(KEY_SPACE)
	await _frames(3)
	_expect(_is(CampaignScript), "dismissing the intro starts the campaign")
	if _is(CampaignScript):
		_expect(_main.screen.slot == 1, "the campaign uses the chosen slot")
		_expect(_main.screen.grid == Vector2i(4, 2), "a new game starts in room 4,2")
		_main.screen.quit_to_title.emit()
	await _frames(3)

	# Back on the title the slot is in use.
	_expect(_is(TitleScript), "quitting returns to the title")
	_expect(_button("Slot1Continue") != null and _button("Slot1Delete") != null, "a used slot offers Continue and Delete")
	_expect(_button("Slot1New") == null, "a used slot does not offer New Game")

	# Delete.
	_button("Slot1Delete").pressed.emit()
	await _frames(3)
	_expect(not SaveGame.exists(1), "Delete removes the slot file")
	_expect(_button("Slot1New") != null and _button("Slot1Delete") == null, "a deleted slot offers New Game again")

	# Continue goes straight to the campaign at the saved checkpoint.
	var progress := Progress.new()
	progress.checkpoint = Vector2i(5, 2)
	progress.max_hp = 7
	SaveGame.write(2, progress)
	_main.show_title()
	await _frames(3)
	_button("Slot2Continue").pressed.emit()
	await _frames(3)
	_expect(_is(CampaignScript), "Continue starts the campaign without the intro")
	if _is(CampaignScript):
		_expect(_main.screen.grid == Vector2i(5, 2), "Continue starts at the checkpoint")
		_expect(_main.screen.get_node("Player").max_hp == 7, "Continue restores stats")
		# Winning shows the ending, then the title.
		_main.screen.won.emit()
	await _frames(3)
	_expect(_is(ImageScreenScript), "winning shows the ending")
	_press_key(KEY_SPACE)
	await _frames(3)
	_expect(_is(TitleScript), "dismissing the ending returns to the title")
	_expect(not paused, "the tree is not left paused")

	for slot: int in SaveGame.SLOTS:
		SaveGame.delete(slot)
	print("main test passed" if _failures == 0 else "main test FAILED: %d failures" % _failures)
	quit(1 if _failures > 0 else 0)


func _is(script: Script) -> bool:
	return _main.screen != null and _main.screen.get_script() == script


func _button(node_name: String) -> Button:
	return _main.screen.find_child(node_name, true, false) as Button


func _press_key(keycode: Key) -> void:
	var event := InputEventKey.new()
	event.keycode = keycode
	event.physical_keycode = keycode
	event.pressed = true
	Input.parse_input_event(event)


func _frames(count: int) -> void:
	for i in count:
		await physics_frame


func _expect(condition: bool, message: String) -> void:
	if not condition:
		_failures += 1
		printerr("FAIL: " + message)
```

- [ ] **Step 2: Run it to verify it fails**

```bash
"$GODOT" --headless --path . --script res://tools/test_main.gd 2>&1 | grep -c "Preload file"
```

Expected: `2` (the title and image screen scripts are missing).

- [ ] **Step 3: Image screen**

Create `scenes/image_screen.gd`:

```gdscript
extends Control
## A full-screen image, dismissed by any key, click or gamepad button.
## Set texture before adding it to the tree.

signal dismissed

var texture: Texture2D

var _done := false


func _ready() -> void:
	var image := TextureRect.new()
	image.texture = texture
	image.scale = Vector2(2, 2)
	image.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(image)


func _unhandled_input(event: InputEvent) -> void:
	if _done or event.is_echo() or not event.is_pressed():
		return
	if event is InputEventKey or event is InputEventMouseButton or event is InputEventJoypadButton:
		_done = true
		dismissed.emit()
```

- [ ] **Step 4: Title**

Create `scenes/title.gd`:

```gdscript
extends Control
## The title screen: a New Game button for each empty save slot, Continue and
## Delete for each used one, and sound and fullscreen toggles.

signal new_game(slot: int)
signal continue_game(slot: int)

const UiKit := preload("res://ui/ui_kit.gd")
const SaveGame := preload("res://save/save_game.gd")
const Background := preload("res://assets/sprites/titleTerrainSmall.png")
const TitleSheet := preload("res://assets/sprites/extranautTitleAnimated.png")
const KopaStrip := preload("res://assets/sprites/kopa.png")
const MattStrip := preload("res://assets/sprites/matt.png")
const OptionsSheet := preload("res://assets/sprites/options.png")

const CENTER_X := 512.0
const SLOTS_TOP := 384.0
const SLOT_SPACING := 60.0
const SMALL_BUTTON := Vector2(140, 20)
const WIDE_BUTTON := Vector2(240, 20)
const TITLE_FRAME_TIME := 0.06
const TOGGLE_SIZE := Vector2(34, 34)
const ICON_SOUND_OFF := Rect2(0, 0, 16, 16)
const ICON_SOUND_ON := Rect2(16, 0, 16, 16)
const ICON_WINDOWED := Rect2(0, 16, 16, 16)
const ICON_FULLSCREEN := Rect2(16, 16, 16, 16)

var _slots: Control
var _title: Sprite2D
var _title_elapsed := 0.0
var _sound_button: Button
var _fullscreen_button: Button


func _ready() -> void:
	_add_image(Background, Vector2.ZERO, 2.0)
	_title = Sprite2D.new()
	_title.texture = TitleSheet
	_title.hframes = 4
	_title.centered = false
	_title.scale = Vector2(4, 4)
	_title.position = Vector2(250, 50)
	add_child(_title)
	_add_image(KopaStrip, Vector2(80, 250), 2.0)
	_add_image(MattStrip, Vector2(300, 300), 2.0)

	_slots = Control.new()
	add_child(_slots)
	_build_slots()

	_sound_button = _add_toggle(Vector2(0, 734), _toggle_sound)
	_fullscreen_button = _add_toggle(Vector2(33, 734), _toggle_fullscreen)
	_refresh_toggles()
	var version := UiKit.make_label("Version 2.0")
	version.position = Vector2(76, 742)
	add_child(version)


func _process(delta: float) -> void:
	_title_elapsed += delta
	if _title_elapsed >= TITLE_FRAME_TIME:
		_title_elapsed -= TITLE_FRAME_TIME
		_title.frame = (_title.frame + 1) % _title.hframes


func _build_slots() -> void:
	for child in _slots.get_children():
		_slots.remove_child(child)
		child.free()
	for slot: int in SaveGame.SLOTS:
		var y: float = SLOTS_TOP + SLOT_SPACING * (slot - 1)
		if SaveGame.read(slot) != null:
			var resume := _add_slot_button("Slot%dContinue" % slot, "Continue Game %d" % slot, Vector2(CENTER_X - SMALL_BUTTON.x - 25.0, y), SMALL_BUTTON)
			resume.pressed.connect(func() -> void: continue_game.emit(slot))
			var delete := _add_slot_button("Slot%dDelete" % slot, "Delete Game %d" % slot, Vector2(CENTER_X + 25.0, y), SMALL_BUTTON)
			delete.pressed.connect(_delete_slot.bind(slot))
		else:
			var fresh := _add_slot_button("Slot%dNew" % slot, "New Game %d - Planet Zorta" % slot, Vector2(CENTER_X - WIDE_BUTTON.x / 2.0, y), WIDE_BUTTON)
			fresh.pressed.connect(func() -> void: new_game.emit(slot))
	(_slots.get_child(0) as Button).grab_focus.call_deferred()


func _delete_slot(slot: int) -> void:
	SaveGame.delete(slot)
	# Deferred: rebuilding frees the button whose signal is being handled.
	_build_slots.call_deferred()


func _add_slot_button(node_name: String, text: String, at: Vector2, button_size: Vector2) -> Button:
	var button := UiKit.make_button(text, button_size)
	button.name = node_name
	button.position = at
	_slots.add_child(button)
	return button


func _add_image(image: Texture2D, at: Vector2, image_scale: float) -> void:
	var rect := TextureRect.new()
	rect.texture = image
	rect.position = at
	rect.scale = Vector2(image_scale, image_scale)
	rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(rect)


func _add_toggle(at: Vector2, on_pressed: Callable) -> Button:
	var button := UiKit.make_button("", TOGGLE_SIZE)
	button.position = at
	button.expand_icon = true
	button.pressed.connect(on_pressed)
	add_child(button)
	return button


func _toggle_sound() -> void:
	AudioServer.set_bus_mute(0, not AudioServer.is_bus_mute(0))
	_refresh_toggles()


func _toggle_fullscreen() -> void:
	var fullscreen := DisplayServer.window_get_mode() == DisplayServer.WINDOW_MODE_FULLSCREEN
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED if fullscreen else DisplayServer.WINDOW_MODE_FULLSCREEN)
	_refresh_toggles()


func _refresh_toggles() -> void:
	_sound_button.icon = _icon(ICON_SOUND_OFF if AudioServer.is_bus_mute(0) else ICON_SOUND_ON)
	var fullscreen := DisplayServer.window_get_mode() == DisplayServer.WINDOW_MODE_FULLSCREEN
	_fullscreen_button.icon = _icon(ICON_FULLSCREEN if fullscreen else ICON_WINDOWED)


func _icon(region: Rect2) -> AtlasTexture:
	var icon := AtlasTexture.new()
	icon.atlas = OptionsSheet
	icon.region = region
	return icon
```

- [ ] **Step 5: Main**

Create `scenes/main.gd`:

```gdscript
extends Node
## The screen flow. Shows one screen at a time: the title, an image screen
## (intro or ending) or the campaign.
## Development options after "--" on the command line:
##   --room=X,Y   skip the title and start an unsaved campaign in that room
##   --shot=PATH  save a screenshot after one second and quit

const Controls := preload("res://input/controls.gd")
const Progress := preload("res://save/progress.gd")
const SaveGame := preload("res://save/save_game.gd")
const TitleScript := preload("res://scenes/title.gd")
const ImageScreenScript := preload("res://scenes/image_screen.gd")
const CampaignScene := preload("res://scenes/campaign.tscn")
const IntroImage := preload("res://assets/sprites/intro.png")
const EndingImage := preload("res://assets/sprites/ending.png")

## The screen currently shown.
var screen: Node


func _ready() -> void:
	Controls.setup()
	var shot_path := ""
	var skip_title := false
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--room="):
			skip_title = true
		elif arg.begins_with("--shot="):
			shot_path = arg.trim_prefix("--shot=")
	if skip_title:
		_start_campaign(0)
	else:
		show_title()
	if shot_path != "":
		await get_tree().create_timer(1.0).timeout
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png(shot_path)
		get_tree().quit()


func show_title() -> void:
	var title := Control.new()
	title.set_script(TitleScript)
	title.new_game.connect(_on_new_game, CONNECT_DEFERRED)
	title.continue_game.connect(_start_campaign, CONNECT_DEFERRED)
	_show(title)


func _on_new_game(slot: int) -> void:
	SaveGame.write(slot, Progress.new())
	_show_image(IntroImage, _start_campaign.bind(slot))


## slot 0 plays without saving.
func _start_campaign(slot: int) -> void:
	var campaign := CampaignScene.instantiate()
	campaign.slot = slot
	if slot > 0:
		campaign.progress = SaveGame.read(slot)
	campaign.won.connect(_show_image.bind(EndingImage, show_title), CONNECT_DEFERRED)
	campaign.quit_to_title.connect(show_title, CONNECT_DEFERRED)
	_show(campaign)


func _show_image(image: Texture2D, then: Callable) -> void:
	var image_screen := Control.new()
	image_screen.set_script(ImageScreenScript)
	image_screen.texture = image
	image_screen.dismissed.connect(then, CONNECT_DEFERRED)
	_show(image_screen)


func _show(next: Node) -> void:
	if screen != null:
		remove_child(screen)
		screen.queue_free()
	get_tree().paused = false
	screen = next
	add_child(screen)
```

Create `scenes/main.tscn`:

```
[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scenes/main.gd" id="1"]

[node name="Main" type="Node"]
process_mode = 3
script = ExtResource("1")
```

- [ ] **Step 6: Make it the main scene**

In `project.godot`, change the `run/main_scene` line to:

```ini
run/main_scene="res://scenes/main.tscn"
```

- [ ] **Step 7: Run the test to verify it passes**

```bash
"$GODOT" --headless --path . --import 2>&1 | grep -i -E "parse error"
"$GODOT" --headless --path . --script res://tools/test_main.gd 2>&1 | tee /tmp/out.txt | grep -E "FAIL:|test passed|test FAILED"; grep -c "SCRIPT ERROR" /tmp/out.txt
```

Expected: `main test passed` and `0`.

- [ ] **Step 8: Look at the screens**

```bash
mkdir -p ../extranaut-shots
SHOTS="$(cd .. && pwd -W)/extranaut-shots"
"$GODOT" --path . -- --shot="$SHOTS/title.png" 2>&1 | grep -i error
"$GODOT" --path . -- --room=4,2 --shot="$SHOTS/hud.png" 2>&1 | grep -i error
```

Open both. Check on the title: background, animated logo, both credit strips, three New Game buttons with readable text, the two toggle icons and the version label. Check on the HUD shot: five HP pips and four fuel pips stacked from the bottom right, the minimap top right with one lit cell, and no leftover placeholder text.

- [ ] **Step 9: Run every check**

```bash
python -m unittest discover -s tools -p "test_*.py" 2>&1 | tail -1
for t in smoke_test test_jetpack test_save test_monsters test_campaign test_main; do "$GODOT" --headless --path . --script res://tools/$t.gd 2>&1 | tee /tmp/out.txt | grep -E "test passed|test FAILED|FAIL:"; grep -c "SCRIPT ERROR" /tmp/out.txt; done
```

Expected: `OK`, then six `passed` lines each followed by `0`.

- [ ] **Step 10: Commit**

```bash
git add scenes tools/test_main.gd project.godot
git commit -m "Add the title, intro, ending and main screen flow"
```

---

## Done when

- Every check in Task 5 Step 9 passes with no script errors.
- Running the project opens the title. New Game shows the intro, then the campaign; the slot then offers Continue and Delete.
- Shooting a save point or collecting a powerup shows SAVED and survives quitting and continuing.
- The minimap fills in as rooms are entered and marks rooms with save points; the pause menu shows it larger.
- P, Enter or Start pauses; Resume and Quit to Title work.
- Falling out of the bottom of the world shows the ending and returns to the title.

## Changes made during execution

1. **Tests act between frames after input.** Godot delivers input once per rendered frame, so waiting a fixed number of physics frames after a simulated key press was flaky under load. Emitting a button's `pressed` signal from inside a physics tick also made the engine log an error when the handler unpaused the tree. Both tests now use a `_settle()` helper that waits for rendered frames and ends between frames. The committed test files supersede the blocks above.
2. **Test commands use `timeout`.** A script error inside a test coroutine stops it before its `quit()` call, leaving headless Godot running forever. Run tests as `timeout 200 "$GODOT" ...`.
3. **Typed loop variable in `scenes/title.gd`.** `for slot: int in SaveGame.SLOTS` and `var y: float`, because the element type of an untyped constant array cannot be inferred.

