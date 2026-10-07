# Extranaut Port, Plan 3: Monsters and Projectiles

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every room is populated with its original monsters, doors, powerups and save points; enemies shoot; the player has health, takes damage, dies and respawns at the last checkpoint.

**Architecture:** One `Monster` base script (a `RigidBody2D`) carries health, shot damage, animation and firing helpers; each kind adds a short `_behave()` porting its timers and impulses from `monster.py`. Static data (radius, mass, sprite, flags) lives in scene files generated from one Python table, so 25 scenes need 14 behaviour scripts. Shots share a `Projectile` base. The campaign wires monster signals when it loads a room and owns the checkpoint and the set of rooms whose powerup is taken.

**Tech Stack:** Godot 4.7 GDScript, Python 3 for the scene generator, headless `--script` tests.

**Spec:** `docs/superpowers/specs/2026-10-07-extranaut-godot-port-design.md`

**This is plan 3 of 7.** Out of scope: writing saves to disk, the real HUD, map and menus (plan 4); Chaosnaut and ChaosBot (plan 5); sounds, particles and screen shake (plan 6).

---

## Conventions for every task

- Shell is Git Bash. Run commands from the repository root.
- Godot binary:

```bash
GODOT="/c/Users/mattf/Desktop/godot47/Godot_v4.7-stable_win64_console.exe"
```

- GDScript files are indented with tabs.
- Work on branch `plan-3-monsters`.
- Commit messages end with this trailer:

```
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

- Every whole-file code block in this plan is introduced by a line of the form ``Create `path`:`` or ``Replace `path` with:``. Write the block to that path exactly.
- Godot prints runtime script errors without failing the process. Each test command below therefore also counts `SCRIPT ERROR` lines, and that count must be 0.

## Porting rules

- Times in `monster.py` are milliseconds; here they are seconds.
- `body.apply_impulse(v)` becomes `apply_central_impulse(v)`. Masses are unchanged, so impulse values are unchanged.
- Where the original applied an impulse every frame (HoverBlock, HandBot), the value is scaled by `delta * 60` so it is frame-rate independent.
- The original located the player by its sprite's top-left corner, 16 px up and left of its centre, and aimed there. `Monster.player_corner()` keeps that, so aim and proximity checks match.
- A shot's velocity is its original impulse divided by its mass of 20.
- "Monsters in the room" counts every monster-class entity still alive in the room, including doors, hover blocks, save points and powerups, as the original's `len(monsters)` did.

## Original behaviours kept on purpose

- JumpBot has 1 HP. The original set 3 and then the base constructor reset it to 1.
- A shot that spawns overlapping its shooter dies at once. This affects AimerTurret firing up and left, and HeadBoss firing right, exactly as in the original.
- AimerTurrets float upward until they rest against a ceiling.
- Save points and powerups zero their own velocity every step, so they sink slowly until they rest on something and cannot be pushed.

## Deliberate differences

- Enemy shots do not collide with each other. In the original they collided but both survived.
- Gun level is capped at 4 (see the spec).

## Collision layers

| Value | Name | Mask |
| --- | --- | --- |
| 1 | World | |
| 2 | Player | 21 (world, monsters, enemy shots) |
| 4 | Monsters | 31 (everything) |
| 8 | Player shots | 21 (world, monsters, enemy shots) |
| 16 | Enemy shots | 15 (world, player, monsters, player shots) |

## Monster table

Radius 16, mass 20, friction 0.5, gravity scale 1, rotation locked, 1 HP, 4 animation frames unless stated. "Touch" means it damages the player on contact.

| Kind | Script | Sheet and row | Differences from the defaults |
| --- | --- | --- | --- |
| BallMonster | ball_monster | ballMonster 0 | rotates |
| SpikyBallMonster | ball_monster | ballMonster 2 | rotates, touch |
| JumpBot | jump_bot | bots2 0 | touch, frame chosen by script |
| Flyer | flyer | ballMonster 3 | gravity -1, touch |
| FlyBot | fly_bot | bots 0 | gravity -0.1, 3 HP, touch |
| BossBot1 | fly_bot | bossBots 0 | gravity -0.1, 6 HP, touch, drifts only downward, drift interval up to 75 ms |
| BossBot2 | fly_bot | bossBots 1 | gravity -0.1, 6 HP, touch, first shot after 1 s then every 0.5 s with random spread |
| BossBot3 | fly_bot | bossBots 2 | gravity -0.1, 10 HP, touch |
| AimerTurret | aimer_turret | bots2 2 | mass 1000, gravity -1, touch, 2 frames |
| DefenseTurretVertical | defense_turret_vertical | turret 0 | mass 5, gravity 0.8 |
| HoverBlock | hover_block | sprites/chaosBlocks cell (1, 4) | mass 4000, friction 20, gravity 0, 1 frame |
| HandBot | hand_bot | bigBots1 0, 32 px frames | radius 32, mass 200, 5 HP, touch, 2 frames |
| SpikyHeadMonster | spiky_head_monster | snakeHeadBoss cell (0, 4) | rotates, touch, immune to shots, 1 frame |
| ArtifactDoor | artifact_door | artifactDoor 0, 32 px frames | radius 32, mass 20000, friction 100, immune to shots, 2 frames |
| MonsterDoor | monster_door | artifactDoor 1, 32 px frames | as ArtifactDoor; opens when 1 monster remains |
| MonsterDoor2 | monster_door | artifactDoor 1, 32 px frames | as ArtifactDoor; opens when 2 monsters remain |
| SavePoint | save_point | savePoint 0 (row 1 when activated) | mass 40000, friction 40000 |
| HpPowerup | powerup | collectibles 2 | mass 40000, friction 40000, powerup, immune to shots |
| FuelPowerup | powerup | collectibles 0 | as HpPowerup |
| GunPowerup | powerup | collectibles 3 | as HpPowerup |
| AlienArtifact | powerup | collectibles 1 | as HpPowerup |
| OrbBoss | orb_boss | orbBoss 0/1 by mode, 32 px frames | radius 32, mass 200, rotates, 20 HP, touch, 2 frames |
| FallenExtranaut | orb_boss | fallenExtranaut 0, 32 px frames | radius 32, mass 200, rotates, 20 HP, touch; flat grenades from (32, 30); also fires aimed shots when chasing |
| OctoBoss | octo_boss | octoBoss 0, 32 px frames | radius 32, mass 200, gravity 0, 20 HP, touch, 1 frame |
| HeadBoss | head_boss | snakeHeadBoss 0 (row 1 shielded), 32 px frames | radius 32, mass 200, 15 HP, touch, frame chosen by script |

## File structure

| Path | Responsibility |
| --- | --- |
| `entities/projectiles/projectile.gd` | Shot base: animation, room bounds, die on contact |
| `entities/projectiles/energy_ball.gd` | Player shot (now extends the base) |
| `entities/projectiles/enemy_energy_ball.gd`, `.tscn` | Straight enemy shot |
| `entities/projectiles/energy_grenade.gd`, `.tscn` | Ballistic enemy shot with a 3 s fuse |
| `entities/player/player.gd`, `.tscn` | Adds health, contact damage, death, artifacts |
| `entities/monsters/monster.gd` | Monster base |
| `entities/monsters/<script>.gd` | 13 behaviour scripts, see the table |
| `tools/make_monster_scenes.py` | Generates `entities/monsters/*.tscn` |
| `tools/test_monsters.gd` | Arena tests |
| `tools/import_world.gd`, `tools/smoke_test.gd` | Rooms instance real monster scenes |
| `scenes/campaign.gd`, `tools/test_campaign.gd` | Monster signals, checkpoint, respawn, powerups taken |
| `world/monster_spawn.gd` | Deleted |

---

### Task 1: Projectile base and enemy shots

**Files:**
- Create: `entities/projectiles/projectile.gd`
- Modify: `entities/projectiles/energy_ball.gd`
- Create: `entities/projectiles/enemy_energy_ball.gd`, `entities/projectiles/enemy_energy_ball.tscn`
- Create: `entities/projectiles/energy_grenade.gd`, `entities/projectiles/energy_grenade.tscn`

These are tested through the arena tests in Task 3 and Task 4. This task ends with the existing checks still passing.

- [ ] **Step 1: Write the base**

Create `entities/projectiles/projectile.gd`:

```gdscript
extends RigidBody2D
## Base for all shots: animates the sprite, dies on touching anything, and
## frees itself once outside the room it was fired in.

const FRAME_TIME := 0.06
const BOUNDS_MARGIN := 32.0

## The room's rectangle in world coordinates. Set by whoever spawns the shot.
## Left empty, the shot is never culled.
var bounds := Rect2()

var _frame_elapsed := 0.0

@onready var _sprite: Sprite2D = $Sprite2D


func _ready() -> void:
	body_entered.connect(_on_body_entered)


func _physics_process(delta: float) -> void:
	_frame_elapsed += delta
	if _frame_elapsed >= FRAME_TIME:
		_frame_elapsed -= FRAME_TIME
		_sprite.frame_coords.x = (_sprite.frame_coords.x + 1) % _sprite.hframes
	if bounds.has_area() and not bounds.grow(BOUNDS_MARGIN).has_point(global_position):
		queue_free()


func _on_body_entered(_body: Node) -> void:
	queue_free()
```

- [ ] **Step 2: Rebase the player's shot on it**

Replace `entities/projectiles/energy_ball.gd` with:

```gdscript
extends "res://entities/projectiles/projectile.gd"
## The player's shot. Flies straight and also dies when it slows below MIN_SPEED.

const MIN_SPEED := 400.0


func _ready() -> void:
	super()
	add_to_group("player_shots")


func _physics_process(delta: float) -> void:
	super(delta)
	if linear_velocity.length() < MIN_SPEED:
		queue_free()
```

- [ ] **Step 3: Add the enemy energy ball**

Create `entities/projectiles/enemy_energy_ball.gd`:

```gdscript
extends "res://entities/projectiles/projectile.gd"
## A straight-flying enemy shot. Hurts the player on contact.


func _ready() -> void:
	super()
	add_to_group("enemy_shots")
```

Create `entities/projectiles/enemy_energy_ball.tscn`:

```
[gd_scene load_steps=5 format=3]

[ext_resource type="Script" path="res://entities/projectiles/enemy_energy_ball.gd" id="1"]
[ext_resource type="Texture2D" path="res://assets/animations/projectiles1.png" id="2"]

[sub_resource type="PhysicsMaterial" id="material"]
friction = 0.5

[sub_resource type="CircleShape2D" id="shape"]
radius = 8.0

[node name="EnemyEnergyBall" type="RigidBody2D"]
collision_layer = 16
collision_mask = 15
mass = 20.0
physics_material_override = SubResource("material")
gravity_scale = 0.0
continuous_cd = 1
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
frame = 4
```

- [ ] **Step 4: Add the grenade**

Create `entities/projectiles/energy_grenade.gd`:

```gdscript
extends "res://entities/projectiles/projectile.gd"
## A ballistic enemy shot. Explodes at once on a body, or FUSE seconds after
## first touching a wall. Hurts the player on contact either way.

const FUSE := 3.0

## Negative until the grenade has touched a wall.
var _fuse := -1.0


func _ready() -> void:
	super()
	add_to_group("enemy_shots")


func _physics_process(delta: float) -> void:
	super(delta)
	if _fuse >= 0.0:
		_fuse -= delta
		if _fuse < 0.0:
			queue_free()


func _on_body_entered(body: Node) -> void:
	if body is StaticBody2D:
		if _fuse < 0.0:
			_fuse = FUSE
	else:
		queue_free()
```

Create `entities/projectiles/energy_grenade.tscn`:

```
[gd_scene load_steps=5 format=3]

[ext_resource type="Script" path="res://entities/projectiles/energy_grenade.gd" id="1"]
[ext_resource type="Texture2D" path="res://assets/animations/projectiles2.png" id="2"]

[sub_resource type="PhysicsMaterial" id="material"]
friction = 0.5

[sub_resource type="CircleShape2D" id="shape"]
radius = 8.0

[node name="EnergyGrenade" type="RigidBody2D"]
collision_layer = 16
collision_mask = 15
mass = 20.0
physics_material_override = SubResource("material")
continuous_cd = 1
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

- [ ] **Step 5: Verify nothing broke**

```bash
"$GODOT" --headless --path . --import 2>&1 | grep -i -E "error|parse"
"$GODOT" --headless --path . --script res://tools/test_campaign.gd 2>&1 | tee /tmp/out.txt | tail -1; grep -c "SCRIPT ERROR" /tmp/out.txt
```

Expected: no import errors, `campaign test passed`, and `0`.

- [ ] **Step 6: Commit**

```bash
git add entities/projectiles
git commit -m "Add a projectile base, enemy energy ball and grenade

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Monster base, scene generator and the arena test

**Files:**
- Create: `tools/test_monsters.gd`
- Create: `entities/monsters/monster.gd`
- Create: `entities/monsters/ball_monster.gd`
- Create: `tools/make_monster_scenes.py`
- Create: `entities/monsters/*.tscn` (generated)

This task builds the base and the first kind, with the full test file. The test file refers to kinds and player features that later tasks add, so it is expected to fail until Task 5; each task says which of its sections must pass.

- [ ] **Step 1: Write the arena test**

Create `tools/test_monsters.gd`:

```gdscript
extends SceneTree
## Arena tests for monsters, shots and player damage.
## Run: godot --headless --path . --script res://tools/test_monsters.gd
## Pass "-- --only=name" to run the sections whose name contains that text.

const Controls := preload("res://input/controls.gd")
const PlayerScene := preload("res://entities/player/player.tscn")
const EnergyBallScene := preload("res://entities/projectiles/energy_ball.tscn")
const EnemyEnergyBallScene := preload("res://entities/projectiles/enemy_energy_ball.tscn")
const EnergyGrenadeScene := preload("res://entities/projectiles/energy_grenade.tscn")

const FLOOR_Y := 500.0
## Centre height of a radius-16 body resting on the floor.
const REST_Y := FLOOR_Y - 16.0
const PLAYER_REST := Vector2(0, FLOOR_Y - 13.0)

var _failures := 0
var _arena: Node2D
var _entities: Node2D
var _player: RigidBody2D
## One entry per shot fired in the current arena, recorded when it was fired.
var _shot_log: Array[Dictionary] = []
var _saves: Array[Node] = []


func _initialize() -> void:
	_run()


func _run() -> void:
	Controls.setup()
	await process_frame
	var only := ""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--only="):
			only = arg.trim_prefix("--only=")
	var sections := {
		"every_kind_runs": _test_every_kind_runs,
		"shots_damage_monsters": _test_shots_damage_monsters,
		"touch_damage": _test_touch_damage,
		"powerups": _test_powerups,
		"save_point": _test_save_point,
		"doors": _test_doors,
		"turrets": _test_turrets,
		"enemy_shots": _test_enemy_shots,
		"player_death": _test_player_death,
		"movers": _test_movers,
	}
	for section_name in sections:
		if only == "" or section_name.contains(only):
			var before := _failures
			await sections[section_name].call()
			print("%s: %s" % [section_name, "ok" if _failures == before else "FAILED"])
	print("monster test passed" if _failures == 0 else "monster test FAILED: %d failures" % _failures)
	quit(1 if _failures > 0 else 0)


func _test_every_kind_runs() -> void:
	_new_arena(Vector2(-300, PLAYER_REST.y))
	var world = JSON.parse_string(FileAccess.get_file_as_string("res://tools/zorta.json"))
	var kinds := {}
	for room in world.rooms:
		for m in room.monsters:
			kinds[m[0]] = true
	_expect(kinds.size() == 25, "25 kinds in the world, found %d" % kinds.size())
	var x := 0.0
	for kind in kinds:
		var file := String(kind).to_snake_case()
		if not ResourceLoader.exists("res://entities/monsters/%s.tscn" % file):
			_fail("no scene for %s" % kind)
			continue
		var monster := _spawn(file, Vector2(x, 400))
		_expect(monster.is_in_group("monsters"), "%s is in the monsters group" % kind)
		_expect(monster.hp == monster.max_hp, "%s starts at full hp" % kind)
		x += 120.0
	await _frames(180)


func _test_shots_damage_monsters() -> void:
	_new_arena()
	var ball := _spawn("ball_monster", Vector2(300, REST_Y))
	ball._kick_timer = 10.0
	_launch(EnergyBallScene, Vector2(200, REST_Y), Vector2(500, 0))
	await _frames(30)
	_expect(not is_instance_valid(ball), "one shot kills a ball monster")

	var bot := _spawn("fly_bot", Vector2(300, 300))
	bot.hit()
	bot.hit()
	_expect(bot.hp == 1 and not bot.is_queued_for_deletion(), "fly bot survives two hits")
	bot.hit()
	_expect(bot.is_queued_for_deletion(), "fly bot dies on the third hit")

	var spiky := _spawn("spiky_head_monster", Vector2(500, REST_Y))
	spiky._kick_timer = 10.0
	_launch(EnergyBallScene, Vector2(420, REST_Y), Vector2(500, 0))
	await _frames(30)
	_expect(is_instance_valid(spiky), "spiky head ignores shots")


func _test_touch_damage() -> void:
	_new_arena()
	await _frames(30)
	var ball := _spawn("ball_monster", _player.position + Vector2(28, -3))
	ball._kick_timer = 10.0
	await _frames(20)
	_expect(_player.hp == 5, "ball monsters are harmless, hp %d" % _player.hp)
	ball.free()

	var spiky := _spawn("spiky_ball_monster", _player.position + Vector2(28, -3))
	spiky._kick_timer = 10.0
	await _frames(10)
	_expect(_player.hp == 4, "spiky ball hurts on touch, hp %d" % _player.hp)
	spiky.free()
	spiky = _spawn("spiky_ball_monster", _player.position + Vector2(28, -3))
	spiky._kick_timer = 10.0
	await _frames(20)
	_expect(_player.hp == 4, "player is invulnerable for a second after a hit, hp %d" % _player.hp)


func _test_powerups() -> void:
	_new_arena()
	await _frames(30)
	var beside := Vector2(28, -3)
	_player.hp = 3
	var powerup := _spawn("hp_powerup", _player.position + beside)
	await _frames(10)
	_expect(_player.max_hp == 6 and _player.hp == 6, "hp powerup raises and refills hp")
	_expect(not is_instance_valid(powerup), "a collected powerup is removed")
	_expect(_saves.size() == 1, "a powerup requests a save")

	_spawn("fuel_powerup", _player.position + beside)
	await _frames(10)
	_expect(_player.jetpack.max_fuel == 2500.0, "fuel powerup adds 500 max fuel")

	_spawn("gun_powerup", _player.position + beside)
	await _frames(10)
	_expect(_player.gun_level == 2, "gun powerup raises the gun level")
	_player.gun_level = 4
	_spawn("gun_powerup", _player.position + beside)
	await _frames(10)
	_expect(_player.gun_level == 4, "gun level is capped at 4")

	_spawn("alien_artifact", _player.position + beside)
	await _frames(10)
	_expect(_player.artifacts == 1, "alien artifact is counted")
	_expect(_saves.size() == 5, "every powerup requests a save, got %d" % _saves.size())


func _test_save_point() -> void:
	_new_arena()
	var save_point := _spawn("save_point", Vector2(300, REST_Y))
	_launch(EnergyBallScene, Vector2(200, REST_Y), Vector2(500, 0))
	await _frames(30)
	_expect(_saves.size() == 1 and _saves[0] == save_point, "shooting a save point requests a save")
	_expect(save_point.sprite.frame_coords.y == 1, "an activated save point changes sprite row")
	_launch(EnergyBallScene, Vector2(200, REST_Y), Vector2(500, 0))
	await _frames(30)
	_expect(_saves.size() == 1, "a save point only activates once")
	_expect(is_instance_valid(save_point), "a save point is not destroyed by shots")


func _test_doors() -> void:
	_new_arena()
	var door := _spawn("monster_door", Vector2(300, 400))
	await _frames(3)
	_expect(not is_instance_valid(door), "a monster door alone in the room opens")

	var ball := _spawn("ball_monster", Vector2(500, REST_Y))
	door = _spawn("monster_door", Vector2(300, 400))
	await _frames(10)
	_expect(is_instance_valid(door), "a monster door stays shut while a monster lives")
	ball.hit()
	await _frames(3)
	_expect(not is_instance_valid(door), "a monster door opens when the last monster dies")

	ball = _spawn("ball_monster", Vector2(500, REST_Y))
	door = _spawn("monster_door_2", Vector2(300, 400))
	await _frames(3)
	_expect(not is_instance_valid(door), "monster door 2 opens when two monsters remain")
	ball.free()

	door = _spawn("artifact_door", Vector2(300, 400))
	_player.artifacts = 3
	await _frames(5)
	_expect(is_instance_valid(door), "the artifact door stays shut with 3 artifacts")
	_player.artifacts = 4
	await _frames(3)
	_expect(not is_instance_valid(door), "the artifact door opens with 4 artifacts")


func _test_turrets() -> void:
	_new_arena()
	var turret_pos := Vector2(300, 300)
	_spawn("aimer_turret", turret_pos)
	await _frames(130)
	_expect(_shot_log.size() >= 1, "aimer turret fires within about 2 s")
	if _shot_log.size() >= 1:
		var shot: Dictionary = _shot_log[0]
		_expect(shot.enemy, "turret shots are enemy shots")
		_expect(absf(shot.velocity.length() - 350.0) < 1.0, "aimed shots fly at 350, got %.1f" % shot.velocity.length())
		_expect(shot.velocity.x < 0.0, "the shot is aimed toward the player on its left")

	_new_arena()
	_spawn("defense_turret_vertical", Vector2(300, REST_Y))
	await _frames(190)
	_expect(_shot_log.size() >= 1, "defense turret fires within about 3 s")
	if _shot_log.size() >= 1:
		var grenade: Dictionary = _shot_log[0]
		_expect(grenade.gravity_scale == 1.0, "defense turret lobs grenades")
		_expect(grenade.velocity.y <= -500.0 and grenade.velocity.y >= -750.0, "grenades are lobbed upward, vy %.1f" % grenade.velocity.y)


func _test_enemy_shots() -> void:
	_new_arena()
	await _frames(30)
	var ball := _launch(EnemyEnergyBallScene, _player.position + Vector2(-80, 0), Vector2(350, 0))
	await _frames(20)
	_expect(_player.hp == 4, "an enemy energy ball hurts the player, hp %d" % _player.hp)
	_expect(not is_instance_valid(ball), "an enemy energy ball dies on contact")

	var grenade := _launch(EnergyGrenadeScene, Vector2(400, REST_Y - 30.0), Vector2.ZERO)
	var frames := 0
	while is_instance_valid(grenade) and frames < 300:
		await physics_frame
		frames += 1
	_expect(frames > 175 and frames < 215, "a grenade explodes 3 s after landing, took %d frames" % frames)

	grenade = _launch(EnergyGrenadeScene, _player.position + Vector2(0, -60), Vector2.ZERO)
	await _frames(30)
	_expect(not is_instance_valid(grenade), "a grenade explodes at once on the player")
	_expect(_player.hp == 3, "a grenade hurts the player, hp %d" % _player.hp)


func _test_player_death() -> void:
	_new_arena()
	await _frames(30)
	var died := [0]
	_player.died.connect(func() -> void: died[0] += 1)
	_player.hp = 1
	_player.hit()
	_expect(_player.is_dead(), "the player dies at 0 hp")
	Input.action_press("move_right")
	await _frames(30)
	Input.action_release("move_right")
	_expect(absf(_player.linear_velocity.x) < 5.0, "a dead player cannot move")
	_expect(died[0] == 0, "died is not emitted before the death pause ends")
	await _frames(100)
	_expect(died[0] == 1, "died is emitted after about 2 s, count %d" % died[0])
	await _frames(30)
	_expect(died[0] == 1, "died is emitted once")
	_player.revive()
	_expect(_player.hp == _player.max_hp and not _player.is_dead(), "revive restores full hp")


func _test_movers() -> void:
	_new_arena()
	var home := Vector2(300, 300)
	var block := _spawn("hover_block", home)
	var bot := _spawn("jump_bot", Vector2(600, REST_Y))
	var highest := bot.position.y
	for i in 120:
		await physics_frame
		highest = minf(highest, bot.position.y)
	_expect(block.position.distance_to(home) < 2.0, "a hover block holds its position")
	_expect(highest < REST_Y - 20.0, "a jump bot jumps")


func _new_arena(player_pos := PLAYER_REST) -> void:
	if _arena != null:
		root.remove_child(_arena)
		_arena.free()
	_shot_log.clear()
	_saves.clear()
	_arena = Node2D.new()
	var floor_body := StaticBody2D.new()
	var floor_shape := CollisionShape2D.new()
	var rect := RectangleShape2D.new()
	rect.size = Vector2(4000, 40)
	floor_shape.shape = rect
	floor_shape.position = Vector2(0, FLOOR_Y + 20.0)
	floor_body.add_child(floor_shape)
	_arena.add_child(floor_body)
	_entities = Node2D.new()
	_arena.add_child(_entities)
	_player = PlayerScene.instantiate()
	_player.position = player_pos
	_player.shot_fired.connect(_add_shot)
	_arena.add_child(_player)
	root.add_child(_arena)


func _spawn(file: String, pos: Vector2) -> RigidBody2D:
	var monster: RigidBody2D = load("res://entities/monsters/%s.tscn" % file).instantiate()
	monster.position = pos
	monster.shot_fired.connect(_add_shot)
	monster.save_requested.connect(func(source: Node) -> void: _saves.append(source))
	_entities.add_child(monster)
	return monster


func _add_shot(shot: RigidBody2D) -> void:
	_arena.add_child(shot)
	_shot_log.append({
		"enemy": shot.is_in_group("enemy_shots"),
		"velocity": shot.linear_velocity,
		"gravity_scale": shot.gravity_scale,
	})


func _launch(scene: PackedScene, pos: Vector2, velocity: Vector2) -> RigidBody2D:
	var shot: RigidBody2D = scene.instantiate()
	shot.position = pos
	shot.linear_velocity = velocity
	_arena.add_child(shot)
	return shot


func _frames(count: int) -> void:
	for i in count:
		await physics_frame


func _expect(condition: bool, message: String) -> void:
	if not condition:
		_fail(message)


func _fail(message: String) -> void:
	_failures += 1
	printerr("FAIL: " + message)
```

- [ ] **Step 2: Write the monster base**

Create `entities/monsters/monster.gd`:

```gdscript
extends RigidBody2D
## Base for everything the original called a Monster: enemies, doors, hover
## blocks, save points and powerups. Scenes are generated by
## tools/make_monster_scenes.py; subclasses add behaviour in _behave().

signal shot_fired(shot: RigidBody2D)
## Emitted by save points and powerups. The campaign sets the checkpoint.
signal save_requested(source: Node)

const EnemyEnergyBallScene := preload("res://entities/projectiles/enemy_energy_ball.tscn")
const EnergyGrenadeScene := preload("res://entities/projectiles/energy_grenade.tscn")

const FRAME_TIME := 0.09
const HIT_TIMEOUT := 0.1
const SHOT_MASS := 20.0
const AIM_IMPULSE := 7000.0
## The original measured the player from its sprite's top-left corner.
const PLAYER_CORNER_OFFSET := Vector2(-16, -16)

@export var max_hp := 1
@export var damages_player_on_touch := false
@export var damaged_by_shots := true
@export var is_powerup := false
## Frames in the looping animation along the sprite row. 1 disables it.
@export var anim_frames := 4

var hp := 1

var _hit_timeout := HIT_TIMEOUT
var _frame_elapsed := 0.0

@onready var sprite: Sprite2D = $Sprite2D


func _ready() -> void:
	hp = max_hp
	add_to_group("monsters")
	body_entered.connect(_on_body_entered)
	if anim_frames > 1:
		sprite.frame_coords.x = randi() % anim_frames
		_frame_elapsed = randf() * FRAME_TIME


func _physics_process(delta: float) -> void:
	_hit_timeout -= delta
	_animate(delta)
	_behave(delta, get_tree().get_first_node_in_group("player"))


## Per-kind behaviour. player is null when there is no player in the tree.
func _behave(_delta: float, _player: Node2D) -> void:
	pass


func _animate(delta: float) -> void:
	if anim_frames <= 1:
		return
	_frame_elapsed += delta
	if _frame_elapsed >= FRAME_TIME:
		_frame_elapsed -= FRAME_TIME
		sprite.frame_coords.x = (sprite.frame_coords.x + 1) % anim_frames


func hit() -> void:
	hp -= 1
	if hp <= 0:
		die()


func die() -> void:
	queue_free()


## Monster-class entities still alive in this room, this one included.
func monsters_in_room() -> int:
	var count := 0
	for node in get_parent().get_children():
		if node.is_in_group("monsters") and not node.is_queued_for_deletion():
			count += 1
	return count


func player_corner(player: Node2D) -> Vector2:
	return player.global_position + PLAYER_CORNER_OFFSET


## Impulse of the original's aimed shots, pointing at the player's corner
## plus lead.
func aim_at(player: Node2D, lead := Vector2.ZERO) -> Vector2:
	return (player_corner(player) + lead - global_position).normalized() * AIM_IMPULSE


func fire(scene: PackedScene, offset: Vector2, impulse: Vector2) -> void:
	var shot: RigidBody2D = scene.instantiate()
	shot.position = global_position + offset
	shot.linear_velocity = impulse / SHOT_MASS
	shot_fired.emit(shot)


func _on_body_entered(body: Node) -> void:
	if damaged_by_shots and _hit_timeout <= 0.0 and body.is_in_group("player_shots"):
		_hit_timeout = HIT_TIMEOUT
		hit()
```

- [ ] **Step 3: Write the first behaviour**

Create `entities/monsters/ball_monster.gd`:

```gdscript
extends "res://entities/monsters/monster.gd"
## Rolls around under random kicks. Used by BallMonster and SpikyBallMonster.

const KICKS := [-5000.0, 0.0, 5000.0]

var _kick_timer := randf_range(0.0, 5.0)


func _behave(delta: float, _player: Node2D) -> void:
	_kick_timer -= delta
	if _kick_timer < 0.0:
		_kick_timer = randf_range(0.0, 3.0)
		apply_central_impulse(Vector2(KICKS.pick_random(), KICKS.pick_random()))
```

- [ ] **Step 4: Write the scene generator**

Create `tools/make_monster_scenes.py`:

```python
"""Generate entities/monsters/*.tscn from the table below.

Static data for each monster kind lives here; behaviour lives in the script
each scene names. Re-running overwrites the scenes.

Usage: python tools/make_monster_scenes.py
"""
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "entities" / "monsters"

TEMPLATE = """[gd_scene load_steps=5 format=3]

[ext_resource type="Script" path="res://entities/monsters/{script}.gd" id="1"]
[ext_resource type="Texture2D" path="res://assets/{texture}.png" id="2"]

[sub_resource type="PhysicsMaterial" id="material"]
friction = {friction}

[sub_resource type="CircleShape2D" id="shape"]
radius = {radius}

[node name="{node}" type="RigidBody2D"]
collision_layer = 4
collision_mask = 31
mass = {mass}
physics_material_override = SubResource("material")
gravity_scale = {gravity}
lock_rotation = {lock}
contact_monitor = true
max_contacts_reported = 8
script = ExtResource("1")
{exports}
[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("shape")

[node name="Sprite2D" type="Sprite2D" parent="."]
scale = Vector2(2, 2)
texture = ExtResource("2")
hframes = {hframes}
vframes = {vframes}
frame_coords = Vector2i({frame_x}, {frame_y})
"""


def monster(name, script, texture, frame=(0, 0), px=16, radius=16, mass=20,
            friction=0.5, gravity=1.0, lock=True, **exports):
    return dict(name=name, script=script, texture=texture, frame=frame, px=px,
                radius=radius, mass=mass, friction=friction, gravity=gravity,
                lock=lock, exports=exports)


HEAVY = dict(mass=40000, friction=40000)
DOOR = dict(px=32, radius=32, mass=20000, friction=100, damaged_by_shots=False, anim_frames=2)
BOSS = dict(px=32, radius=32, mass=200, damages_player_on_touch=True)
POWERUP = dict(is_powerup=True, damaged_by_shots=False, **HEAVY)

MONSTERS = [
    monster("ball_monster", "ball_monster", "animations/ballMonster", lock=False),
    monster("spiky_ball_monster", "ball_monster", "animations/ballMonster", frame=(0, 2),
            lock=False, damages_player_on_touch=True),
    monster("jump_bot", "jump_bot", "animations/bots2", damages_player_on_touch=True, anim_frames=1),
    monster("flyer", "flyer", "animations/ballMonster", frame=(0, 3), gravity=-1.0,
            damages_player_on_touch=True),
    monster("fly_bot", "fly_bot", "animations/bots", gravity=-0.1, max_hp=3,
            damages_player_on_touch=True),
    monster("boss_bot_1", "fly_bot", "animations/bossBots", gravity=-0.1, max_hp=6,
            damages_player_on_touch=True, drift_interval_max=0.075, drift_up_max=0.0),
    monster("boss_bot_2", "fly_bot", "animations/bossBots", frame=(0, 1), gravity=-0.1, max_hp=6,
            damages_player_on_touch=True, first_fire_delay=1.0, fire_interval=0.5,
            random_spread=True),
    monster("boss_bot_3", "fly_bot", "animations/bossBots", frame=(0, 2), gravity=-0.1, max_hp=10,
            damages_player_on_touch=True),
    monster("aimer_turret", "aimer_turret", "animations/bots2", frame=(0, 2), mass=1000,
            gravity=-1.0, damages_player_on_touch=True, anim_frames=2),
    monster("defense_turret_vertical", "defense_turret_vertical", "animations/turret", mass=5,
            gravity=0.8),
    monster("hover_block", "hover_block", "sprites/chaosBlocks", frame=(1, 4), mass=4000,
            friction=20, gravity=0.0, anim_frames=1),
    monster("hand_bot", "hand_bot", "animations/bigBots1", px=32, radius=32, mass=200, max_hp=5,
            damages_player_on_touch=True, anim_frames=2),
    monster("spiky_head_monster", "spiky_head_monster", "animations/snakeHeadBoss", frame=(0, 4),
            lock=False, damages_player_on_touch=True, damaged_by_shots=False, anim_frames=1),
    monster("artifact_door", "artifact_door", "animations/artifactDoor", **DOOR),
    monster("monster_door", "monster_door", "animations/artifactDoor", frame=(0, 1), **DOOR),
    monster("monster_door_2", "monster_door", "animations/artifactDoor", frame=(0, 1),
            open_when_count=2, **DOOR),
    monster("save_point", "save_point", "animations/savePoint", **HEAVY),
    monster("hp_powerup", "powerup", "animations/collectibles", frame=(0, 2), kind="hp", **POWERUP),
    monster("fuel_powerup", "powerup", "animations/collectibles", kind="fuel", **POWERUP),
    monster("gun_powerup", "powerup", "animations/collectibles", frame=(0, 3), kind="gun", **POWERUP),
    monster("alien_artifact", "powerup", "animations/collectibles", frame=(0, 1), kind="artifact",
            **POWERUP),
    monster("orb_boss", "orb_boss", "animations/orbBoss", lock=False, max_hp=20, anim_frames=2,
            **BOSS),
    monster("fallen_extranaut", "orb_boss", "animations/fallenExtranaut", lock=False, max_hp=20,
            grenade_offset=(32, 30), lob_grenades=False, fires_when_chasing=True,
            row_per_mode=False, **BOSS),
    monster("octo_boss", "octo_boss", "animations/octoBoss", gravity=0.0, max_hp=20,
            anim_frames=1, **BOSS),
    monster("head_boss", "head_boss", "animations/snakeHeadBoss", max_hp=15, anim_frames=1, **BOSS),
]


def png_size(path):
    with open(path, "rb") as file:
        header = file.read(24)
    return struct.unpack(">II", header[16:24])


def godot_value(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return '"%s"' % value
    if isinstance(value, tuple):
        return "Vector2(%s, %s)" % value
    return repr(value)


def render(m):
    width, height = png_size(ROOT / "assets" / (m["texture"] + ".png"))
    exports = "".join("%s = %s\n" % (key, godot_value(value)) for key, value in m["exports"].items())
    return TEMPLATE.format(
        script=m["script"],
        texture=m["texture"],
        friction=float(m["friction"]),
        radius=float(m["radius"]),
        node="".join(part.capitalize() for part in m["name"].split("_")),
        mass=float(m["mass"]),
        gravity=float(m["gravity"]),
        lock=godot_value(m["lock"]),
        exports=exports,
        hframes=width // m["px"],
        vframes=height // m["px"],
        frame_x=m["frame"][0],
        frame_y=m["frame"][1],
    )


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for m in MONSTERS:
        with open(OUT / (m["name"] + ".tscn"), "w", newline="\n") as file:
            file.write(render(m))
    print("Wrote %d monster scenes" % len(MONSTERS))


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Generate the scenes**

```bash
python tools/make_monster_scenes.py && ls entities/monsters/*.tscn | wc -l
```

Expected: `Wrote 25 monster scenes` and `25`.

Only `ball_monster.tscn` and `spiky_ball_monster.tscn` can load until their scripts exist in later tasks.

- [ ] **Step 6: Run the first sections**

```bash
"$GODOT" --headless --path . --import 2>&1 | grep -c "ball_monster"
"$GODOT" --headless --path . --script res://tools/test_monsters.gd -- --only=touch 2>&1 | tail -4
```

Expected: `0` (no errors naming ball_monster). The test prints `FAIL: spiky ball hurts on touch` because the player has no health yet; `ball monsters are harmless` must not appear among the failures. A `SCRIPT ERROR` about `hp` on the player is expected here and goes away in Task 3.

- [ ] **Step 7: Commit**

```bash
git add tools/test_monsters.gd tools/make_monster_scenes.py entities/monsters
git commit -m "Add the monster base, scene generator and arena tests

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Player health, damage and death

**Files:**
- Modify: `entities/player/player.gd`
- Modify: `entities/player/player.tscn`

- [ ] **Step 1: Confirm the failing sections**

```bash
"$GODOT" --headless --path . --script res://tools/test_monsters.gd -- --only=player_death 2>&1 | tail -3
```

Expected: `player_death: FAILED` or script errors about `died`, `hit` or `hp`.

- [ ] **Step 2: Add health to the player**

Replace `entities/player/player.gd` with:

```gdscript
extends RigidBody2D
## The Extranaut: runs, jetpacks, shoots, takes damage and dies.

signal shot_fired(shot: RigidBody2D)
## Emitted once, DEATH_TIME after hp reaches zero.
signal died

const Jetpack := preload("res://entities/player/jetpack.gd")
const EnergyBallScene := preload("res://entities/projectiles/energy_ball.tscn")

## Seconds between shots, indexed by gun level - 1.
const FIRE_COOLDOWNS := [1.0, 0.8, 0.6, 0.4]
const MAX_GUN_LEVEL := 4
const WALK_FRAME_TIME := 0.06
const WALK_MIN_SPEED := 30.0
## Where a shot appears relative to the player's centre, facing right.
const MUZZLE_OFFSET := Vector2(20, 7)
const HIT_INVULNERABLE_TIME := 1.0
## While invulnerable the sprite is hidden for half of each period.
const FLASH_PERIOD := 0.06
## The original waited 5 s before respawning.
const DEATH_TIME := 2.0
const DEAD_ROW_OFFSET := 2

@export var run_speed := 200.0
## The original set horizontal velocity instantly; this reaches run_speed in 80 ms.
@export var run_accel := 2500.0
@export var thrust_accel := 1750.0
@export var shot_speed := 500.0

var jetpack := Jetpack.new()
var gun_level := 1
var max_hp := 5
var hp := 5
var artifacts := 0
## 1 facing right, -1 facing left.
var facing := 1

var _fire_cooldown := 0.0
var _walk_elapsed := 0.0
var _hit_timeout := 0.0
var _death_timer := 0.0

@onready var _sprite: Sprite2D = $Sprite2D


func _ready() -> void:
	add_to_group("player")


func is_dead() -> bool:
	return hp <= 0


func hit() -> void:
	if _hit_timeout > 0.0 or is_dead():
		return
	hp -= 1
	_hit_timeout = HIT_INVULNERABLE_TIME
	if is_dead():
		_death_timer = DEATH_TIME


## Restores the player after death. The caller positions it.
func revive() -> void:
	hp = max_hp
	_hit_timeout = 0.0
	_death_timer = 0.0
	jetpack.fuel = jetpack.max_fuel
	jetpack.stalled = false
	linear_velocity = Vector2.ZERO


func _integrate_forces(state: PhysicsDirectBodyState2D) -> void:
	var direction := 0.0
	var wants_thrust := false
	if not is_dead():
		direction = signf(Input.get_axis("move_left", "move_right"))
		wants_thrust = Input.is_action_pressed("jetpack")
	if direction != 0.0:
		facing = int(direction)
	var velocity := state.linear_velocity
	velocity.x = move_toward(velocity.x, direction * run_speed, run_accel * state.step)
	if jetpack.step(state.step, wants_thrust):
		velocity.y -= thrust_accel * state.step
	state.linear_velocity = velocity


func _physics_process(delta: float) -> void:
	if is_dead():
		if _death_timer > 0.0:
			_death_timer -= delta
			if _death_timer <= 0.0:
				died.emit()
	else:
		_hit_timeout = maxf(_hit_timeout - delta, 0.0)
		_check_contacts()
		_fire_cooldown = maxf(_fire_cooldown - delta, 0.0)
		if Input.is_action_pressed("fire") and _fire_cooldown <= 0.0:
			_fire()
	_animate(delta)


## Damage and pickups from whatever the player is touching. Checked every
## frame, not only on first contact, so standing against a monster keeps hurting.
func _check_contacts() -> void:
	for body in get_colliding_bodies():
		if body.is_in_group("enemy_shots"):
			hit()
		elif body.is_in_group("monsters"):
			if body.damages_player_on_touch:
				hit()
			if body.is_powerup:
				body.apply_powerup(self)


func _fire() -> void:
	var shot: RigidBody2D = EnergyBallScene.instantiate()
	shot.position = global_position + Vector2(MUZZLE_OFFSET.x * facing, MUZZLE_OFFSET.y)
	shot.linear_velocity = Vector2(shot_speed * facing, 0.0)
	shot_fired.emit(shot)
	_fire_cooldown = FIRE_COOLDOWNS[clampi(gun_level, 1, MAX_GUN_LEVEL) - 1]


func _animate(delta: float) -> void:
	var row := 0 if facing > 0 else 1
	if is_dead():
		_sprite.frame_coords = Vector2i(0, row + DEAD_ROW_OFFSET)
		_sprite.visible = true
		return
	_sprite.frame_coords.y = row
	_sprite.visible = _hit_timeout <= 0.0 or fmod(_hit_timeout, FLASH_PERIOD) < FLASH_PERIOD / 2.0
	if absf(linear_velocity.x) > WALK_MIN_SPEED:
		_walk_elapsed += delta
		if _walk_elapsed >= WALK_FRAME_TIME:
			_walk_elapsed -= WALK_FRAME_TIME
			_sprite.frame_coords.x = (_sprite.frame_coords.x + 1) % _sprite.hframes
```

- [ ] **Step 3: Turn on contact reporting**

In `entities/player/player.tscn`, add these two lines directly after the line `continuous_cd = 1`:

```
contact_monitor = true
max_contacts_reported = 8
```

- [ ] **Step 4: Run the sections that are now complete**

```bash
for s in touch player_death enemy_shots; do "$GODOT" --headless --path . --script res://tools/test_monsters.gd -- --only=$s 2>&1 | tee /tmp/out.txt | grep -E "ok$|FAILED$|FAIL:"; grep -c "SCRIPT ERROR" /tmp/out.txt; done
```

Expected: `touch_damage: ok`, `player_death: ok`, `enemy_shots: ok`, each followed by `0`.

- [ ] **Step 5: Confirm the earlier checks still pass**

```bash
"$GODOT" --headless --path . --script res://tools/test_campaign.gd 2>&1 | tail -1
```

Expected: `campaign test passed`.

- [ ] **Step 6: Commit**

```bash
git add entities/player
git commit -m "Give the player health, contact damage and death

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Enemy behaviours

**Files:**
- Create: `entities/monsters/jump_bot.gd`, `flyer.gd`, `fly_bot.gd`, `aimer_turret.gd`, `defense_turret_vertical.gd`, `hover_block.gd`, `hand_bot.gd`, `spiky_head_monster.gd`, `orb_boss.gd`, `octo_boss.gd`, `head_boss.gd`

- [ ] **Step 1: JumpBot**

Create `entities/monsters/jump_bot.gd`:

```gdscript
extends "res://entities/monsters/monster.gd"
## Hops once a second, toward the player when it is within 150 px on both axes.

const NEAR := 150.0

var _jump_timer := 1.0
## While positive the bot shows its jumping frame.
var _airborne_timer := 0.5


func _behave(delta: float, player: Node2D) -> void:
	_airborne_timer -= delta
	_jump_timer -= delta
	if _jump_timer < 0.0:
		_jump_timer = 1.0
		_airborne_timer = 0.5
		var push := 0.0
		if player != null:
			var to_player := player_corner(player) - global_position
			if absf(to_player.x) < NEAR and absf(to_player.y) < NEAR:
				push = 5000.0 if to_player.x > 0.0 else -5000.0
		apply_central_impulse(Vector2(push, -8000.0))


func _animate(_delta: float) -> void:
	sprite.frame_coords.x = 1 if _airborne_timer > 0.0 else 0
```

- [ ] **Step 2: Flyer**

Create `entities/monsters/flyer.gd`:

```gdscript
extends "res://entities/monsters/monster.gd"
## Floats upward and is knocked down and sideways at random intervals.

const KICKS := [-5000.0, 0.0, 5000.0]

var _kick_timer := randf_range(0.0, 5.0)


func _behave(delta: float, _player: Node2D) -> void:
	_kick_timer -= delta
	if _kick_timer < 0.0:
		_kick_timer = randf_range(0.0, 3.0)
		apply_central_impulse(Vector2(KICKS.pick_random(), randf_range(5000.0, 10000.0)))
```

- [ ] **Step 3: FlyBot and the three BossBots**

Create `entities/monsters/fly_bot.gd`:

```gdscript
extends "res://entities/monsters/monster.gd"
## Hovers with small random drifts and fires a pair of shots diagonally
## downward. Used by FlyBot and BossBot1 to 3, which differ in the exports.

const DRIFTS := [-1000.0, 0.0, 1000.0]
const SHOT_IMPULSE := 7000.0
const MUZZLE := 32.0

@export var first_fire_delay := 2.0
@export var fire_interval := 2.0
## Fire each shot with a random impulse up to SHOT_IMPULSE on each axis,
## not straight along the diagonal.
@export var random_spread := false
@export var drift_interval_max := 0.1
## Largest upward drift impulse. BossBot1 only drifts downward.
@export var drift_up_max := 1000.0

var _drift_timer := randf_range(0.0, 0.1)
var _fire_timer := 0.0


func _ready() -> void:
	super()
	_fire_timer = first_fire_delay


func _behave(delta: float, _player: Node2D) -> void:
	_drift_timer -= delta
	if _drift_timer < 0.0:
		_drift_timer = randf_range(0.0, drift_interval_max)
		apply_central_impulse(Vector2(DRIFTS.pick_random(), randf_range(-drift_up_max, 1000.0)))
	_fire_timer -= delta
	if _fire_timer < 0.0:
		_fire_timer = fire_interval
		for side in [1.0, -1.0]:
			var impulse := Vector2(side * SHOT_IMPULSE, SHOT_IMPULSE)
			if random_spread:
				impulse = Vector2(side * randf_range(0.0, SHOT_IMPULSE), randf_range(0.0, SHOT_IMPULSE))
			fire(EnemyEnergyBallScene, Vector2(side * MUZZLE, 0.0), impulse)
```

- [ ] **Step 4: AimerTurret**

Create `entities/monsters/aimer_turret.gd`:

```gdscript
extends "res://entities/monsters/monster.gd"
## Fires an aimed shot at the player every 2 s.

## Muzzle offset per axis, by the sign of the aim. The original's values are
## lopsided: a shot aimed up and left spawns inside the turret and dies.
const MUZZLE_POSITIVE := 36.0
const MUZZLE_NEGATIVE := -8.0

var _fire_timer := 2.0


func _behave(delta: float, player: Node2D) -> void:
	_fire_timer -= delta
	if _fire_timer < 0.0 and player != null:
		_fire_timer = 2.0
		var impulse := aim_at(player)
		var offset := Vector2(
			MUZZLE_POSITIVE if impulse.x > 0.0 else MUZZLE_NEGATIVE,
			MUZZLE_POSITIVE if impulse.y > 0.0 else MUZZLE_NEGATIVE
		)
		fire(EnemyEnergyBallScene, offset, impulse)
```

- [ ] **Step 5: DefenseTurretVertical**

Create `entities/monsters/defense_turret_vertical.gd`:

```gdscript
extends "res://entities/monsters/monster.gd"
## Lobs a grenade upward every 3 s.

var _fire_timer := randf_range(0.0, 3.0)


func _behave(delta: float, _player: Node2D) -> void:
	_fire_timer -= delta
	if _fire_timer < 0.0:
		_fire_timer = 3.0
		var impulse := Vector2(randf_range(-10000.0, 10000.0), randf_range(-15000.0, -10000.0))
		fire(EnergyGrenadeScene, Vector2(8, -32), impulse)
```

- [ ] **Step 6: HoverBlock**

Create `entities/monsters/hover_block.gd`:

```gdscript
extends "res://entities/monsters/monster.gd"
## A heavy floating block that springs gently back to where it was placed.
## It works as a platform and can be shot away.

## Impulse per pixel of displacement per frame at 60 fps, as in the original.
const SPRING := 2.0

var _home := Vector2.ZERO


func _ready() -> void:
	super()
	_home = global_position


func _behave(delta: float, _player: Node2D) -> void:
	apply_central_impulse((_home - global_position) * SPRING * delta * 60.0)
```

- [ ] **Step 7: HandBot**

Create `entities/monsters/hand_bot.gd`:

```gdscript
extends "res://entities/monsters/monster.gd"
## A big bot that thrusts upward while the player is above it and within
## 100 px horizontally.

const NEAR_X := 100.0
## Upward impulse per frame at 60 fps, as in the original.
const LIFT := 5000.0


func _behave(delta: float, player: Node2D) -> void:
	if player == null:
		return
	var corner := player_corner(player)
	if absf(global_position.x - corner.x) < NEAR_X and corner.y < global_position.y:
		apply_central_impulse(Vector2(0.0, -LIFT * delta * 60.0))
```

- [ ] **Step 8: SpikyHeadMonster**

Create `entities/monsters/spiky_head_monster.gd`:

```gdscript
extends "res://entities/monsters/monster.gd"
## An indestructible spiked ball in the head boss's room. It dies when three
## monsters remain in the room.

const KICKS := [-5000.0, 0.0, 5000.0]
const DIE_AT_COUNT := 3

var _kick_timer := 1.0


func _behave(delta: float, _player: Node2D) -> void:
	if monsters_in_room() == DIE_AT_COUNT:
		die()
		return
	_kick_timer -= delta
	if _kick_timer < 0.0:
		_kick_timer = 1.0
		apply_central_impulse(Vector2(KICKS.pick_random(), KICKS.pick_random()))
```

- [ ] **Step 9: OrbBoss and FallenExtranaut**

Create `entities/monsters/orb_boss.gd`:

```gdscript
extends "res://entities/monsters/monster.gd"
## Alternates every 5 to 10 s between chasing the player and flying upward
## while throwing grenades. Used by OrbBoss and FallenExtranaut.

enum Mode { CHASING, FLYING }

const DRIFTS := [-1000.0, 0.0, 1000.0]
const AIMED_MUZZLE := 36.0

@export var grenade_offset := Vector2(32, -32)
## Throw grenades upward. When false they are thrown flat.
@export var lob_grenades := true
## Also fire an aimed shot every 2 s while chasing.
@export var fires_when_chasing := false
## Show sprite row 0 when chasing and row 1 when flying.
@export var row_per_mode := true

var _mode: Mode = [Mode.CHASING, Mode.FLYING].pick_random()
var _mode_timer := randf_range(5.0, 10.0)
var _force_timer := randf_range(0.0, 5.0)
var _grenade_timer := 1.0
var _fire_timer := 2.0


func _behave(delta: float, player: Node2D) -> void:
	_mode_timer -= delta
	if _mode_timer <= 0.0:
		_mode_timer = randf_range(5.0, 10.0)
		_mode = Mode.FLYING if _mode == Mode.CHASING else Mode.CHASING
	if row_per_mode:
		sprite.frame_coords.y = 0 if _mode == Mode.CHASING else 1
	_force_timer -= delta
	if _mode == Mode.FLYING:
		_fly(delta)
	elif player != null:
		_chase(delta, player)


func _fly(delta: float) -> void:
	if _force_timer < 0.0:
		_force_timer = randf_range(0.0, 0.1)
		apply_central_impulse(Vector2(DRIFTS.pick_random(), -15000.0))
	_grenade_timer -= delta
	if _grenade_timer <= 0.0:
		_grenade_timer = 1.0
		for i in 3:
			var up := randf_range(-15000.0, -10000.0) if lob_grenades else 0.0
			fire(EnergyGrenadeScene, grenade_offset, Vector2(randf_range(-10000.0, 10000.0), up))


func _chase(delta: float, player: Node2D) -> void:
	var corner := player_corner(player)
	if _force_timer < 0.0:
		_force_timer = 0.06
		var sideways := 5000.0 if corner.x > global_position.x else -5000.0
		var vertical := 5000.0 if corner.y > global_position.y else -15000.0
		apply_central_impulse(Vector2(sideways, vertical))
	if fires_when_chasing:
		_fire_timer -= delta
		if _fire_timer <= 0.0:
			_fire_timer = 2.0
			var impulse := aim_at(player)
			var offset := Vector2(
				AIMED_MUZZLE if impulse.x > 0.0 else -AIMED_MUZZLE,
				AIMED_MUZZLE if impulse.y > 0.0 else -AIMED_MUZZLE
			)
			fire(EnemyEnergyBallScene, offset, impulse)
```

- [ ] **Step 10: OctoBoss**

Create `entities/monsters/octo_boss.gd`:

```gdscript
extends "res://entities/monsters/monster.gd"
## Hovers, fires an aimed shot every second, drops three grenades every 5 s,
## and lurches every 2 s, harder the more it has been hurt.

const AIMED_MUZZLE := 34.0

var _shoot_timer := 1.0
var _grenade_timer := 5.0
var _lurch_timer := 2.0


func _behave(delta: float, player: Node2D) -> void:
	_shoot_timer -= delta
	if _shoot_timer <= 0.0 and player != null:
		_shoot_timer = 1.0
		var impulse := aim_at(player)
		var offset := Vector2(
			AIMED_MUZZLE if impulse.x > 0.0 else -AIMED_MUZZLE,
			AIMED_MUZZLE if impulse.y > 0.0 else -AIMED_MUZZLE
		)
		fire(EnemyEnergyBallScene, offset, impulse)

	_grenade_timer -= delta
	if _grenade_timer <= 0.0:
		_grenade_timer = 5.0
		for i in 3:
			fire(EnergyGrenadeScene, Vector2(0, 48), Vector2(randf_range(-10000.0, 10000.0), 0.0))

	_lurch_timer -= delta
	if _lurch_timer <= 0.0:
		_lurch_timer = 2.0
		var extra := 2000.0 * (max_hp - hp)
		var sideways: float = [30000.0 + extra, -30000.0 - extra].pick_random()
		var vertical: float = [1000.0 + extra, -1000.0 - extra].pick_random()
		apply_central_impulse(Vector2(sideways, vertical))
```

- [ ] **Step 11: HeadBoss**

Create `entities/monsters/head_boss.gd`:

```gdscript
extends "res://entities/monsters/monster.gd"
## A stationary head that fires aimed shots faster as it is hurt, and is
## shielded for 2 s after each hit. Its frame follows the player's height.

const SHIELD_TIME := 2.0
## The original aimed 32 px down and right of the player's sprite corner.
const AIM_LEAD := Vector2(32, 32)
## Muzzle offset when firing right and when firing left. The right-hand one
## overlaps the boss, so those shots die at once, as in the original.
const MUZZLE_RIGHT := Vector2(34, -16)
const MUZZLE_LEFT := Vector2(-50, -16)

var _shoot_timer := 1.0
var _shield := 0.0


func _behave(delta: float, player: Node2D) -> void:
	_shield -= delta
	sprite.frame_coords.y = 1 if _shield > 0.0 else 0
	if player == null:
		return
	_shoot_timer -= delta
	if _shoot_timer <= 0.0:
		_shoot_timer = 1.0 - (max_hp - hp) * 0.05
		var impulse := aim_at(player, AIM_LEAD)
		fire(EnemyEnergyBallScene, MUZZLE_RIGHT if impulse.x > 0.0 else MUZZLE_LEFT, impulse)
	var height := player_corner(player).y - global_position.y
	if height < -500.0:
		sprite.frame_coords.x = 2
	elif height < -100.0:
		sprite.frame_coords.x = 1
	else:
		sprite.frame_coords.x = 0


func hit() -> void:
	if _shield <= 0.0:
		_shield = SHIELD_TIME
		super()
```

- [ ] **Step 12: Run the sections these complete**

```bash
"$GODOT" --headless --path . --import 2>&1 | grep -i -E "parse error"
for s in turrets movers; do "$GODOT" --headless --path . --script res://tools/test_monsters.gd -- --only=$s 2>&1 | tee /tmp/out.txt | grep -E "ok$|FAILED$|FAIL:"; grep -c "SCRIPT ERROR" /tmp/out.txt; done
```

Expected: no parse errors for the scripts in this task (errors naming `artifact_door`, `monster_door`, `save_point` or `powerup` are expected until Task 5), then `turrets: ok`, `movers: ok`, each followed by `0`.

- [ ] **Step 13: Commit**

```bash
git add entities/monsters
git commit -m "Port enemy behaviours from monster.py

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Doors, save points and powerups

**Files:**
- Create: `entities/monsters/artifact_door.gd`, `monster_door.gd`, `save_point.gd`, `powerup.gd`

- [ ] **Step 1: ArtifactDoor**

Create `entities/monsters/artifact_door.gd`:

```gdscript
extends "res://entities/monsters/monster.gd"
## Blocks the way until the player holds all four alien artifacts.

const ARTIFACTS_NEEDED := 4


func _behave(_delta: float, player: Node2D) -> void:
	if player != null and player.artifacts >= ARTIFACTS_NEEDED:
		die()
```

- [ ] **Step 2: MonsterDoor**

Create `entities/monsters/monster_door.gd`:

```gdscript
extends "res://entities/monsters/monster.gd"
## Blocks the way until the room is cleared. The count includes this door and
## every other monster-class entity in the room, as in the original.

## MonsterDoor opens at 1 (only the door left); MonsterDoor2 opens at 2.
@export var open_when_count := 1


func _behave(_delta: float, _player: Node2D) -> void:
	if monsters_in_room() == open_when_count:
		die()
```

- [ ] **Step 3: SavePoint**

Create `entities/monsters/save_point.gd`:

```gdscript
extends "res://entities/monsters/monster.gd"
## Shoot it to save. It activates once per visit to the room.

var activated := false


func _integrate_forces(state: PhysicsDirectBodyState2D) -> void:
	state.linear_velocity = Vector2.ZERO


func hit() -> void:
	if not activated:
		activated = true
		sprite.frame_coords.y = 1
		save_requested.emit(self)
```

- [ ] **Step 4: Powerups**

Create `entities/monsters/powerup.gd`:

```gdscript
extends "res://entities/monsters/monster.gd"
## A pickup applied when the player touches it. Used by HpPowerup, FuelPowerup,
## GunPowerup and AlienArtifact, which differ in kind.

const FUEL_BONUS := 500.0
const MAX_GUN_LEVEL := 4

## One of "hp", "fuel", "gun", "artifact".
@export var kind := "hp"

var _applied := false


func _integrate_forces(state: PhysicsDirectBodyState2D) -> void:
	state.linear_velocity = Vector2.ZERO


func apply_powerup(player: Node2D) -> void:
	if _applied:
		return
	_applied = true
	match kind:
		"hp":
			player.max_hp += 1
			player.hp = player.max_hp
		"fuel":
			player.jetpack.max_fuel += FUEL_BONUS
		"gun":
			player.gun_level = mini(player.gun_level + 1, MAX_GUN_LEVEL)
		"artifact":
			player.artifacts += 1
	save_requested.emit(self)
	die()
```

- [ ] **Step 5: Run the whole arena test**

```bash
"$GODOT" --headless --path . --import 2>&1 | grep -i -E "parse error"
"$GODOT" --headless --path . --script res://tools/test_monsters.gd 2>&1 | tee /tmp/out.txt | grep -E "ok$|FAILED$|FAIL:|test passed|test FAILED"; grep -c "SCRIPT ERROR" /tmp/out.txt
```

Expected: no parse errors, ten `ok` lines, `monster test passed`, and `0`.

- [ ] **Step 6: Commit**

```bash
git add entities/monsters
git commit -m "Add doors, save points and powerups

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Rooms instance real monsters

**Files:**
- Modify: `tools/smoke_test.gd`
- Modify: `tools/import_world.gd`
- Delete: `world/monster_spawn.gd`
- Regenerate: `world/rooms/*.tscn`

- [ ] **Step 1: Add the failing check**

In `tools/smoke_test.gd`, add these lines directly before the line `for wall in room.get_node("Walls").get_children():`:

```gdscript
	for entity in room.get_node("Entities").get_children():
		if not entity.is_in_group("monsters"):
			_fail("%s entity %s is not a monster" % [path, entity.name])
			break
```

- [ ] **Step 2: Run it to verify it fails**

```bash
"$GODOT" --headless --path . --script res://tools/smoke_test.gd 2>&1 | tail -1
```

Expected: `smoke test FAILED` with one failure per room that has monsters.

- [ ] **Step 3: Make the importer require monster scenes**

In `tools/import_world.gd`:

Delete the line:

```gdscript
const MonsterSpawnScript := preload("res://world/monster_spawn.gd")
```

Replace the whole `_build_entities` function with:

```gdscript
func _build_entities(monsters: Array) -> Node2D:
	var entities := Node2D.new()
	entities.name = "Entities"
	for i in monsters.size():
		var kind: String = monsters[i][0]
		var scene: PackedScene = load(MONSTER_SCENE % kind.to_snake_case())
		var node: Node2D = scene.instantiate()
		node.name = "%s%d" % [kind, i]
		node.position = Vector2(monsters[i][1], monsters[i][2])
		entities.add_child(node)
	return entities
```

Then delete the marker script:

```bash
git rm -q world/monster_spawn.gd
rm -f world/monster_spawn.gd.uid
```

- [ ] **Step 4: Regenerate and verify**

```bash
"$GODOT" --headless --path . --script res://tools/import_world.gd 2>&1 | tail -1
"$GODOT" --headless --path . --script res://tools/smoke_test.gd 2>&1 | tee /tmp/out.txt | tail -1; grep -c "SCRIPT ERROR" /tmp/out.txt
grep -c "entities/monsters/save_point.tscn" world/rooms/room_4_2.tscn
```

Expected: `imported 100 rooms`, `smoke test passed: 100 rooms`, `0`, and `1`.

The smoke test steps every room with no player in the tree, so this also proves every behaviour copes with a missing player.

- [ ] **Step 5: Commit**

```bash
git add -A tools world
git commit -m "Instance real monster scenes in rooms

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Campaign wiring, checkpoint and respawn

**Files:**
- Modify: `tools/test_campaign.gd`
- Modify: `scenes/campaign.gd`

- [ ] **Step 1: Add the failing checks**

In `tools/test_campaign.gd`, find these two lines in `_run`:

```gdscript
	root.remove_child(campaign)
	campaign.free()
	await _check_one_tile_shaft()
```

and insert directly before them:

```gdscript
	await _check_checkpoint_and_respawn(campaign, player)
	_check_powerups_taken(campaign)
```

Then add these two functions directly before `func _check_exit_rules() -> void:`:

```gdscript
## Runs in room (5, 2), reached by the transition check above.
func _check_checkpoint_and_respawn(campaign: Node2D, player: RigidBody2D) -> void:
	_expect(campaign.checkpoint == Vector2i(4, 2), "the checkpoint starts at the start room")
	# Dying returns the player to the checkpoint room with full hp.
	player.revive()
	player.hp = 1
	player.hit()
	var waited := 0
	while campaign.grid != Vector2i(4, 2) and waited < 180:
		await physics_frame
		waited += 1
	_expect(campaign.grid == Vector2i(4, 2), "death respawns in the checkpoint room, grid %s" % campaign.grid)
	_expect(player.hp == player.max_hp and not player.is_dead(), "respawn restores full hp")
	var local: Vector2 = player.global_position - campaign.room.position
	_expect(local.distance_to(Vector2(480, 352)) < 80.0, "respawn is at the room's player start, at %s" % local)
	_expect(campaign.get_node("World").get_child_count() == 1, "only the checkpoint room is loaded")
	await _frames(30)

	# Shooting the start room's save point sets the checkpoint and heals.
	var save_point: Node = campaign.room.get_node("Entities").get_child(0)
	campaign.checkpoint = Vector2i(0, 0)
	player.hp = 2
	save_point.hit()
	_expect(campaign.checkpoint == Vector2i(4, 2), "a save point sets the checkpoint")
	_expect(player.hp == player.max_hp, "a save point heals the player")


func _check_powerups_taken(campaign: Node2D) -> void:
	var world = JSON.parse_string(FileAccess.get_file_as_string("res://tools/zorta.json"))
	var at := Vector2i(-1, -1)
	for data in world.rooms:
		for m in data.monsters:
			if m[0] == "HpPowerup":
				at = Vector2i(int(data.x), int(data.y))
	_expect(at != Vector2i(-1, -1), "found a room with an hp powerup")
	var fresh: Node2D = campaign.load_room(at)
	_expect(_count_powerups(fresh) == 1, "an untouched room has its powerup")
	fresh.free()
	campaign.powerups_taken[at] = true
	var revisited: Node2D = campaign.load_room(at)
	_expect(_count_powerups(revisited) == 0, "a taken powerup does not come back")
	revisited.free()
	campaign.powerups_taken.erase(at)


func _count_powerups(room: Node2D) -> int:
	var count := 0
	for entity in room.get_node("Entities").get_children():
		if entity.is_powerup:
			count += 1
	return count


```

- [ ] **Step 2: Run it to verify it fails**

```bash
"$GODOT" --headless --path . --script res://tools/test_campaign.gd 2>&1 | grep -E "FAIL|SCRIPT ERROR" | head -3
```

Expected: errors about `checkpoint` or `load_room` not existing on the campaign.

- [ ] **Step 3: Wire the campaign**

Replace `scenes/campaign.gd` with:

```gdscript
extends Node2D
## The campaign: owns the current room, the player, shots and the camera,
## moves between rooms when the player crosses an edge, and tracks the
## checkpoint the player respawns at.
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
## The room the player respawns in. Set by save points and powerups.
var checkpoint := START_ROOM
## Rooms (Vector2i keys) whose powerup has been collected.
var powerups_taken := {}

## False from a transition until the player has left every exit zone, so
## arriving inside the opposite zone does not bounce straight back.
var _exits_armed := false
var _sliding := false

@onready var _world: Node2D = $World
@onready var _player: RigidBody2D = $Player
@onready var _shots: Node2D = $Shots
@onready var _camera: Camera2D = $Camera2D
@onready var _status_label: Label = $Hud/Fuel


func _ready() -> void:
	Controls.setup()
	var shot_path := ""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--room="):
			var parts := arg.trim_prefix("--room=").split(",")
			grid = Vector2i(int(parts[0]), int(parts[1]))
		elif arg.begins_with("--shot="):
			shot_path = arg.trim_prefix("--shot=")

	_player.shot_fired.connect(_on_shot_fired)
	_player.died.connect(_respawn)
	room = load_room(grid)
	_world.add_child(room)
	_place_player_at_start()

	if shot_path != "":
		await get_tree().create_timer(1.0).timeout
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png(shot_path)
		get_tree().quit()


func _process(_delta: float) -> void:
	_status_label.text = "HP %d\nFUEL\n%d\nART %d" % [_player.hp, int(_player.jetpack.fuel), _player.artifacts]


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
		if entity.is_powerup and powerups_taken.has(at):
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
	grid = checkpoint
	room = load_room(grid)
	_world.add_child(room)
	_player.revive()
	_place_player_at_start()


func _place_player_at_start() -> void:
	var start: Vector2 = room.player_start if room.has_player_start else ROOM_SIZE / 2.0
	_player.global_position = room.position + start
	_camera.position = room.position + VIEW_CENTER
	_exits_armed = false


func _clear_shots() -> void:
	for shot in _shots.get_children():
		shot.queue_free()


func _on_shot_fired(shot: RigidBody2D) -> void:
	shot.bounds = Rect2(room.position, ROOM_SIZE)
	_shots.add_child(shot)


## A save point was activated or a powerup collected in the current room.
func _on_save_requested(source: Node) -> void:
	checkpoint = grid
	_player.hp = _player.max_hp
	if source.is_powerup:
		powerups_taken[grid] = true
```

- [ ] **Step 4: Run every check**

```bash
python -m unittest discover -s tools -p "test_*.py" 2>&1 | tail -1
for t in smoke_test test_jetpack test_monsters test_campaign; do "$GODOT" --headless --path . --script res://tools/$t.gd 2>&1 | tee /tmp/out.txt | tail -1; grep -c "SCRIPT ERROR" /tmp/out.txt; done
```

Expected: `OK`, then `smoke test passed: 100 rooms`, `jetpack test passed`, `monster test passed`, `campaign test passed`, each followed by `0`.

- [ ] **Step 5: Look at a populated room**

```bash
mkdir -p ../extranaut-shots
"$GODOT" --path . -- --room=5,5 --shot="$(cd .. && pwd -W)/extranaut-shots/monsters_5_5.png" 2>&1 | grep -i error
```

Open the screenshot. Check: monster sprites are drawn whole (not sliced across frames), sit at sensible places, and are behind any foreground tiles.

- [ ] **Step 6: Commit**

```bash
git add scenes tools
git commit -m "Wire monsters into the campaign with checkpoint and respawn

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Done when

- All five checks in Task 7 Step 4 pass with no script errors.
- Rooms contain their monsters, which move, shoot and can be killed.
- The player takes damage, flashes while invulnerable, dies at 0 HP and respawns at the last checkpoint with full HP.
- Shooting a save point or collecting a powerup sets the checkpoint. A collected powerup does not return when the room is re-entered.
- The author has played it and reported on difficulty: whether enemies and bosses feel like the original, given the player's smaller body.
