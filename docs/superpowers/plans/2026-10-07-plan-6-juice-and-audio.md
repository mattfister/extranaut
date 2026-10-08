# Extranaut Port, Plan 6: Juice and Audio

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The game has its original music and sound effects, particles for exhaust and explosions, screen shake, a hit flash and a fade on death.

**Architecture:** An `Audio` autoload plays effects from a small pool of players and crossfades music between two players. A `ParticleField` node in the campaign ports the original's hand-rolled particle system: it stores particles in an array and draws them itself. A `ScreenFx` node shakes the camera and owns a full-room overlay for flashes and fades. Monsters, shots and the player reach the field and the screen effects through groups, so they work unchanged in test arenas that have neither.

**Tech Stack:** Godot 4.7 GDScript, headless `--script` tests.

**Spec:** `docs/superpowers/specs/2026-10-07-extranaut-godot-port-design.md`

**This is plan 6 of 7**, executed before plan 5 so that Chaosnaut is built with sound and effects available.

---

## Conventions for every task

- Shell is Git Bash. Run commands from the repository root.
- Godot binary:

```bash
GODOT="/c/Users/mattf/Desktop/godot47/Godot_v4.7-stable_win64_console.exe"
```

- GDScript files are indented with tabs.
- Work on branch `plan-6-juice-and-audio`.
- Commit messages end with the attribution trailer lines in force for the session.
- Every whole-file code block is introduced by ``Create `path`:`` or ``Replace `path` with:``. Write the block to that path exactly.
- Run every Godot test as `timeout 200 "$GODOT" ...`. A script error inside a test can stop it before its `quit()` call.
- Each test's output must contain no `SCRIPT ERROR` lines and no lines starting `ERROR`.

## Facts from the original

Sounds (`sounds.py` and callers). All files are in `assets/sounds/`.

| Event | Sound |
| --- | --- |
| Player fires | `shoot` |
| Player or monster hit and surviving | `hit` |
| Jetpack thrusting | `jet`, with each puff of flame |
| Jetpack held while empty | `packEmpty`, with each puff of smoke |
| BallMonster, SpikyBallMonster, Flyer die | `deadAlien` |
| Any bot, turret or boss dies; SpikyHeadMonster dies | `explode` |
| HP, fuel, gun powerup, alien artifact | `armorUpgrade`, `jetpackUpgrade`, `gunUpgrade`, `alienArtifactAcquired` |
| Game starts | `extranautTitle` |

Music: the title plays `ruinsCore`. A room with a music name plays it; a room without one keeps whatever is playing. The original set music volume to 0.3 on a fresh start and 0.1 after a room change; this port uses one level.

Particles (`particle.py`). Each is a 16 px animated frame drawn at 2x, cycling 4 frames at 60 ms. Velocities below are converted from the original's pixels per millisecond.

| Kind | Sheet and row | Velocity x | Velocity y | Life | Friction |
| --- | --- | --- | --- | --- | --- |
| explosion | botParticles 0 | -100 to 100 | -100 to 100 | 0.8 to 1.5 s | 0 |
| exhaust | botParticles 0 | -10 to 10 | 50 to 100 | 0.2 to 0.3 s | 0 |
| jet_fire | jetPackParticles 0 | -100 to 100 | 50 to 100 | 0.8 to 1.5 s | 0 |
| jet_smoke | jetPackParticles 2 | -100 to 100 | -100 to 100 | 0.8 to 1.5 s | 100 px/s² |
| energy | jetPackParticles 3 | -100 to 100 | -100 to 100 | 0.4 to 0.6 s | 0 |

Emission:

- Death explosions: 40 particles for JumpBot, HandBot, FlyBot, AimerTurret and the three BossBots; 100 for OrbBoss, FallenExtranaut and OctoBoss; 200 for HeadBoss.
- Exhaust: 1 to 5 particles every 30 ms under FlyBot and the BossBots; 1 every 30 ms under OctoBoss, and under HandBot while it thrusts.
- Jetpack: 1 to 5 particles every 30 ms while up is held, flame while thrusting and smoke while empty.
- A grenade bursts into 10 to 20 energy particles when it explodes.
- Particles are cleared when the room changes.

## Additions that were not in the original

- Music crossfades over 1 second when the track changes.
- Screen shake on player hits and on explosions, stronger for the 100 and 200 particle bosses.
- A brief white flash when the player is hit.
- The screen fades to black during the 2 second death pause and fades back in on respawn.
- `intro` plays on the intro screen. The original only played it when sound was toggled back on.
- The same effect is not restarted within 50 ms, so forty simultaneous explosions are one sound.

## File structure

