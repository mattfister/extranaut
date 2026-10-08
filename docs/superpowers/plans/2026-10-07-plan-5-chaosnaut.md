# Extranaut Port, Plan 5: Chaosnaut

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The Chaosnaut wave-survival mode is playable from the title screen, with a game-over screen showing the wave reached, kills and the stored best.

**Architecture:** A `Chaosnaut` scene is a single walled arena built in code. It reuses the player, hover blocks, shots, particle field, screen effects, HUD and pause menu from the campaign, adds one new monster (ChaosBot), and runs a wave timer. A small `ChaosScore` helper stores the best result as JSON beside the save slots. `Main` gains one more screen.

**Tech Stack:** Godot 4.7 GDScript, headless `--script` tests.

**Spec:** `docs/superpowers/specs/2026-10-07-extranaut-godot-port-design.md`

**This is plan 5 of 7**, executed after plan 6.

---

## Conventions for every task

- Shell is Git Bash. Run commands from the repository root.
- Godot binary:

```bash
GODOT="/c/Users/mattf/Desktop/godot47/Godot_v4.7-stable_win64_console.exe"
```

- GDScript files are indented with tabs.
- Work on branch `plan-5-chaosnaut`.
- Commit messages end with the attribution trailer lines in force for the session.
- Every whole-file code block is introduced by ``Create `path`:`` or ``Replace `path` with:``. Write the block to that path exactly.
- Run every Godot test as `timeout 200 "$GODOT" ...`.
- Count errors with `grep -E 'SCRIPT ERROR|^ERROR' | grep -v -c 'at exit'`; the count must be 0.
- Audio, particles and screen effects are reached through groups (`"audio"`, `"particle_field"`, `"screen_fx"`), never through the `Audio` global.

## Facts from the original

Arena (`chaosnautRoom.py`): one 960x768 room bounded by four walls, with no tiles. 40 HoverBlocks at random positions, x from 128 to 800 and y from 0 to 736. Whenever fewer than 40 remain, new ones are added. The player starts at (32, 704), has its fuel refilled every frame, and has gun level 3. Music is `chaosNaut`.

Waves: the first wave arrives after 2 s and then one every 10 s. Each plays `newWave`, increases the wave number, and spawns floor(wave / 4) + 1 ChaosBots at x = 928 with y from 0 to 736.

ChaosBot (`monster.py`): radius 16, mass 20, no gravity, rotation locked, 1 HP, hurts on touch, explodes into 40 particles with the `explode` sound, and trails exhaust. Sheet `bots`, row 1, or row 2 when angry. Every frame its horizontal velocity is set to -100, or -300 when angry. At intervals of 0.5 to 1 s (the first after up to 0.1 s) it gets an impulse of 0 horizontally, or 1000 when angry, and -3000 to 3000 vertically. A bot whose x reaches 16 or less is moved to x = 928 and becomes angry.

Game over: when the player's death pause ends, the original returned to the title. It tracked the wave number and a kill count but showed neither, and the kill count was never incremented.

## Additions

- A game-over screen with wave reached, kills and the best result so far.
- Kills are counted.
- The best result (highest wave, then most kills) is stored in `chaosnaut.json` beside the save slots.
- The pause menu works here, without its map.

## File structure

| Path | Responsibility |
| --- | --- |
| `entities/monsters/chaos_bot.gd` | ChaosBot behaviour |
| `tools/make_monster_scenes.py` | Adds the chaos_bot row |
| `entities/monsters/monster.gd` | Adds a `died` signal |
| `save/chaos_score.gd` | Best Chaosnaut result on disk |
| `scenes/chaosnaut.gd`, `chaosnaut.tscn` | The arena, waves and game over |
| `ui/pause_menu.gd` | Optional map |
| `scenes/title.gd`, `scenes/main.gd` | Chaosnaut button and screen |
| `tools/test_chaosnaut.gd`, `tools/test_main.gd` | Tests |

---

### Task 1: ChaosBot, the died signal and the score file

**Files:**
- Create: `tools/test_chaosnaut.gd`
- Create: `entities/monsters/chaos_bot.gd`
- Create: `save/chaos_score.gd`
- Modify: `entities/monsters/monster.gd`, `tools/make_monster_scenes.py`

