# Extranaut Port, Plan 2: Player, Walls and Room Transitions

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A playable Extranaut who can run, jetpack and shoot through all 100 rooms, with sliding camera transitions between rooms.

**Architecture:** The player and its shots are `RigidBody2D` circles using the original masses and speeds. A `Campaign` scene owns the current room, the player, the shots and the camera; it detects room exits with the original thresholds, loads the neighbouring room beside the current one in world space, and slides the camera across while the tree is paused. Jetpack fuel is a small standalone class so its reach can be tested numerically against a port of the original pulse logic.

**Tech Stack:** Godot 4.7 GDScript, headless `--script` tests.

**Spec:** `docs/superpowers/specs/2026-10-07-extranaut-godot-port-design.md`

**This is plan 2 of 7.** Out of scope here and covered later: monsters and damage (plan 3), saves, HUD, map, menus and the ending (plan 4), sound and particles (plan 6).

---

## Conventions for every task

- Shell is Git Bash. Run commands from the repository root.
- Godot binary:

```bash
GODOT="/c/Users/mattf/Desktop/godot47/Godot_v4.7-stable_win64_console.exe"
```

- GDScript files are indented with tabs.
- Work on branch `plan-2-player-and-rooms`.
- Commit messages end with this trailer:

```
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

## Facts from the original that this plan ports

Player (`playerCharacter.py`): circle radius 16, mass 20. Left/right set horizontal velocity to 200 px/s, and to 0 with no input. The sprite sheet `xenoNaturalistSheet` has rows 0 (right), 1 (left), 2 (dead right), 3 (dead left), 4 frames each; the walk cycle advances every 60 ms while horizontal speed exceeds 30.

Jetpack: every 100 ms while up is held and fuel exceeds 300, an impulse of 3500 (175 px/s on mass 20) costing 300 fuel. Fuel regenerates 50 on a 40 ms timer. At the original's 60 fps with millisecond timers, the 40 ms timer fires every third frame, so regeneration is effectively 1,000 fuel/s, not the 1,250 the constants suggest. A simulation of that logic gives these apex heights from a standing start with up held:

| Max fuel | Original apex (px) |
| --- | --- |
| 2000 | 1273 |
| 3500 | 4271 |
| 5000 | 9030 |

A continuous model with thrust 1750 px/s², burn 3000 fuel/s, regeneration 1000 fuel/s, running until the tank is empty and restarting at 400 fuel, matches the original apex within 1% across 2000 to 5000 max fuel.

Gun: energy ball radius 8, mass 20, no gravity, impulse 10,000 (500 px/s). It spawns 20 px in front of the player's centre and 7 px below it. It dies on touching anything or when its speed drops below 400. Cooldown by gun level: 1000, 800, 600, 400 ms.

Room exits (`game.py`), in terms of the player's centre in room coordinates:

| Exit | Trigger | Entry position in the next room |
| --- | --- | --- |
| Right | x >= 944 | (16, y) |
| Left | x <= 16 | (944, y) |
| Down | y >= 742 | (x, 16) |
| Up | y <= 26 | (x, 720) |

After a transition, no further transition happens until the player has been outside every trigger zone. At the edge of the 10x10 grid nothing happens. Velocity carries over.

## Collision layers

| Bit | Value | Name |
| --- | --- | --- |
| 1 | 1 | World (walls) |
| 2 | 2 | Player |
| 3 | 4 | Monsters (plan 3) |
| 4 | 8 | Player shots |
| 5 | 16 | Enemy shots (plan 3) |

Player: layer 2, mask 1 + 4 + 16 = 21. Player shot: layer 8, mask 21.

## Physics decisions

- The player has `lock_rotation` and friction 0. The original body could roll, so wall friction never slowed it; zero friction on a non-rotating body gives the same result.
- The player has `can_sleep = false`, because `_integrate_forces` is not called on a sleeping body and input would be ignored.
- Player and shots use `continuous_cd = 2` (cast shape). A long fall exceeds 16 px per physics frame, which would otherwise pass through a wall segment.

## File structure

| Path | Responsibility |
| --- | --- |
| `input/controls.gd` | Registers input actions in code |
| `entities/player/jetpack.gd` | Fuel model |
| `entities/player/player.gd`, `player.tscn` | Movement, thrust, firing, animation |
| `entities/projectiles/energy_ball.gd`, `energy_ball.tscn` | Player shot |
| `scenes/campaign.gd`, `campaign.tscn` | Current room, transitions, camera, temporary HUD strip |
| `tools/test_jetpack.gd` | Jetpack reach against a port of the original logic |
| `tools/test_campaign.gd` | Headless play test: rest, run, thrust, fire, no tunnelling, room transition |
| `tools/import_world.gd`, `tools/smoke_test.gd` | Modified: foreground draws above entities |
| `scenes/room_viewer.gd`, `room_viewer.tscn` | Deleted |

---

### Task 1: Foreground layer above entities

The player lives outside the room scene, so it would draw on top of the whole room. Raising the foreground's `z_index` puts it back above the player, as in the original.

**Files:**
- Modify: `tools/smoke_test.gd`
- Modify: `tools/import_world.gd`
- Regenerate: `world/rooms/*.tscn`

- [ ] **Step 1: Add the failing check**

In `tools/smoke_test.gd`, add these lines directly before the line `root.remove_child(room)`:

```gdscript
	_expect(room.get_node("Foreground").z_index == 10, "%s Foreground z_index" % path)
	_expect(room.get_node("ForegroundAnimated").z_index == 10, "%s ForegroundAnimated z_index" % path)
```

- [ ] **Step 2: Run it to verify it fails**

```bash
"$GODOT" --headless --path . --script res://tools/smoke_test.gd 2>&1 | tail -2
```

Expected: `smoke test FAILED: 200 failures`.

- [ ] **Step 3: Set the z index in the importer**

In `tools/import_world.gd`, add a constant after `const ART_SCALE := Vector2(2, 2)`:

```gdscript
const FOREGROUND_Z := 10
```

In `_build_room`, directly after the line `animated.name = layer_name.capitalize() + "Animated"`, add:

```gdscript
		if layer_name == "foreground":
			layer.z_index = FOREGROUND_Z
			animated.z_index = FOREGROUND_Z
```

- [ ] **Step 4: Regenerate and verify**

```bash
"$GODOT" --headless --path . --script res://tools/import_world.gd 2>&1 | tail -1
"$GODOT" --headless --path . --script res://tools/smoke_test.gd 2>&1 | tail -1
```

Expected: `imported 100 rooms`, then `smoke test passed: 100 rooms`.

- [ ] **Step 5: Commit**

```bash
git add tools world
git commit -m "Draw room foreground above entities

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Jetpack fuel model

**Files:**
- Create: `tools/test_jetpack.gd`
- Create: `entities/player/jetpack.gd`

- [ ] **Step 1: Write the failing test**

Create `tools/test_jetpack.gd`:

```gdscript
extends SceneTree
## Checks that the continuous jetpack reaches the same height as the original
## pulsed one. Run: godot --headless --path . --script res://tools/test_jetpack.gd

const Jetpack := preload("res://entities/player/jetpack.gd")
const GRAVITY := 900.0
const THRUST_ACCEL := 1750.0
const DT := 1.0 / 60.0
const FRAMES := 900

var _failures := 0


func _init() -> void:
	for max_fuel in [2000.0, 2500.0, 3000.0, 3500.0, 4000.0, 4500.0, 5000.0]:
		var original := _original_apex(max_fuel)
		var ported := _ported_apex(max_fuel)
		var error := absf(ported - original) / original
		print("max fuel %d: original %d px, ported %d px, error %.1f%%" % [max_fuel, original, ported, error * 100.0])
		if error > 0.05:
			_failures += 1
			printerr("FAIL: apex differs by more than 5% at max fuel ", max_fuel)
	_check_stall_and_restart()
	print("jetpack test passed" if _failures == 0 else "jetpack test FAILED")
	quit(1 if _failures > 0 else 0)


## Port of the jetpack part of PlayerCharacter.update with up held, stepped at
## 60 fps with the integer millisecond frame times pygame reported.
func _original_apex(max_fuel: float) -> float:
	var frame_ms := [17, 17, 16]
	var fuel := max_fuel
	var pulse_timer := 0
	var regen_timer := 40
	var velocity := 0.0
	var height := 0.0
	var apex := 0.0
	for frame in FRAMES:
		velocity -= GRAVITY * DT
		height += velocity * DT
		apex = maxf(apex, height)
		var ms: int = frame_ms[frame % 3]
		if pulse_timer > 0:
			pulse_timer = maxi(pulse_timer - ms, 0)
		if fuel > 300.0 and pulse_timer <= 0:
			pulse_timer = 100
			velocity += 175.0
			fuel -= 300.0
		regen_timer -= ms
		if regen_timer <= 0:
			fuel = minf(fuel + 50.0, max_fuel)
			regen_timer = 40
	return apex


func _ported_apex(max_fuel: float) -> float:
	var jetpack := Jetpack.new()
	jetpack.max_fuel = max_fuel
	jetpack.fuel = max_fuel
	var velocity := 0.0
	var height := 0.0
	var apex := 0.0
	for frame in FRAMES:
		var thrusting := jetpack.step(DT, true)
		velocity += ((THRUST_ACCEL if thrusting else 0.0) - GRAVITY) * DT
		height += velocity * DT
		apex = maxf(apex, height)
	return apex


func _check_stall_and_restart() -> void:
	var jetpack := Jetpack.new()
	jetpack.fuel = 10.0
	_expect(jetpack.step(DT, true), "thrusts with a little fuel left")
	_expect(not jetpack.step(DT, true), "stalls once empty")
	_expect(jetpack.fuel >= 0.0, "fuel never goes negative")
	for i in 12:
		_expect(not jetpack.step(DT, true), "stays stalled below the restart level")
	for i in 20:
		jetpack.step(DT, false)
	_expect(jetpack.step(DT, true), "restarts after regenerating")
	jetpack.fuel = jetpack.max_fuel
	jetpack.step(1.0, false)
	_expect(jetpack.fuel == jetpack.max_fuel, "regeneration stops at max fuel")


func _expect(condition: bool, message: String) -> void:
	if not condition:
		_failures += 1
		printerr("FAIL: " + message)
```

- [ ] **Step 2: Run it to verify it fails**

```bash
"$GODOT" --headless --path . --script res://tools/test_jetpack.gd 2>&1 | tail -3; echo "exit=${PIPESTATUS[0]}"
```

Expected: a parse or load error mentioning `res://entities/player/jetpack.gd`, and a non-zero exit.

- [ ] **Step 3: Write the fuel model**

Create `entities/player/jetpack.gd`:

```gdscript
extends RefCounted
## Jetpack fuel. A continuous version of the original's 100 ms impulse pulses,
## tuned so reach per tank matches (see tools/test_jetpack.gd).

const BURN_RATE := 3000.0
const REGEN_RATE := 1000.0
## After running dry the jetpack stays off until fuel recovers to this level.
const RESTART_FUEL := 400.0

var max_fuel := 2000.0
var fuel := 2000.0
var stalled := false


## Advances fuel by delta seconds. Returns true if the jetpack is thrusting.
func step(delta: float, wants_thrust: bool) -> bool:
	fuel = minf(fuel + REGEN_RATE * delta, max_fuel)
	if stalled and fuel >= RESTART_FUEL:
		stalled = false
	if not wants_thrust or stalled:
		return false
	fuel -= BURN_RATE * delta
	if fuel <= 0.0:
		fuel = 0.0
		stalled = true
	return true
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
"$GODOT" --headless --path . --script res://tools/test_jetpack.gd 2>&1 | tail -9; echo "exit=${PIPESTATUS[0]}"
```

Expected: seven lines each with an error under 5%, then `jetpack test passed` and `exit=0`.

- [ ] **Step 5: Commit**

```bash
git add tools/test_jetpack.gd entities
git commit -m "Add jetpack fuel model matched to the original's reach

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Input actions

**Files:**
- Create: `input/controls.gd`

Actions are registered in code so the bindings are readable and do not depend on hand-edited `project.godot` event blobs.

- [ ] **Step 1: Create `input/controls.gd`**

```gdscript
extends RefCounted
## Registers the game's input actions. Call setup() once at startup.
## Ctrl and Esc are deliberately unbound: browsers intercept them.

const ACTIONS := {
	"move_left": {
		"keys": [KEY_LEFT, KEY_A],
		"buttons": [JOY_BUTTON_DPAD_LEFT],
		"axis": [JOY_AXIS_LEFT_X, -1.0],
	},
	"move_right": {
		"keys": [KEY_RIGHT, KEY_D],
		"buttons": [JOY_BUTTON_DPAD_RIGHT],
		"axis": [JOY_AXIS_LEFT_X, 1.0],
	},
	"jetpack": {
		"keys": [KEY_UP, KEY_W],
		"buttons": [JOY_BUTTON_DPAD_UP, JOY_BUTTON_A],
		"axis": [JOY_AXIS_LEFT_Y, -1.0],
	},
	"fire": {
		"keys": [KEY_Z, KEY_X, KEY_SPACE],
		"buttons": [JOY_BUTTON_X],
	},
}


static func setup() -> void:
	for action in ACTIONS:
		if InputMap.has_action(action):
			continue
		InputMap.add_action(action, 0.5)
		var binding: Dictionary = ACTIONS[action]
		for key in binding.get("keys", []):
			var event := InputEventKey.new()
			event.physical_keycode = key
			InputMap.action_add_event(action, event)
		for button in binding.get("buttons", []):
			var event := InputEventJoypadButton.new()
			event.button_index = button
			InputMap.action_add_event(action, event)
		if binding.has("axis"):
			var event := InputEventJoypadMotion.new()
			event.axis = binding.axis[0]
			event.axis_value = binding.axis[1]
			InputMap.action_add_event(action, event)
```

- [ ] **Step 2: Commit**

This file is exercised by the campaign test in Task 6.

```bash
git add input
git commit -m "Register input actions in code

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Energy ball

**Files:**
- Create: `entities/projectiles/energy_ball.gd`
- Create: `entities/projectiles/energy_ball.tscn`

- [ ] **Step 1: Create `entities/projectiles/energy_ball.gd`**

```gdscript
extends RigidBody2D
## The player's shot. Flies straight, and dies when it touches anything,
## slows below MIN_SPEED, or leaves the room it was fired in.

const MIN_SPEED := 400.0
const FRAME_TIME := 0.06
const BOUNDS_MARGIN := 32.0

## The room's rectangle in world coordinates. Set by whoever spawns the shot.
var bounds := Rect2()

var _frame_elapsed := 0.0

@onready var _sprite: Sprite2D = $Sprite2D


func _ready() -> void:
	body_entered.connect(func(_body: Node) -> void: queue_free())


func _physics_process(delta: float) -> void:
	_frame_elapsed += delta
	if _frame_elapsed >= FRAME_TIME:
		_frame_elapsed -= FRAME_TIME
		_sprite.frame_coords.x = (_sprite.frame_coords.x + 1) % _sprite.hframes
	if linear_velocity.length() < MIN_SPEED:
		queue_free()
	elif bounds.has_area() and not bounds.grow(BOUNDS_MARGIN).has_point(global_position):
		queue_free()
```

- [ ] **Step 2: Create `entities/projectiles/energy_ball.tscn`**

```
[gd_scene load_steps=5 format=3]

[ext_resource type="Script" path="res://entities/projectiles/energy_ball.gd" id="1"]
[ext_resource type="Texture2D" path="res://assets/animations/projectiles1.png" id="2"]

[sub_resource type="PhysicsMaterial" id="material"]
friction = 0.5

[sub_resource type="CircleShape2D" id="shape"]
radius = 8.0

[node name="EnergyBall" type="RigidBody2D"]
collision_layer = 8
collision_mask = 21
mass = 20.0
physics_material_override = SubResource("material")
gravity_scale = 0.0
lock_rotation = true
continuous_cd = 2
contact_monitor = true
max_contacts_reported = 4
script = ExtResource("1")

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("shape")

[node name="Sprite2D" type="Sprite2D" parent="."]
scale = Vector2(2, 2)
texture = ExtResource("2")
hframes = 4
vframes = 4
```

- [ ] **Step 3: Check it loads**

```bash
"$GODOT" --headless --path . --import 2>&1 | grep -i -E "error|parse"; echo "grep_exit=$?"
```

Expected: no matching lines and `grep_exit=1`.

- [ ] **Step 4: Commit**

```bash
git add entities/projectiles
git commit -m "Add the player's energy ball shot

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Player

**Files:**
- Create: `entities/player/player.gd`
- Create: `entities/player/player.tscn`

- [ ] **Step 1: Create `entities/player/player.gd`**

```gdscript
extends RigidBody2D
## The Extranaut: runs, jetpacks and shoots.

signal shot_fired(shot: RigidBody2D)

const Jetpack := preload("res://entities/player/jetpack.gd")
const EnergyBallScene := preload("res://entities/projectiles/energy_ball.tscn")

## Seconds between shots, indexed by gun level - 1.
const FIRE_COOLDOWNS := [1.0, 0.8, 0.6, 0.4]
const MAX_GUN_LEVEL := 4
const WALK_FRAME_TIME := 0.06
const WALK_MIN_SPEED := 30.0
## Where a shot appears relative to the player's centre, facing right.
const MUZZLE_OFFSET := Vector2(20, 7)

@export var run_speed := 200.0
## The original set horizontal velocity instantly; this reaches run_speed in 80 ms.
@export var run_accel := 2500.0
@export var thrust_accel := 1750.0
@export var shot_speed := 500.0

var jetpack := Jetpack.new()
var gun_level := 1
## 1 facing right, -1 facing left.
var facing := 1

var _fire_cooldown := 0.0
var _walk_elapsed := 0.0

@onready var _sprite: Sprite2D = $Sprite2D


func _integrate_forces(state: PhysicsDirectBodyState2D) -> void:
	var direction := signf(Input.get_axis("move_left", "move_right"))
	if direction != 0.0:
		facing = int(direction)
	var velocity := state.linear_velocity
	velocity.x = move_toward(velocity.x, direction * run_speed, run_accel * state.step)
	if jetpack.step(state.step, Input.is_action_pressed("jetpack")):
		velocity.y -= thrust_accel * state.step
	state.linear_velocity = velocity


func _physics_process(delta: float) -> void:
	_fire_cooldown = maxf(_fire_cooldown - delta, 0.0)
	if Input.is_action_pressed("fire") and _fire_cooldown <= 0.0:
		_fire()
	_animate(delta)


func _fire() -> void:
	var shot: RigidBody2D = EnergyBallScene.instantiate()
	shot.position = global_position + Vector2(MUZZLE_OFFSET.x * facing, MUZZLE_OFFSET.y)
	shot.linear_velocity = Vector2(shot_speed * facing, 0.0)
	shot_fired.emit(shot)
	_fire_cooldown = FIRE_COOLDOWNS[clampi(gun_level, 1, MAX_GUN_LEVEL) - 1]


func _animate(delta: float) -> void:
	_sprite.frame_coords.y = 0 if facing > 0 else 1
	if absf(linear_velocity.x) > WALK_MIN_SPEED:
		_walk_elapsed += delta
		if _walk_elapsed >= WALK_FRAME_TIME:
			_walk_elapsed -= WALK_FRAME_TIME
			_sprite.frame_coords.x = (_sprite.frame_coords.x + 1) % _sprite.hframes
```

- [ ] **Step 2: Create `entities/player/player.tscn`**

```
[gd_scene load_steps=5 format=3]

[ext_resource type="Script" path="res://entities/player/player.gd" id="1"]
[ext_resource type="Texture2D" path="res://assets/animations/xenoNaturalistSheet.png" id="2"]

[sub_resource type="PhysicsMaterial" id="material"]
friction = 0.0

[sub_resource type="CircleShape2D" id="shape"]
radius = 16.0

[node name="Player" type="RigidBody2D"]
collision_layer = 2
collision_mask = 21
mass = 20.0
physics_material_override = SubResource("material")
can_sleep = false
lock_rotation = true
continuous_cd = 2
script = ExtResource("1")

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("shape")

[node name="Sprite2D" type="Sprite2D" parent="."]
scale = Vector2(2, 2)
texture = ExtResource("2")
hframes = 4
vframes = 4
```

- [ ] **Step 3: Check it loads**

```bash
"$GODOT" --headless --path . --import 2>&1 | grep -i -E "error|parse"; echo "grep_exit=$?"
```

Expected: no matching lines and `grep_exit=1`.

- [ ] **Step 4: Commit**

The player's behaviour is tested through the campaign scene in Task 6.

```bash
git add entities/player
git commit -m "Add the player with movement, jetpack and gun

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Campaign scene and room transitions

**Files:**
- Create: `tools/test_campaign.gd`
- Create: `scenes/campaign.gd`
- Create: `scenes/campaign.tscn`
- Modify: `project.godot` (main scene)
- Delete: `scenes/room_viewer.gd`, `scenes/room_viewer.tscn`

Rooms sit in world space at `grid * (960, 768)`, so the next room is placed beside the current one and the camera slides between them. The tree is paused during the slide; the `Campaign` node itself keeps processing so it can run the tween.

The test uses room (4, 2), whose layout near the edges is: floor at y = 640 for x from 0 to 128, and floor at y = 480 for x from 896 to 960.

- [ ] **Step 1: Write the failing test**

Create `tools/test_campaign.gd`:

```gdscript
extends SceneTree
## Headless play test of the campaign scene.
## Run: godot --headless --path . --script res://tools/test_campaign.gd

const CampaignScript := preload("res://scenes/campaign.gd")

var _failures := 0


func _initialize() -> void:
	_run()


func _run() -> void:
	_check_exit_rules()

	var campaign: Node2D = load("res://scenes/campaign.tscn").instantiate()
	root.add_child(campaign)
	var player: RigidBody2D = campaign.get_node("Player")
	var shots: Node = campaign.get_node("Shots")
	await _frames(120)

	# Comes to rest on the ground of the start room.
	var local: Vector2 = player.global_position - campaign.room.position
	_expect(player.linear_velocity.length() < 5.0, "player rests, velocity %s" % player.linear_velocity)
	_expect(local.y > 352.0 and local.y < 768.0, "player is on the ground, y %.1f" % local.y)

	# Runs right at the original speed, then stops.
	var start_x := player.global_position.x
	Input.action_press("move_right")
	await _frames(30)
	_expect(absf(player.linear_velocity.x - 200.0) < 20.0, "runs at 200, got %.1f" % player.linear_velocity.x)
	Input.action_release("move_right")
	await _frames(30)
	_expect(player.global_position.x > start_x + 50.0, "moved right")
	_expect(absf(player.linear_velocity.x) < 5.0, "stops when input is released")
	_expect(player.facing == 1, "faces right")

	# Jetpack lifts and burns fuel.
	await _frames(90)
	var start_y := player.global_position.y
	Input.action_press("jetpack")
	await _frames(30)
	Input.action_release("jetpack")
	_expect(player.global_position.y < start_y - 30.0, "jetpack lifts the player")
	_expect(player.jetpack.fuel < player.jetpack.max_fuel, "jetpack burns fuel")

	# Fires one shot to the right, and respects the cooldown.
	Input.action_press("fire")
	await _frames(10)
	Input.action_release("fire")
	_expect(shots.get_child_count() == 1, "one shot fired, got %d" % shots.get_child_count())
	if shots.get_child_count() > 0:
		_expect(shots.get_child(0).linear_velocity.x > 400.0, "shot flies right")

	# A fast fall does not pass through the floor (y = 640 at x = 64).
	player.global_position = campaign.room.position + Vector2(64, 300)
	player.linear_velocity = Vector2(0, 1500)
	await _frames(60)
	local = player.global_position - campaign.room.position
	_expect(local.y < 640.0, "fast fall stops on the floor, y %.1f" % local.y)

	# Walking off the right edge moves to room (5, 2).
	player.global_position = campaign.room.position + Vector2(920, 440)
	player.linear_velocity = Vector2.ZERO
	await _frames(30)
	Input.action_press("move_right")
	var waited := 0
	while campaign.grid != Vector2i(5, 2) and waited < 120:
		await physics_frame
		waited += 1
	Input.action_release("move_right")
	_expect(campaign.grid == Vector2i(5, 2), "entered room 5,2, grid is %s" % campaign.grid)
	_expect(paused, "tree is paused during the slide")
	await _frames(40)
	_expect(not paused, "tree resumes after the slide")
	_expect(campaign.get_node("World").get_child_count() == 1, "old room is freed")
	_expect(campaign.room.position == Vector2(5 * 960, 2 * 768), "new room is placed in world space")
	local = player.global_position - campaign.room.position
	_expect(local.x >= 16.0 and local.x < 300.0, "player enters at the left, x %.1f" % local.x)
	var camera: Camera2D = campaign.get_node("Camera2D")
	_expect(camera.position == campaign.room.position + Vector2(512, 384), "camera is on the new room")
	_expect(shots.get_child_count() == 0, "shots are cleared on transition")

	print("campaign test passed" if _failures == 0 else "campaign test FAILED: %d failures" % _failures)
	quit(1 if _failures > 0 else 0)


func _check_exit_rules() -> void:
	_expect(CampaignScript.exit_step(Vector2(480, 384)) == Vector2i.ZERO, "no exit mid-room")
	_expect(CampaignScript.exit_step(Vector2(944, 384)) == Vector2i.RIGHT, "exit right at 944")
	_expect(CampaignScript.exit_step(Vector2(943, 384)) == Vector2i.ZERO, "no exit at 943")
	_expect(CampaignScript.exit_step(Vector2(16, 384)) == Vector2i.LEFT, "exit left at 16")
	_expect(CampaignScript.exit_step(Vector2(480, 742)) == Vector2i.DOWN, "exit down at 742")
	_expect(CampaignScript.exit_step(Vector2(480, 26)) == Vector2i.UP, "exit up at 26")
	_expect(CampaignScript.entry_position(Vector2i.RIGHT, Vector2(944, 300)) == Vector2(16, 300), "enter from left side")
	_expect(CampaignScript.entry_position(Vector2i.LEFT, Vector2(16, 300)) == Vector2(944, 300), "enter from right side")
	_expect(CampaignScript.entry_position(Vector2i.DOWN, Vector2(200, 742)) == Vector2(200, 16), "enter from top")
	_expect(CampaignScript.entry_position(Vector2i.UP, Vector2(200, 26)) == Vector2(200, 720), "enter from bottom")


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
"$GODOT" --headless --path . --script res://tools/test_campaign.gd 2>&1 | tail -3; echo "exit=${PIPESTATUS[0]}"
```

Expected: a load error mentioning `res://scenes/campaign.gd`, and a non-zero exit.

- [ ] **Step 3: Create `scenes/campaign.gd`**

```gdscript
extends Node2D
## The campaign: owns the current room, the player, shots and the camera, and
## moves between rooms when the player crosses an edge.
## To save a screenshot and quit:
##   godot --path . -- --room=4,2 --shot=C:/some/file.png

const Controls := preload("res://input/controls.gd")

const ROOM_SIZE := Vector2(960, 768)
const GRID_SIZE := Vector2i(10, 10)
const START_ROOM := Vector2i(4, 2)
## Camera centre relative to the room origin: the room fills the left 960 px
## of the 1024 px view and the HUD strip covers the rest.
const VIEW_CENTER := Vector2(512, 384)
const SLIDE_TIME := 0.35

var grid := START_ROOM
var room: Node2D

## False from a transition until the player has left every exit zone, so
## arriving inside the opposite zone does not bounce straight back.
var _exits_armed := false
var _sliding := false

@onready var _world: Node2D = $World
@onready var _player: RigidBody2D = $Player
@onready var _shots: Node2D = $Shots
@onready var _camera: Camera2D = $Camera2D
@onready var _fuel_label: Label = $Hud/Fuel


func _ready() -> void:
	Controls.setup()
	var shot_path := ""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--room="):
			var parts := arg.trim_prefix("--room=").split(",")
			grid = Vector2i(int(parts[0]), int(parts[1]))
		elif arg.begins_with("--shot="):
			shot_path = arg.trim_prefix("--shot=")

	room = _load_room(grid)
	_world.add_child(room)
	var start: Vector2 = room.player_start if room.has_player_start else ROOM_SIZE / 2.0
	_player.global_position = room.position + start
	_camera.position = room.position + VIEW_CENTER
	_player.shot_fired.connect(_on_shot_fired)

	if shot_path != "":
		await get_tree().create_timer(1.0).timeout
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png(shot_path)
		get_tree().quit()


func _process(_delta: float) -> void:
	_fuel_label.text = "FUEL\n%d" % int(_player.jetpack.fuel)


func _physics_process(_delta: float) -> void:
	if _sliding:
		return
	var local := _player.global_position - room.position
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


## Which way the player is leaving, given its centre in room coordinates.
## Thresholds are the original's, converted from sprite corner to centre.
static func exit_step(local: Vector2) -> Vector2i:
	if local.x >= 944.0:
		return Vector2i.RIGHT
	if local.x <= 16.0:
		return Vector2i.LEFT
	if local.y >= 742.0:
		return Vector2i.DOWN
	if local.y <= 26.0:
		return Vector2i.UP
	return Vector2i.ZERO


## Where the player appears in the next room after leaving in direction step.
static func entry_position(step: Vector2i, local: Vector2) -> Vector2:
	match step:
		Vector2i.RIGHT:
			return Vector2(16.0, local.y)
		Vector2i.LEFT:
			return Vector2(944.0, local.y)
		Vector2i.DOWN:
			return Vector2(local.x, 16.0)
		_:
			return Vector2(local.x, 720.0)


func _enter_room(next: Vector2i, step: Vector2i, local: Vector2) -> void:
	_sliding = true
	_exits_armed = false
	var old_room := room
	grid = next
	room = _load_room(grid)
	_world.add_child(room)
	for shot in _shots.get_children():
		shot.queue_free()
	_player.global_position = room.position + entry_position(step, local)

	get_tree().paused = true
	var tween := create_tween()
	tween.set_pause_mode(Tween.TWEEN_PAUSE_PROCESS)
	tween.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tween.tween_property(_camera, "position", room.position + VIEW_CENTER, SLIDE_TIME)
	await tween.finished
	old_room.queue_free()
	get_tree().paused = false
	_sliding = false


func _load_room(at: Vector2i) -> Node2D:
	var loaded: Node2D = load("res://world/rooms/room_%d_%d.tscn" % [at.x, at.y]).instantiate()
	loaded.position = Vector2(at) * ROOM_SIZE
	return loaded


func _on_shot_fired(shot: RigidBody2D) -> void:
	shot.bounds = Rect2(room.position, ROOM_SIZE)
	_shots.add_child(shot)
```

- [ ] **Step 4: Create `scenes/campaign.tscn`**

`process_mode = 3` is "always" and `process_mode = 1` is "pausable".

```
[gd_scene load_steps=3 format=3]

[ext_resource type="Script" path="res://scenes/campaign.gd" id="1"]
[ext_resource type="PackedScene" path="res://entities/player/player.tscn" id="2"]

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

[node name="Strip" type="ColorRect" parent="Hud"]
offset_left = 960.0
offset_right = 1024.0
offset_bottom = 768.0
color = Color(0, 0, 0, 1)

[node name="Fuel" type="Label" parent="Hud"]
offset_left = 962.0
offset_top = 4.0
offset_right = 1022.0
offset_bottom = 60.0
theme_override_font_sizes/font_size = 12
horizontal_alignment = 1
```

- [ ] **Step 5: Make it the main scene and remove the viewer**

In `project.godot`, change the `run/main_scene` line to:

```ini
run/main_scene="res://scenes/campaign.tscn"
```

Then:

```bash
git rm -q scenes/room_viewer.gd scenes/room_viewer.tscn
rm -f scenes/room_viewer.gd.uid
```

- [ ] **Step 6: Run the test to verify it passes**

```bash
"$GODOT" --headless --path . --import 2>&1 | grep -i -E "error|parse"
"$GODOT" --headless --path . --script res://tools/test_campaign.gd 2>&1 | tail -6; echo "exit=${PIPESTATUS[0]}"
```

Expected: `campaign test passed` and `exit=0`.

- [ ] **Step 7: Look at it**

```bash
mkdir -p build/shots
"$GODOT" --path . -- --shot="$(pwd -W)/build/shots/campaign_start.png" 2>&1 | grep -i error
```

Open `build/shots/campaign_start.png`. Check: the player sprite stands on the ground near the middle of room (4, 2); the right 64 px is black with a `FUEL 2000` label; no collision debug lines are drawn.

- [ ] **Step 8: Run every check**

```bash
python -m unittest discover -s tools -p "test_*.py" 2>&1 | tail -1
for t in smoke_test test_jetpack test_campaign; do "$GODOT" --headless --path . --script res://tools/$t.gd 2>&1 | tail -1; done
```

Expected: `OK`, `smoke test passed: 100 rooms`, `jetpack test passed`, `campaign test passed`.

- [ ] **Step 9: Commit**

```bash
git add -A scenes tools project.godot
git commit -m "Add the campaign scene with sliding room transitions

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Done when

- All four checks in Task 6 Step 8 pass.
- Running the project starts in room (4, 2) with a controllable player: arrows or A/D to run, up or W to jetpack, Z, X or Space to fire.
- Crossing a room edge slides the camera to the next room.
- The author has played it and reported how movement, thrust and transitions feel. Tuning values are the exported properties on `entities/player/player.gd`, the constants in `entities/player/jetpack.gd`, and `SLIDE_TIME` in `scenes/campaign.gd`.