| Path | Responsibility |
| --- | --- |
| `audio/audio.gd` | Autoload `Audio`: effects and crossfading music |
| `effects/particle_field.gd` | Stores, advances and draws particles |
| `effects/screen_fx.gd` | Camera shake, flash and fade overlay |
| `tools/test_effects.gd` | Tests for the three above |
| `entities/monsters/monster.gd` | Hit and death sounds, death particles, exhaust helper |
| `entities/monsters/fly_bot.gd`, `hand_bot.gd`, `octo_boss.gd`, `powerup.gd` | Exhaust and pickup sounds |
| `tools/make_monster_scenes.py` | Death sound and particle count per kind |
| `entities/projectiles/energy_grenade.gd` | Burst on explosion |
| `entities/player/player.gd` | Shot, hit and jet sounds; jet particles; `death_started` |
| `scenes/campaign.gd`, `campaign.tscn` | Hosts the field and screen effects; room music; death fade |
| `scenes/title.gd`, `scenes/main.gd` | Title music and jingles |
| `project.godot` | Registers the autoload |

---

### Task 1: Audio autoload

**Files:**
- Create: `tools/test_effects.gd`
- Create: `audio/audio.gd`
- Modify: `project.godot`

- [ ] **Step 1: Write the failing test**

The file tests all three new systems. Sections for the particle field and screen effects fail until Task 2.

Create `tools/test_effects.gd`:

```gdscript
extends SceneTree
## Tests for the Audio autoload, ParticleField and ScreenFx.
## Run: godot --headless --path . --script res://tools/test_effects.gd

const EFFECTS := [
	"shoot", "hit", "jet", "packEmpty", "deadAlien", "explode", "armorUpgrade",
	"jetpackUpgrade", "gunUpgrade", "alienArtifactAcquired", "extranautTitle",
	"intro", "newWave",
]

var _failures := 0


func _initialize() -> void:
	_run()


func _run() -> void:
	await process_frame
	_test_sounds_exist()
	await _test_audio()
	_test_particle_field()
	await _test_screen_fx()
	print("effects test passed" if _failures == 0 else "effects test FAILED: %d failures" % _failures)
	quit(1 if _failures > 0 else 0)


func _test_sounds_exist() -> void:
	var tracks := {"ruinsCore": true, "chaosNaut": true}
	var world = JSON.parse_string(FileAccess.get_file_as_string("res://tools/zorta.json"))
	for room in world.rooms:
		if room.music != null:
			tracks[room.music] = true
	for sound in EFFECTS + tracks.keys():
		_expect(ResourceLoader.exists("res://assets/sounds/%s.ogg" % sound), "sound %s exists" % sound)


func _test_audio() -> void:
	var audio: Node = root.get_node("Audio")
	audio.play("shoot")
	_expect(audio.is_playing("shoot"), "an effect plays")
	_expect(not audio.is_playing("explode"), "other effects are not reported as playing")
	audio.play("shoot")
	_expect(audio.playing_count("shoot") == 1, "an effect is not restarted within the retrigger gap")
	audio.play("no_such_sound")
	_expect(not audio.is_playing("no_such_sound"), "a missing sound is ignored")

	_expect(audio.current_music() == "", "no music at first")
	audio.play_music("zortaSurface")
	_expect(audio.current_music() == "zortaSurface", "music starts")
	_expect(audio.music_player().playing and audio.music_player().stream.loop, "music plays and loops")
	var first: AudioStreamPlayer = audio.music_player()
	audio.play_music("zortaSurface")
	_expect(audio.music_player() == first, "asking for the current track does not restart it")
	audio.play_music("pyriteZone")
	_expect(audio.current_music() == "pyriteZone" and audio.music_player() != first, "a new track takes over on the other player")
	await create_timer(audio.FADE_TIME + 0.3).timeout
	_expect(not first.playing, "the old track stops after the crossfade")
	_expect(is_equal_approx(audio.music_player().volume_db, audio.MUSIC_VOLUME_DB), "the new track reaches full music volume")


func _test_particle_field() -> void:
	var field: Node2D = load("res://effects/particle_field.gd").new()
	root.add_child(field)
	_expect(field.is_in_group("particle_field"), "the field joins its group")
	field.emit("explosion", Vector2(100, 100), 40)
	_expect(field.count() == 40, "emit adds particles")
	field.advance(0.5)
	_expect(field.count() == 40, "explosion particles live at least 0.8 s")
	field.advance(1.1)
	_expect(field.count() == 0, "explosion particles are gone after 1.5 s")

	field.emit("exhaust", Vector2.ZERO, 5)
	field.advance(0.31)
	_expect(field.count() == 0, "exhaust particles live at most 0.3 s")

	field.emit("jet_smoke", Vector2.ZERO, 1)
	var start_speed: float = field.particle_velocity(0).length()
	field.advance(0.5)
	_expect(field.particle_velocity(0).length() < start_speed or start_speed == 0.0, "smoke slows down")

	field.emit("energy", Vector2.ZERO, 10)
	field.clear()
	_expect(field.count() == 0, "clear removes everything")
	root.remove_child(field)
	field.free()


func _test_screen_fx() -> void:
	var fx: CanvasLayer = load("res://effects/screen_fx.gd").new()
	var camera := Camera2D.new()
	root.add_child(camera)
	root.add_child(fx)
	fx.camera = camera
	_expect(fx.is_in_group("screen_fx"), "screen fx joins its group")
	fx.shake(0.5)
	fx.shake(0.2)
	_expect(fx.trauma == 0.5, "a weaker shake does not reduce a stronger one")
	await process_frame
	await process_frame
	_expect(fx.trauma < 0.5 and fx.trauma > 0.0, "shake decays")
	await create_timer(0.5).timeout
	_expect(fx.trauma == 0.0 and camera.offset == Vector2.ZERO, "the camera settles")

	fx.fade_out(0.1)
	await create_timer(0.2).timeout
	_expect(is_equal_approx(fx.overlay_color().a, 1.0), "fade out ends opaque")
	fx.fade_in(0.1)
	await create_timer(0.2).timeout
	_expect(is_zero_approx(fx.overlay_color().a), "fade in ends clear")
	fx.flash()
	_expect(fx.overlay_color().a > 0.0, "flash shows at once")
	await create_timer(0.3).timeout
	_expect(is_zero_approx(fx.overlay_color().a), "flash fades away")
	root.remove_child(fx)
	fx.free()
	camera.queue_free()


func _expect(condition: bool, message: String) -> void:
	if not condition:
		_failures += 1
		printerr("FAIL: " + message)
```