- [ ] **Step 1: Write the failing test**

The arena sections fail until Task 2.

Create `tools/test_chaosnaut.gd`:

```gdscript
extends SceneTree
## Tests for ChaosBot, ChaosScore and the Chaosnaut arena.
## Run: godot --headless --path . --script res://tools/test_chaosnaut.gd

const SaveGame := preload("res://save/save_game.gd")
const ChaosScore := preload("res://save/chaos_score.gd")

var _failures := 0


func _initialize() -> void:
	_run()


func _run() -> void:
	await process_frame
	SaveGame.directory = "user://test_saves/"
	DirAccess.make_dir_recursive_absolute(SaveGame.directory)
	_test_score()
	await _test_chaos_bot()
	await _test_arena()
	ChaosScore.clear()
	print("chaosnaut test passed" if _failures == 0 else "chaosnaut test FAILED: %d failures" % _failures)
	quit(1 if _failures > 0 else 0)


func _test_score() -> void:
	ChaosScore.clear()
	var none := ChaosScore.read()
	_expect(none.wave == 0 and none.kills == 0, "no best result at first")
	_expect(ChaosScore.submit(3, 5), "the first result is the best")
	_expect(not ChaosScore.submit(2, 9), "a lower wave is not better, whatever the kills")
	_expect(not ChaosScore.submit(3, 5), "an equal result is not better")
	_expect(ChaosScore.submit(3, 6), "more kills on the same wave is better")
	var best := ChaosScore.read()
	_expect(best.wave == 3 and best.kills == 6, "the best result is stored")


func _test_chaos_bot() -> void:
	var holder := Node2D.new()
	root.add_child(holder)
	var bot: RigidBody2D = load("res://entities/monsters/chaos_bot.tscn").instantiate()
	bot.position = Vector2(500, 300)
	holder.add_child(bot)
	var deaths := [0]
	bot.died.connect(func() -> void: deaths[0] += 1)
	await _frames(20)
	_expect(absf(bot.linear_velocity.x + 100.0) < 1.0, "a chaos bot drifts left at 100, got %.1f" % bot.linear_velocity.x)
	_expect(bot.sprite.frame_coords.y == 1, "a calm chaos bot uses sprite row 1")
	_expect(absf(bot.position.y - 300.0) < 200.0, "a chaos bot is not pulled down by gravity")
	bot.angry = true
	await _frames(5)
	_expect(absf(bot.linear_velocity.x + 300.0) < 1.0, "an angry chaos bot drifts left at 300")
	_expect(bot.sprite.frame_coords.y == 2, "an angry chaos bot uses sprite row 2")
	bot.hit()
	_expect(deaths[0] == 1, "a dying monster emits died")
	root.remove_child(holder)
	holder.free()


func _test_arena() -> void:
	ChaosScore.clear()
	var audio: Node = root.get_node("Audio")
	var arena: Node2D = load("res://scenes/chaosnaut.tscn").instantiate()
	root.add_child(arena)
	var player: RigidBody2D = arena.get_node("Player")
	await _frames(5)

	_expect(arena.block_count() == 40, "the arena starts with 40 hover blocks, got %d" % arena.block_count())
	_expect(arena.bot_count() == 0 and arena.wave == 0, "no bots before the first wave")
	_expect(player.gun_level == 3, "the player has gun level 3")
	_expect(player.position.distance_to(Vector2(32, 704)) < 60.0, "the player starts bottom left, at %s" % player.position)
	_expect(audio.current_music() == "chaosNaut", "the arena plays its music")

	# Fuel never runs out.
	Input.action_press("jetpack")
	await _frames(60)
	Input.action_release("jetpack")
	_expect(player.jetpack.fuel > player.jetpack.max_fuel - 200.0, "fuel is refilled every frame")

	# Waves.
	var before := Time.get_ticks_msec()
	arena.next_wave_in = 0.01
	await _frames(3)
	_expect(arena.wave == 1 and arena.bot_count() == 1, "wave 1 spawns one bot, got wave %d and %d bots" % [arena.wave, arena.bot_count()])
	_expect(audio.last_played_msec("newWave") >= before, "a wave plays newWave")
	_expect(arena.next_wave_in > 9.0, "the next wave is 10 s away")
	arena.wave = 3
	arena.next_wave_in = 0.01
	await _frames(3)
	_expect(arena.wave == 4 and arena.bot_count() == 3, "wave 4 spawns two bots, got %d in total" % arena.bot_count())

	# A bot reaching the left edge wraps round and turns angry.
	var bot: RigidBody2D = arena.bots()[0]
	bot.global_position = Vector2(10, 300)
	await _frames(3)
	_expect(bot.global_position.x > 800.0 and bot.angry, "a bot at the left edge wraps to the right and turns angry")

	# Kills are counted and blocks are replaced.
	bot.hit()
	_expect(arena.kills == 1, "killing a bot counts")
	arena.blocks()[0].hit()
	await _frames(3)
	_expect(arena.block_count() == 40, "a destroyed block is replaced")
	_expect(arena.kills == 1, "destroying a block is not a kill")

	# Game over.
	var game_over: CanvasLayer = arena.get_node("GameOver")
	_expect(not game_over.visible, "no game-over screen while alive")
	player.revive()
	player.hp = 1
	player.hit()
	await _frames(130)
	await _settle()
	_expect(game_over.visible and paused, "the game-over screen shows after the death pause")
	_expect(game_over.get_node("Stats").text.contains("Wave 4"), "the game-over screen shows the wave, text: %s" % game_over.get_node("Stats").text)
	_expect(ChaosScore.read().wave == 4 and ChaosScore.read().kills == 1, "the result is stored as the best")
	var finished := [0]
	arena.finished.connect(func() -> void: finished[0] += 1)
	game_over.get_node("Back").pressed.emit()
	await _settle()
	_expect(finished[0] == 1, "Back to Title finishes the mode")
	_expect(not paused, "leaving unpauses the tree")
	root.remove_child(arena)
	arena.free()


## Waits for deferred work, ending between frames, where real button presses
## arrive.
func _settle() -> void:
	await process_frame
	await process_frame
	await physics_frame
	await process_frame


func _frames(count: int) -> void:
	for i in count:
		await physics_frame


func _expect(condition: bool, message: String) -> void:
	if not condition:
		_failures += 1
		printerr("FAIL: " + message)
```