- [ ] **Step 2: Write the autoload**

Create `audio/audio.gd`:

```gdscript
extends Node
## Autoload "Audio": sound effects and crossfading music. Names are file
## names in assets/sounds without the extension.

const SOUND_PATH := "res://assets/sounds/%s.ogg"
const SFX_PLAYER_COUNT := 8
const SFX_VOLUME_DB := -6.0
const MUSIC_VOLUME_DB := -12.0
const SILENT_DB := -60.0
const FADE_TIME := 1.0
## The same effect is not restarted within this many milliseconds, so a burst
## of identical events is one sound.
const RETRIGGER_GAP_MS := 50

var _sfx_players: Array[AudioStreamPlayer] = []
## The effect last played on each player, in step with _sfx_players.
var _sfx_names: Array[String] = []
var _next_sfx := 0
var _last_played := {}
var _music_players: Array[AudioStreamPlayer] = []
var _active_music := 0
var _music_name := ""
var _fade: Tween


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for i in SFX_PLAYER_COUNT:
		var player := AudioStreamPlayer.new()
		player.volume_db = SFX_VOLUME_DB
		add_child(player)
		_sfx_players.append(player)
		_sfx_names.append("")
	for i in 2:
		var player := AudioStreamPlayer.new()
		player.volume_db = SILENT_DB
		add_child(player)
		_music_players.append(player)


func play(sound: String) -> void:
	var now := Time.get_ticks_msec()
	if _last_played.has(sound) and now - int(_last_played[sound]) < RETRIGGER_GAP_MS:
		return
	var stream := _load(sound)
	if stream == null:
		return
	_last_played[sound] = now
	var index := _pick_sfx_player()
	_sfx_names[index] = sound
	_sfx_players[index].stream = stream
	_sfx_players[index].play()


## Plays the effect unless it is already sounding. For continuous actions.
func play_if_idle(sound: String) -> void:
	if not is_playing(sound):
		play(sound)


func is_playing(sound: String) -> bool:
	return playing_count(sound) > 0


func playing_count(sound: String) -> int:
	var count := 0
	for i in SFX_PLAYER_COUNT:
		if _sfx_names[i] == sound and _sfx_players[i].playing:
			count += 1
	return count


## Crossfades to a looping track. Does nothing if it is already playing.
func play_music(track: String) -> void:
	if track == _music_name:
		return
	var stream := _load(track)
	if stream == null:
		return
	if stream is AudioStreamOggVorbis:
		stream.loop = true
	_music_name = track
	var old := _music_players[_active_music]
	_active_music = 1 - _active_music
	var fresh := _music_players[_active_music]
	fresh.stream = stream
	fresh.volume_db = SILENT_DB
	fresh.play()
	if _fade != null:
		_fade.kill()
	_fade = create_tween().set_parallel()
	_fade.tween_property(fresh, "volume_db", MUSIC_VOLUME_DB, FADE_TIME)
	_fade.tween_property(old, "volume_db", SILENT_DB, FADE_TIME)
	_fade.chain().tween_callback(old.stop)


func current_music() -> String:
	return _music_name


func music_player() -> AudioStreamPlayer:
	return _music_players[_active_music]


## A player that has finished, or failing that the least recently used.
func _pick_sfx_player() -> int:
	for i in SFX_PLAYER_COUNT:
		if not _sfx_players[i].playing:
			return i
	_next_sfx = (_next_sfx + 1) % SFX_PLAYER_COUNT
	return _next_sfx


func _load(sound: String) -> AudioStream:
	var path := SOUND_PATH % sound
	if not ResourceLoader.exists(path):
		push_warning("no sound named %s" % sound)
		return null
	return load(path)
```

- [ ] **Step 3: Register it**

Append to `project.godot`, after the `[application]` section and before `[display]`:

```ini
[autoload]

Audio="*res://audio/audio.gd"

```

- [ ] **Step 4: Run the audio sections**

```bash
timeout 200 "$GODOT" --headless --path . --script res://tools/test_effects.gd 2>&1 | grep -E "FAIL:|test passed|test FAILED|SCRIPT ERROR" | head
```

Expected: no `FAIL:` lines about sounds, effects or music. Script errors about `particle_field.gd` are expected until Task 2.

- [ ] **Step 5: Commit**

```bash
git add audio tools/test_effects.gd project.godot
git commit -m "Add the Audio autoload with effects and crossfading music"
```

---

### Task 2: Particle field and screen effects

**Files:**
- Create: `effects/particle_field.gd`
- Create: `effects/screen_fx.gd`

- [ ] **Step 1: Particle field**

Create `effects/particle_field.gd`:

```gdscript
extends Node2D
## A port of the original's particle system: particles are plain records in
## an array, advanced and drawn here. Anything can add to it through the
## "particle_field" group:
##   get_tree().call_group("particle_field", "emit", "explosion", position, 40)

const BotSheet := preload("res://assets/animations/botParticles.png")
const JetSheet := preload("res://assets/animations/jetPackParticles.png")

const FRAME_TIME := 0.06
const FRAMES := 4
const SOURCE_SIZE := 16.0
const DRAW_SIZE := 32.0
## Particles start within this distance of the emit position on each axis.
const SPAWN_JITTER := 4.0


class Particle:
	var position: Vector2
	var velocity: Vector2
	var friction: float
	var life: float
	var age: float
	var sheet: Texture2D
	var row: int


## Velocity ranges are in px/s, life in seconds, friction in px/s².
var _kinds := {
	"explosion": {"sheet": BotSheet, "row": 0, "vx": [-100.0, 100.0], "vy": [-100.0, 100.0], "life": [0.8, 1.5], "friction": 0.0},
	"exhaust": {"sheet": BotSheet, "row": 0, "vx": [-10.0, 10.0], "vy": [50.0, 100.0], "life": [0.2, 0.3], "friction": 0.0},
	"jet_fire": {"sheet": JetSheet, "row": 0, "vx": [-100.0, 100.0], "vy": [50.0, 100.0], "life": [0.8, 1.5], "friction": 0.0},
	"jet_smoke": {"sheet": JetSheet, "row": 2, "vx": [-100.0, 100.0], "vy": [-100.0, 100.0], "life": [0.8, 1.5], "friction": 100.0},
	"energy": {"sheet": JetSheet, "row": 3, "vx": [-100.0, 100.0], "vy": [-100.0, 100.0], "life": [0.4, 0.6], "friction": 0.0},
}
var _particles: Array[Particle] = []


func _ready() -> void:
	add_to_group("particle_field")


## at is in this node's coordinates, which are world coordinates in the campaign.
func emit(kind: String, at: Vector2, amount: int = 1) -> void:
	var spec: Dictionary = _kinds[kind]
	for i in amount:
		var particle := Particle.new()
		particle.position = at + Vector2(randf_range(-SPAWN_JITTER, SPAWN_JITTER), randf_range(-SPAWN_JITTER, SPAWN_JITTER))
		particle.velocity = Vector2(randf_range(spec.vx[0], spec.vx[1]), randf_range(spec.vy[0], spec.vy[1]))
		particle.friction = spec.friction
		particle.life = randf_range(spec.life[0], spec.life[1])
		particle.sheet = spec.sheet
		particle.row = spec.row
		_particles.append(particle)
	queue_redraw()


func count() -> int:
	return _particles.size()


func particle_velocity(index: int) -> Vector2:
	return _particles[index].velocity


func clear() -> void:
	_particles.clear()
	queue_redraw()


func advance(delta: float) -> void:
	for i in range(_particles.size() - 1, -1, -1):
		var particle := _particles[i]
		particle.age += delta
		if particle.age >= particle.life:
			_particles.remove_at(i)
			continue
		particle.velocity.x = move_toward(particle.velocity.x, 0.0, particle.friction * delta)
		particle.velocity.y = move_toward(particle.velocity.y, 0.0, particle.friction * delta)
		particle.position += particle.velocity * delta


func _process(delta: float) -> void:
	if _particles.is_empty():
		return
	advance(delta)
	queue_redraw()


func _draw() -> void:
	var half := Vector2(DRAW_SIZE, DRAW_SIZE) / 2.0
	for particle in _particles:
		var frame := int(particle.age / FRAME_TIME) % FRAMES
		var source := Rect2(frame * SOURCE_SIZE, particle.row * SOURCE_SIZE, SOURCE_SIZE, SOURCE_SIZE)
		draw_texture_rect_region(particle.sheet, Rect2(particle.position - half, half * 2.0), source)
```