- [ ] **Step 2: The died signal**

In `entities/monsters/monster.gd`, add after the `save_requested` signal:

```gdscript
## Emitted once when the monster dies, before it is freed.
signal died
```

and in `die`, add directly before the line `queue_free()`:

```gdscript
	died.emit()
```

- [ ] **Step 3: ChaosBot**

Create `entities/monsters/chaos_bot.gd`:

```gdscript
extends "res://entities/monsters/monster.gd"
## Chaosnaut's enemy. Drifts left at a fixed speed with random vertical
## kicks. The arena makes it angry, and faster, when it reaches the left edge.

const SPEED := 100.0
const ANGRY_SPEED := 300.0
const KICK := 3000.0
const ANGRY_PUSH := 1000.0
const CALM_ROW := 1
const ANGRY_ROW := 2

var angry := false

var _kick_timer := randf_range(0.0, 0.1)


func _integrate_forces(state: PhysicsDirectBodyState2D) -> void:
	var velocity := state.linear_velocity
	velocity.x = -ANGRY_SPEED if angry else -SPEED
	state.linear_velocity = velocity


func _behave(delta: float, _player: Node2D) -> void:
	exhaust(delta, 14.0, 5)
	sprite.frame_coords.y = ANGRY_ROW if angry else CALM_ROW
	_kick_timer -= delta
	if _kick_timer < 0.0:
		_kick_timer = randf_range(0.5, 1.0)
		apply_central_impulse(Vector2(ANGRY_PUSH if angry else 0.0, randf_range(-KICK, KICK)))
```

In `tools/make_monster_scenes.py`, add this row to `MONSTERS` directly after the `head_boss` row:

```python
    monster("chaos_bot", "chaos_bot", "animations/bots", frame=(0, 1), gravity=0.0,
            damages_player_on_touch=True, **BOT),
```

Regenerate:

```bash
python tools/make_monster_scenes.py
```