- [ ] **Step 2: Screen effects**

Create `effects/screen_fx.gd`:

```gdscript
extends CanvasLayer
## Camera shake, and an overlay across the room view for flashes and fades.
## Reached through the "screen_fx" group:
##   get_tree().call_group("screen_fx", "shake", 0.5)

const ROOM_VIEW := Vector2(960, 768)
## Camera offset in pixels at full trauma.
const MAX_OFFSET := 10.0
## Trauma lost per second.
const DECAY := 2.5
const FLASH_COLOR := Color(1, 1, 1, 0.35)
const FLASH_TIME := 0.12

## The camera to shake. Set by the owner.
var camera: Camera2D
## 0 to 1. The offset scales with its square, so small knocks stay subtle.
var trauma := 0.0

var _overlay: ColorRect
var _overlay_tween: Tween


func _ready() -> void:
	add_to_group("screen_fx")
	_overlay = ColorRect.new()
	_overlay.size = ROOM_VIEW
	_overlay.color = Color(0, 0, 0, 0)
	_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_overlay)


func shake(strength: float) -> void:
	trauma = minf(maxf(trauma, strength), 1.0)


func flash() -> void:
	_overlay.color = FLASH_COLOR
	_tween_overlay(Color(FLASH_COLOR, 0.0), FLASH_TIME)


func fade_out(time: float) -> void:
	_overlay.color = Color(0, 0, 0, 0)
	_tween_overlay(Color(0, 0, 0, 1), time)


func fade_in(time: float) -> void:
	_overlay.color = Color(0, 0, 0, 1)
	_tween_overlay(Color(0, 0, 0, 0), time)


func overlay_color() -> Color:
	return _overlay.color


func _process(delta: float) -> void:
	trauma = maxf(trauma - DECAY * delta, 0.0)
	if camera != null:
		camera.offset = Vector2(randf_range(-1.0, 1.0), randf_range(-1.0, 1.0)) * MAX_OFFSET * trauma * trauma


func _tween_overlay(target: Color, time: float) -> void:
	if _overlay_tween != null:
		_overlay_tween.kill()
	_overlay_tween = create_tween()
	_overlay_tween.tween_property(_overlay, "color", target, time)
```

- [ ] **Step 3: Run the whole effects test**

```bash
timeout 200 "$GODOT" --headless --path . --script res://tools/test_effects.gd > /tmp/out.txt 2>&1; grep -E "FAIL:|test passed|test FAILED" /tmp/out.txt; grep -c -E "SCRIPT ERROR|^ERROR" /tmp/out.txt
```

Expected: `effects test passed` and `0`.

- [ ] **Step 4: Commit**

```bash
git add effects
git commit -m "Add the particle field and screen effects"
```

---

### Task 3: Monsters, shots and the player use them

**Files:**
- Modify: `tools/test_monsters.gd`
- Modify: `entities/monsters/monster.gd`, `fly_bot.gd`, `hand_bot.gd`, `octo_boss.gd`, `powerup.gd`
- Modify: `tools/make_monster_scenes.py`; regenerate `entities/monsters/*.tscn`
- Modify: `entities/projectiles/energy_grenade.gd`
- Modify: `entities/player/player.gd`

- [ ] **Step 1: Add the failing test section**

In `tools/test_monsters.gd`:

Add a member variable after `var _player: RigidBody2D`:

```gdscript
var _field: Node2D
```

Add to the `sections` dictionary in `_run`, after the `"movers"` entry:

```gdscript
		"effects": _test_effects,
```

In `_new_arena`, add directly before the line `root.add_child(_arena)`:

```gdscript
	_field = load("res://effects/particle_field.gd").new()
	_arena.add_child(_field)
```

Add this function directly before `func _new_arena(`:

```gdscript
func _test_effects() -> void:
	_new_arena()
	var audio: Node = root.get_node("Audio")
	var bot := _spawn("jump_bot", Vector2(300, REST_Y))
	bot.hit()
	_expect(_field.count() == 40, "a dying jump bot emits 40 particles, got %d" % _field.count())
	_expect(audio.is_playing("explode"), "a dying bot plays explode")
	_field.clear()

	var ball := _spawn("ball_monster", Vector2(400, REST_Y))
	ball.hit()
	_expect(_field.count() == 0, "a dying ball monster emits no particles")
	_expect(audio.is_playing("deadAlien"), "a dying ball monster plays deadAlien")

	var flyer := _spawn("fly_bot", Vector2(600, 300))
	flyer.hit()
	_expect(audio.is_playing("hit"), "a monster that survives a hit plays hit")
	await _frames(10)
	_expect(_field.count() > 0, "a fly bot leaves exhaust")
	flyer.free()

	await _frames(30)
	_field.clear()
	Input.action_press("jetpack")
	await _frames(10)
	Input.action_release("jetpack")
	_expect(_field.count() > 0, "the jetpack leaves particles")
	_expect(audio.is_playing("jet"), "the jetpack plays jet")

	var started := [0]
	_player.death_started.connect(func() -> void: started[0] += 1)
	_player.hp = 1
	_player.hit()
	_expect(started[0] == 1, "death_started is emitted when hp reaches zero")

	_new_arena()
	_launch(EnergyGrenadeScene, Vector2(400, REST_Y - 30.0), Vector2.ZERO)
	await _frames(200)
	_expect(_field.count() >= 10, "an exploding grenade bursts into at least 10 particles, got %d" % _field.count())
```