Expected: `Wrote 26 monster scenes`.

- [ ] **Step 4: ChaosScore**

Create `save/chaos_score.gd`:

```gdscript
extends RefCounted
## The best Chaosnaut result, stored beside the save slots.

const SaveGame := preload("res://save/save_game.gd")
const FILE_NAME := "chaosnaut.json"


static func path() -> String:
	return SaveGame.directory + FILE_NAME


## Returns {"wave": int, "kills": int}, zeros if nothing is stored.
static func read() -> Dictionary:
	var best := {"wave": 0, "kills": 0}
	if not FileAccess.file_exists(path()):
		return best
	var json := JSON.new()
	if json.parse(FileAccess.get_file_as_string(path())) != OK or not json.data is Dictionary:
		return best
	best.wave = int(json.data.get("wave", 0))
	best.kills = int(json.data.get("kills", 0))
	return best


## Stores the result if it beats the best: a higher wave, or the same wave
## with more kills. Returns true if it did.
static func submit(wave: int, kills: int) -> bool:
	var best := read()
	if wave < best.wave or (wave == best.wave and kills <= best.kills):
		return false
	var file := FileAccess.open(path(), FileAccess.WRITE)
	if file == null:
		push_warning("could not write %s" % path())
		return false
	file.store_string(JSON.stringify({"wave": wave, "kills": kills}))
	return true


static func clear() -> void:
	if FileAccess.file_exists(path()):
		DirAccess.remove_absolute(path())
```

- [ ] **Step 5: Run the first two sections**

```bash
timeout 200 "$GODOT" --headless --path . --script res://tools/test_chaosnaut.gd 2>&1 | grep -E "FAIL:" | head -5
timeout 200 "$GODOT" --headless --path . --script res://tools/test_monsters.gd 2>&1 | grep -E "test passed|test FAILED"
```

Expected: no `FAIL:` lines about the score or the chaos bot (the arena section cannot load its scene yet), and `monster test passed`.

- [ ] **Step 6: Commit**

```bash
git add entities/monsters save/chaos_score.gd tools
git commit -m "Add ChaosBot, a died signal and the Chaosnaut score file"
```

---

### Task 2: The arena

**Files:**
- Modify: `ui/pause_menu.gd`
- Create: `scenes/chaosnaut.gd`, `scenes/chaosnaut.tscn`

- [ ] **Step 1: Make the pause menu's map optional**

In `ui/pause_menu.gd`, add after the `BUTTON_SIZE` constant:

```gdscript
## Set false before adding to the tree for modes that have no map.
@export var show_map := true
```

In `_ready`, add directly after the line `add_child(_map)`:

```gdscript
	_map.visible = show_map
```

Replace the `open` function with:

```gdscript
## progress is a save/progress.gd object, or null when there is no map.
func open(progress: RefCounted, current: Vector2i) -> void:
	if progress != null:
		_map.show_progress(progress, current)
	_resume.grab_focus()
```

- [ ] **Step 2: The arena script**

Create `scenes/chaosnaut.gd`:

```gdscript
extends Node2D
## Chaosnaut: survive waves of ChaosBots in one walled room full of hover
## blocks, with unlimited fuel.

## The player chose to go back to the title, after dying or from the pause menu.
signal finished

const Controls := preload("res://input/controls.gd")
const ChaosScore := preload("res://save/chaos_score.gd")
const UiKit := preload("res://ui/ui_kit.gd")
const HoverBlockScene := preload("res://entities/monsters/hover_block.tscn")
const ChaosBotScene := preload("res://entities/monsters/chaos_bot.tscn")

const ROOM_SIZE := Vector2(960, 768)
const VIEW_CENTER := Vector2(512, 384)
const WALL_RADIUS := 0.5
const PLAYER_START := Vector2(32, 704)
const GUN_LEVEL := 3
const BLOCK_COUNT := 40
const BLOCK_X_MIN := 128.0
const BLOCK_X_MAX := 800.0
const SPAWN_Y_MAX := 736.0
const BOT_SPAWN_X := 928.0
## A bot at or left of this wraps to BOT_SPAWN_X and turns angry.
const BOT_WRAP_X := 16.0
const FIRST_WAVE_DELAY := 2.0
const WAVE_INTERVAL := 10.0

var wave := 0
var kills := 0
## Seconds until the next wave.
var next_wave_in := FIRST_WAVE_DELAY

var _over := false

@onready var _entities: Node2D = $Entities
@onready var _player: RigidBody2D = $Player
@onready var _shots: Node2D = $Shots
@onready var _camera: Camera2D = $Camera2D
@onready var _hud: Control = $Hud/Strip
@onready var _wave_label: Label = $Hud/Wave
@onready var _screen_fx: CanvasLayer = $ScreenFx
@onready var _pause_menu: CanvasLayer = $PauseMenu
@onready var _game_over: CanvasLayer = $GameOver


func _ready() -> void:
	Controls.setup()
	_build_walls()
	_build_game_over()
	_wave_label.add_theme_font_override("font", UiKit.FONT)
	_wave_label.add_theme_font_size_override("font_size", UiKit.FONT_SIZE)
	_camera.position = VIEW_CENTER
	_screen_fx.camera = _camera
	_player.position = PLAYER_START
	_player.gun_level = GUN_LEVEL
	_player.shot_fired.connect(_on_shot_fired)
	_player.died.connect(_on_player_died)
	_pause_menu.resume_pressed.connect(_set_pause_menu.bind(false))
	_pause_menu.quit_pressed.connect(_leave)
	get_tree().call_group("audio", "play_music", "chaosNaut")
	_top_up_blocks()


func _process(_delta: float) -> void:
	_hud.set_status(_player.hp, _player.jetpack.fuel, 0)
	_wave_label.text = "Wave %d" % wave


func _physics_process(delta: float) -> void:
	if _over:
		return
	_player.jetpack.fuel = _player.jetpack.max_fuel
	next_wave_in -= delta
	if next_wave_in <= 0.0:
		_start_wave()
	for bot in bots():
		if bot.global_position.x <= BOT_WRAP_X:
			bot.global_position.x = BOT_SPAWN_X
			bot.angry = true
	_top_up_blocks()


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("pause") and not _over:
		_set_pause_menu(not _pause_menu.visible)


func blocks() -> Array[Node]:
	return _living("chaos_blocks")


func bots() -> Array[Node]:
	return _living("chaos_bots")


func block_count() -> int:
	return blocks().size()


func bot_count() -> int:
	return bots().size()


func _living(group: String) -> Array[Node]:
	var result: Array[Node] = []
	for node in _entities.get_children():
		if node.is_in_group(group) and not node.is_queued_for_deletion():
			result.append(node)
	return result


func _start_wave() -> void:
	wave += 1
	next_wave_in = WAVE_INTERVAL
	get_tree().call_group("audio", "play", "newWave")
	for i in wave / 4 + 1:
		var bot: RigidBody2D = ChaosBotScene.instantiate()
		bot.position = Vector2(BOT_SPAWN_X, randf_range(0.0, SPAWN_Y_MAX))
		bot.add_to_group("chaos_bots")
		bot.died.connect(func() -> void: kills += 1)
		_entities.add_child(bot)


func _top_up_blocks() -> void:
	for i in BLOCK_COUNT - block_count():
		var block: RigidBody2D = HoverBlockScene.instantiate()
		block.position = Vector2(randf_range(BLOCK_X_MIN, BLOCK_X_MAX), randf_range(0.0, SPAWN_Y_MAX))
		block.add_to_group("chaos_blocks")
		_entities.add_child(block)


func _build_walls() -> void:
	var body := StaticBody2D.new()
	body.name = "Walls"
	var material := PhysicsMaterial.new()
	material.friction = 0.5
	body.physics_material_override = material
	var corners := [Vector2.ZERO, Vector2(ROOM_SIZE.x, 0), ROOM_SIZE, Vector2(0, ROOM_SIZE.y)]
	for i in 4:
		var a: Vector2 = corners[i]
		var b: Vector2 = corners[(i + 1) % 4]
		var capsule := CapsuleShape2D.new()
		capsule.radius = WALL_RADIUS
		capsule.height = a.distance_to(b) + WALL_RADIUS * 2.0
		var shape := CollisionShape2D.new()
		shape.shape = capsule
		shape.position = (a + b) / 2.0
		shape.rotation = (b - a).angle() - PI / 2.0
		body.add_child(shape)
	add_child(body)


func _build_game_over() -> void:
	var dim := ColorRect.new()
	dim.color = Color(0, 0, 0, 0.8)
	dim.size = Vector2(1024, 768)
	_game_over.add_child(dim)
	var heading := UiKit.make_label("GAME OVER")
	heading.position = Vector2(0, 260)
	heading.size = Vector2(1024, 20)
	heading.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_game_over.add_child(heading)
	var stats := UiKit.make_label("")
	stats.name = "Stats"
	stats.position = Vector2(0, 310)
	stats.size = Vector2(1024, 80)
	stats.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_game_over.add_child(stats)
	var back := UiKit.make_button("Back to Title", Vector2(140, 20))
	back.name = "Back"
	back.position = Vector2(442, 420)
	back.pressed.connect(_leave)
	_game_over.add_child(back)


func _on_player_died() -> void:
	_over = true
	var is_best := ChaosScore.submit(wave, kills)
	var best := ChaosScore.read()
	var stats: Label = _game_over.get_node("Stats")
	stats.text = "Wave %d     Kills %d\n\nBest: Wave %d     Kills %d%s" % [
		wave, kills, best.wave, best.kills, "\n\nNew best!" if is_best else "",
	]
	_game_over.visible = true
	get_tree().paused = true
	(_game_over.get_node("Back") as Button).grab_focus()


func _set_pause_menu(open: bool) -> void:
	_pause_menu.visible = open
	get_tree().paused = open
	if open:
		_pause_menu.open(null, Vector2i.ZERO)


func _leave() -> void:
	_pause_menu.visible = false
	get_tree().paused = false
	finished.emit()


func _on_shot_fired(shot: RigidBody2D) -> void:
	shot.bounds = Rect2(Vector2.ZERO, ROOM_SIZE)
	_shots.add_child(shot)
```