- [ ] **Step 2: Run it to verify it fails**

```bash
timeout 200 "$GODOT" --headless --path . --script res://tools/test_monsters.gd -- --only=effects 2>&1 | grep -E "FAIL:|FAILED$" | head -3
```

Expected: `FAIL: a dying jump bot emits 40 particles, got 0` among the failures.

- [ ] **Step 3: Monster base**

In `entities/monsters/monster.gd`:

Add after the line `const PLAYER_CORNER_OFFSET := Vector2(-16, -16)`:

```gdscript
const EXHAUST_INTERVAL := 0.03
## Deaths with at least this many particles shake the screen hard.
const BIG_EXPLOSION := 100
```

Add after the `is_save_point` export:

```gdscript
## Sound played on death, or empty for none.
@export var death_sound := ""
## Explosion particles emitted on death.
@export var death_particles := 0
```

Add after the line `var _frame_elapsed := 0.0`:

```gdscript
var _exhaust_timer := 0.0
```

Replace the `hit` and `die` functions with:

```gdscript
func hit() -> void:
	hp -= 1
	if hp <= 0:
		die()
	else:
		Audio.play("hit")


func die() -> void:
	if is_queued_for_deletion():
		return
	if death_sound != "":
		Audio.play(death_sound)
	if death_particles > 0:
		emit_particles("explosion", Vector2.ZERO, death_particles)
		get_tree().call_group("screen_fx", "shake", 0.8 if death_particles >= BIG_EXPLOSION else 0.3)
	queue_free()


func emit_particles(kind: String, offset: Vector2, amount: int) -> void:
	get_tree().call_group("particle_field", "emit", kind, global_position + offset, amount)


## Call every frame to leave a trail of exhaust below the monster: up to
## max_amount particles every EXHAUST_INTERVAL, drop pixels below its centre.
func exhaust(delta: float, drop: float, max_amount: int) -> void:
	_exhaust_timer -= delta
	if _exhaust_timer < 0.0:
		_exhaust_timer = EXHAUST_INTERVAL
		emit_particles("exhaust", Vector2(randf_range(-4.0, 4.0), drop), randi_range(1, max_amount))
```

- [ ] **Step 4: Exhaust and pickup sounds**

In `entities/monsters/fly_bot.gd`, add as the first line of `_behave`:

```gdscript
	exhaust(delta, 14.0, 5)
```

In `entities/monsters/octo_boss.gd`, add as the first line of `_behave`:

```gdscript
	exhaust(delta, 32.0, 1)
```

In `entities/monsters/hand_bot.gd`, add directly after the line `apply_central_impulse(Vector2(0.0, -LIFT * delta * 60.0))`, at the same indentation:

```gdscript
		exhaust(delta, 32.0, 1)
```

In `entities/monsters/powerup.gd`, add after the `MAX_GUN_LEVEL` constant:

```gdscript
const SOUNDS := {
	"hp": "armorUpgrade",
	"fuel": "jetpackUpgrade",
	"gun": "gunUpgrade",
	"artifact": "alienArtifactAcquired",
}
```

and add directly before the line `save_requested.emit(self)`:

```gdscript
	Audio.play(SOUNDS[kind])
```

- [ ] **Step 5: Death sounds and particle counts**

In `tools/make_monster_scenes.py`, add after the `POWERUP = ...` line:

```python
ALIEN = dict(death_sound="deadAlien")
BOT = dict(death_sound="explode", death_particles=40)
BIG = dict(death_sound="explode", death_particles=100)
```

Then add these keyword arguments to the rows named, before the closing parenthesis of each call:

| Rows | Add |
| --- | --- |
| `ball_monster`, `spiky_ball_monster`, `flyer` | `**ALIEN` |
| `jump_bot`, `fly_bot`, `boss_bot_1`, `boss_bot_2`, `boss_bot_3`, `aimer_turret`, `hand_bot` | `**BOT` |
| `orb_boss`, `fallen_extranaut`, `octo_boss` | `**BIG` |
| `defense_turret_vertical`, `spiky_head_monster` | `death_sound="explode"` |
| `head_boss` | `death_sound="explode", death_particles=200` |