- [ ] **Step 3: The arena scene**

Create `scenes/chaosnaut.tscn`:

```
[gd_scene load_steps=7 format=3]

[ext_resource type="Script" path="res://scenes/chaosnaut.gd" id="1"]
[ext_resource type="PackedScene" path="res://entities/player/player.tscn" id="2"]
[ext_resource type="Script" path="res://ui/hud.gd" id="3"]
[ext_resource type="Script" path="res://ui/pause_menu.gd" id="4"]
[ext_resource type="Script" path="res://effects/particle_field.gd" id="5"]
[ext_resource type="Script" path="res://effects/screen_fx.gd" id="6"]

[node name="Chaosnaut" type="Node2D"]
process_mode = 3
script = ExtResource("1")

[node name="Entities" type="Node2D" parent="."]
process_mode = 1

[node name="Player" parent="." instance=ExtResource("2")]
process_mode = 1

[node name="Shots" type="Node2D" parent="."]
process_mode = 1

[node name="Particles" type="Node2D" parent="."]
process_mode = 1
script = ExtResource("5")

[node name="Camera2D" type="Camera2D" parent="."]

[node name="Hud" type="CanvasLayer" parent="."]

[node name="Strip" type="Control" parent="Hud"]
offset_right = 1024.0
offset_bottom = 768.0
mouse_filter = 2
script = ExtResource("3")

[node name="Wave" type="Label" parent="Hud"]
offset_left = 960.0
offset_top = 4.0
offset_right = 1024.0
offset_bottom = 24.0
horizontal_alignment = 1

[node name="ScreenFx" type="CanvasLayer" parent="."]
layer = 1
script = ExtResource("6")

[node name="PauseMenu" type="CanvasLayer" parent="."]
layer = 2
visible = false
script = ExtResource("4")
show_map = false

[node name="GameOver" type="CanvasLayer" parent="."]
layer = 3
visible = false
```

- [ ] **Step 4: Run the test**

```bash
timeout 200 "$GODOT" --headless --path . --script res://tools/test_chaosnaut.gd > /tmp/out.txt 2>&1; grep -E "FAIL:|test passed|test FAILED" /tmp/out.txt; grep -E 'SCRIPT ERROR|^ERROR' /tmp/out.txt | grep -v -c 'at exit'
```