Regenerate:

```bash
python tools/make_monster_scenes.py
grep -l "death_sound" entities/monsters/*.tscn | wc -l
grep -c "death_particles = 200" entities/monsters/head_boss.tscn
```

Expected: `Wrote 25 monster scenes`, `16`, and `1`.

- [ ] **Step 6: Grenade burst**

Replace `entities/projectiles/energy_grenade.gd` with:

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
			_explode()


func _on_body_entered(body: Node) -> void:
	if body is StaticBody2D:
		if _fuse < 0.0:
			_fuse = FUSE
	else:
		_explode()


func _explode() -> void:
	if is_queued_for_deletion():
		return
	get_tree().call_group("particle_field", "emit", "energy", global_position, randi_range(10, 20))
	queue_free()
```

- [ ] **Step 7: Player sounds, jet particles and death signal**

In `entities/player/player.gd`:

Add after the `died` signal:

```gdscript
## Emitted at the moment hp reaches zero.
signal death_started
```

Add after the `DEAD_ROW_OFFSET` constant:

```gdscript
const JET_PUFF_INTERVAL := 0.03
## Where jet particles appear relative to the centre, facing right.
const JET_OFFSET := Vector2(-6, 14)
```

Add after the line `var _death_timer := 0.0`:

```gdscript
var _wants_thrust := false
var _thrusting := false
var _jet_puff_timer := 0.0
```

Replace the `hit` function with:

```gdscript
func hit() -> void:
	if _hit_timeout > 0.0 or is_dead():
		return
	hp -= 1
	_hit_timeout = HIT_INVULNERABLE_TIME
	Audio.play("hit")
	get_tree().call_group("screen_fx", "shake", 0.5)
	get_tree().call_group("screen_fx", "flash")
	if is_dead():
		_death_timer = DEATH_TIME
		death_started.emit()
```

In `_integrate_forces`, replace the three lines

```gdscript
	if jetpack.step(state.step, wants_thrust):
		velocity.y -= thrust_accel * state.step
	state.linear_velocity = velocity
```

with

```gdscript
	_wants_thrust = wants_thrust
	_thrusting = jetpack.step(state.step, wants_thrust)
	if _thrusting:
		velocity.y -= thrust_accel * state.step
	state.linear_velocity = velocity
```

In `_physics_process`, add directly after the line `_fire()` and at the indentation of the `if` above it (two tabs):

```gdscript
		_puff_jet(delta)
```

In `_fire`, add as the last line:

```gdscript
	Audio.play("shoot")
```

Add this function directly before `func _fire() -> void:`:

```gdscript
## Flame and the jet sound while thrusting; smoke and a sputter while the
## button is held on an empty tank.
func _puff_jet(delta: float) -> void:
	if not _wants_thrust:
		return
	_jet_puff_timer -= delta
	if _jet_puff_timer >= 0.0:
		return
	_jet_puff_timer = JET_PUFF_INTERVAL
	var at := global_position + Vector2(JET_OFFSET.x * facing, JET_OFFSET.y)
	get_tree().call_group("particle_field", "emit", "jet_fire" if _thrusting else "jet_smoke", at, randi_range(1, 5))
	Audio.play_if_idle("jet" if _thrusting else "packEmpty")
```

- [ ] **Step 8: Run the monster test**

```bash
timeout 200 "$GODOT" --headless --path . --script res://tools/test_monsters.gd > /tmp/out.txt 2>&1; grep -E "FAIL:|FAILED$|test passed|test FAILED" /tmp/out.txt; grep -c -E "SCRIPT ERROR|^ERROR" /tmp/out.txt
```

Expected: `monster test passed` and `0`.

- [ ] **Step 9: Commit**

```bash
git add entities tools
git commit -m "Monsters, shots and the player play sounds and emit particles"
```

---

### Task 4: Campaign, title and screens

**Files:**
- Modify: `tools/test_campaign.gd`
- Modify: `scenes/campaign.gd`, `scenes/campaign.tscn`
- Modify: `scenes/title.gd`, `scenes/main.gd`

- [ ] **Step 1: Add the failing checks**

In `tools/test_campaign.gd`, in `_run`, add directly after the first `await _frames(120)`:

```gdscript
	_expect(root.get_node("Audio").current_music() == "zortaSurface", "the start room plays its music")
	_expect(campaign.get_node("Particles").is_in_group("particle_field"), "the campaign hosts a particle field")
	_expect(campaign.get_node("ScreenFx").camera == campaign.get_node("Camera2D"), "screen effects drive the campaign camera")
```

In `_check_checkpoint_and_respawn`, add directly after the line `player.hit()`:

```gdscript
	await _frames(60)
	_expect(campaign.get_node("ScreenFx").overlay_color().a > 0.3, "the screen fades out during the death pause")