Expected: `chaosnaut test passed` and `0`.

- [ ] **Step 5: Commit**

```bash
git add scenes ui
git commit -m "Add the Chaosnaut arena with waves and a game-over screen"
```

---

### Task 3: Title button and main flow

**Files:**
- Modify: `tools/test_main.gd`
- Modify: `scenes/title.gd`, `scenes/main.gd`

- [ ] **Step 1: Add the failing checks**

In `tools/test_main.gd`, add a constant after `CampaignScript`:

```gdscript
const ChaosnautScript := preload("res://scenes/chaosnaut.gd")
```

and add directly before the line `	for slot in SaveGame.SLOTS:` near the end of `_run` (the second such loop, which deletes the slots before printing the result):

```gdscript
	# Chaosnaut from the title and back.
	_expect(_button("Chaosnaut") != null, "the title offers Chaosnaut")
	_button("Chaosnaut").pressed.emit()
	await _settle()
	_expect(_is(ChaosnautScript), "the Chaosnaut button starts the mode")
	if _is(ChaosnautScript):
		_main.screen.finished.emit()
	await _settle()
	_expect(_is(TitleScript), "leaving Chaosnaut returns to the title")

```

- [ ] **Step 2: Run it to verify it fails**

```bash
timeout 200 "$GODOT" --headless --path . --script res://tools/test_main.gd 2>&1 | grep -E "FAIL:" | head -2
```

Expected: `FAIL: the title offers Chaosnaut`.

- [ ] **Step 3: Title button**

In `scenes/title.gd`:

Add after the `continue_game` signal:

```gdscript
signal chaosnaut_pressed
```

Add after the `SLOT_SPACING` constant:

```gdscript
const CHAOSNAUT_Y := 564.0
```

In `_ready`, add directly after the line `_build_slots()`:

```gdscript
	var chaosnaut := UiKit.make_button("Chaosnaut", SMALL_BUTTON)
	chaosnaut.name = "Chaosnaut"
	chaosnaut.position = Vector2(CENTER_X - SMALL_BUTTON.x / 2.0, CHAOSNAUT_Y)
	chaosnaut.pressed.connect(func() -> void: chaosnaut_pressed.emit())
	add_child(chaosnaut)
```

- [ ] **Step 4: Main flow**

In `scenes/main.gd`:

Add after the `CampaignScene` constant:

```gdscript
const ChaosnautScene := preload("res://scenes/chaosnaut.tscn")
```

In `show_title`, add directly after the line that connects `continue_game`:

```gdscript
	title.chaosnaut_pressed.connect(_start_chaosnaut, CONNECT_DEFERRED)
```

Add this function directly before `func _show_image(`:

```gdscript
func _start_chaosnaut() -> void:
	var chaosnaut := ChaosnautScene.instantiate()
	chaosnaut.finished.connect(show_title, CONNECT_DEFERRED)
	_show(chaosnaut)


```

- [ ] **Step 5: Run every check**

```bash
python -m unittest discover -s tools -p "test_*.py" 2>&1 | tail -1
for t in smoke_test test_jetpack test_save test_effects test_monsters test_campaign test_chaosnaut test_main; do timeout 200 "$GODOT" --headless --path . --script res://tools/$t.gd > /tmp/out.txt 2>&1; echo "$t: $(grep -E 'test passed|test FAILED' /tmp/out.txt) errors=$(grep -E 'SCRIPT ERROR|^ERROR' /tmp/out.txt | grep -v -c 'at exit')"; grep "FAIL:" /tmp/out.txt; done
```

Expected: `OK`, then eight `passed` lines each with `errors=0`.

- [ ] **Step 6: Commit**

```bash
git add scenes tools/test_main.gd
git commit -m "Add Chaosnaut to the title screen"
```

---

## Done when

- Every check in Task 3 Step 5 passes with no errors.
- The title has a Chaosnaut button that starts the mode.
- Waves arrive every 10 seconds with a sound; bots drift left, wrap round angry, and can be shot.
- Fuel never runs out; blocks that are shot away are replaced.
- Dying shows wave, kills and the best result, and Back to Title returns to the title.