```

and add directly after the line that expects `"respawn restores full hp"`:

```gdscript
	_expect(campaign.get_node("Particles").count() == 0, "particles are cleared on respawn")
```

- [ ] **Step 2: Run it to verify it fails**

```bash
timeout 200 "$GODOT" --headless --path . --script res://tools/test_campaign.gd 2>&1 | grep -E "FAIL:|SCRIPT ERROR" | head -3
```

Expected: a failure or script error about the music, `Particles` or `ScreenFx`.

- [ ] **Step 3: Campaign scene**

Replace `scenes/campaign.tscn` with:

```
[gd_scene load_steps=8 format=3]

[ext_resource type="Script" path="res://scenes/campaign.gd" id="1"]
[ext_resource type="PackedScene" path="res://entities/player/player.tscn" id="2"]
[ext_resource type="Script" path="res://ui/hud.gd" id="3"]
[ext_resource type="Script" path="res://ui/map_view.gd" id="4"]
[ext_resource type="Script" path="res://ui/pause_menu.gd" id="5"]
[ext_resource type="Script" path="res://effects/particle_field.gd" id="6"]
[ext_resource type="Script" path="res://effects/screen_fx.gd" id="7"]

[node name="Campaign" type="Node2D"]
process_mode = 3
script = ExtResource("1")

[node name="World" type="Node2D" parent="."]
process_mode = 1

[node name="Player" parent="." instance=ExtResource("2")]
process_mode = 1

[node name="Shots" type="Node2D" parent="."]
process_mode = 1

[node name="Particles" type="Node2D" parent="."]
process_mode = 1
script = ExtResource("6")

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

[node name="ScreenFx" type="CanvasLayer" parent="."]
layer = 1
script = ExtResource("7")

[node name="PauseMenu" type="CanvasLayer" parent="."]
layer = 2
visible = false
script = ExtResource("5")
```

- [ ] **Step 4: Campaign script**

In `scenes/campaign.gd`:

Add after the `MAX_GUN_LEVEL` constant:

```gdscript
const RESPAWN_FADE_IN := 0.4
```

Add after the `_pause_menu` onready line:

```gdscript
@onready var _particles: Node2D = $Particles
@onready var _screen_fx: CanvasLayer = $ScreenFx
```

In `_ready`, add directly after the line `_player.died.connect(_respawn)`:

```gdscript
	_player.death_started.connect(func() -> void: _screen_fx.fade_out(_player.DEATH_TIME))
	_screen_fx.camera = _camera
```

In `_enter_room`, add directly after the line `_clear_shots()`:

```gdscript
	_particles.clear()
```

In `_respawn`, add directly after the line `_clear_shots()`:

```gdscript
	_particles.clear()
	_screen_fx.fade_in(RESPAWN_FADE_IN)
```

In `_note_room`, add as the first lines of the function:

```gdscript
	if room.music != "":
		Audio.play_music(room.music)
```

- [ ] **Step 5: Title and intro sounds**

In `scenes/title.gd`, add as the first lines of `_ready`:

```gdscript
	Audio.play_music("ruinsCore")
	Audio.play("extranautTitle")
```

In `scenes/main.gd`, in `_on_new_game`, add as the last line:

```gdscript
	Audio.play("intro")
```

- [ ] **Step 6: Run every check**

```bash
python -m unittest discover -s tools -p "test_*.py" 2>&1 | tail -1
for t in smoke_test test_jetpack test_save test_effects test_monsters test_campaign test_main; do timeout 200 "$GODOT" --headless --path . --script res://tools/$t.gd > /tmp/out.txt 2>&1; echo "$t: $(grep -E 'test passed|test FAILED' /tmp/out.txt) errors=$(grep -c -E 'SCRIPT ERROR|^ERROR' /tmp/out.txt)"; grep "FAIL:" /tmp/out.txt; done
```

Expected: `OK`, then seven `passed` lines each with `errors=0`.

- [ ] **Step 7: Look at it**

```bash
"$GODOT" --path . -- --room=1,3 --shot="$(cd .. && pwd -W)/extranaut-shots/fx.png" 2>&1 | grep -i error
```

Room (1, 3) holds the three BossBots. Open the screenshot and check that small exhaust particles trail below each bot and are drawn as whole frames.

- [ ] **Step 8: Commit**

```bash
git add scenes tools/test_campaign.gd
git commit -m "Campaign plays room music and hosts particles and screen effects"
```

---

## Done when

- Every check in Task 4 Step 6 passes with no errors.
- The title plays music; each zone plays its own track and crossfades when the track changes.
- Shots, hits, deaths, pickups and the jetpack make their sounds.
- Bots trail exhaust, the jetpack trails flame or smoke, bots and bosses explode into particles, grenades burst.
- The screen shakes on hits and explosions, flashes when the player is hit, and fades out and back in around a death.
- The author has listened to it: relative volume of music and effects cannot be judged by tests.
