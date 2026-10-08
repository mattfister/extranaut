extends Node2D
## A looping cover image to record as a GIF: the animated logo, the Extranaut
## jetpacking across beneath it and two ball monsters rolling on the terrain.
## Run this scene on its own (F6); it resizes the window to SIZE.
##
## The layout lives in cover.tscn. Everything on screen repeats every
## LOOP_TIME, and for the first FLIGHT_START seconds of each loop the Extranaut
## and his jet particles are gone, so a recording cut to LOOP_TIME from
## anywhere in that stretch loops cleanly.

const SIZE := Vector2i(630, 500)
const LOGO_FRAME_TIME := 0.06
## A whole number of logo cycles, and long enough for the last jet particles
## to burn out before the loop restarts:
## FLIGHT_START + FLIGHT_TIME + 1.5 * PARTICLE_LIFE_SCALE <= LOOP_TIME.
const LOOP_TIME := 3.6
const FLIGHT_START := 1.0
const FLIGHT_TIME := 1.9
## How far off each side of the screen the flight starts and ends.
const FLIGHT_MARGIN := 24.0
const BOB_HEIGHT := 24.0
## Bobs over the whole flight.
const BOBS := 1.75
const WALK_FRAME_TIME := 0.06
const JET_PUFF_INTERVAL := 0.03
## Where jet particles appear relative to the Extranaut's centre, as in player.gd.
const JET_OFFSET := Vector2(-6, 14)
const PARTICLE_LIFE_SCALE := 0.45
const BALL_RADIUS := 16.0
## As monster.gd. LOOP_TIME is a whole number of these too.
const BALL_FRAME_TIME := 0.09
## For each ball: how far it rolls either side of where cover.tscn puts it,
## and how far through the loop (0 to 1) it is in that roll at the start.
const BALL_ROLLS := [
	{"reach": 80.0, "phase": 0.0},
	{"reach": 80.0, "phase": 0.35},
]
## Background pixels darker than this are sky.
const SKY_BRIGHTNESS := 0.05

var _time := 0.0
var _jet_puff_timer := 0.0

@onready var _logo: Sprite2D = $Logo
@onready var _extranaut: Sprite2D = $Extranaut
@onready var _particles: Node2D = $Particles
## The height the flight bobs around.
@onready var _flight_y := _extranaut.position.y
@onready var _balls: Array[Sprite2D] = [$Ball1, $Ball2]
## The x each ball rolls around.
@onready var _ball_homes: Array[float] = [$Ball1.position.x, $Ball2.position.x]

## The height of the top of the background's terrain at each x on screen,
## starting BALL_RADIUS off the left edge.
var _ground := PackedFloat32Array()


func _ready() -> void:
	var window := get_window()
	window.content_scale_size = SIZE
	# Before the size: fixing the frame changes the size of the window.
	window.unresizable = true
	window.size = SIZE
	_read_ground()


func _process(delta: float) -> void:
	_time = fmod(_time + delta, LOOP_TIME)
	_logo.frame = int(_time / LOGO_FRAME_TIME) % _logo.hframes
	_roll_balls()
	var progress := (_time - FLIGHT_START) / FLIGHT_TIME
	_extranaut.visible = progress >= 0.0 and progress <= 1.0
	if not _extranaut.visible:
		return
	var bob := sin(progress * BOBS * TAU)
	_extranaut.position = Vector2(
		lerpf(-FLIGHT_MARGIN, SIZE.x + FLIGHT_MARGIN, progress),
		_flight_y + bob * BOB_HEIGHT)
	_extranaut.frame_coords.x = int(_time / WALK_FRAME_TIME) % _extranaut.hframes
	# The jetpack fires through the low half of each bob, pushing back up.
	_jet_puff_timer -= delta
	if bob > 0.0 and _jet_puff_timer < 0.0:
		_jet_puff_timer = JET_PUFF_INTERVAL
		_particles.emit("jet_fire", _extranaut.position + JET_OFFSET, randi_range(1, 5), PARTICLE_LIFE_SCALE)


func _read_ground() -> void:
	var background: Sprite2D = $Background
	var image := background.texture.get_image()
	for x in range(-int(BALL_RADIUS), SIZE.x + int(BALL_RADIUS) + 1):
		var column := clampi(int((x - background.position.x) / background.scale.x), 0, image.get_width() - 1)
		var top := 0
		while top < image.get_height() and image.get_pixel(column, top).get_luminance() < SKY_BRIGHTNESS:
			top += 1
		_ground.append(background.position.y + top * background.scale.y)


## Each ball rolls out and back once a loop, resting on the terrain and
## turning as far as it has travelled.
func _roll_balls() -> void:
	for i in _balls.size():
		var roll: Dictionary = BALL_ROLLS[i]
		var offset: float = roll.reach * sin((_time / LOOP_TIME + roll.phase) * TAU)
		var x := _ball_homes[i] + offset
		_balls[i].position = Vector2(x, _resting_y(x))
		_balls[i].rotation = offset / BALL_RADIUS
		_balls[i].frame_coords.x = (int(_time / BALL_FRAME_TIME) + i) % _balls[i].hframes


## The height of the centre of a ball at x that is sitting on the terrain.
func _resting_y(x: float) -> float:
	var y := INF
	for dx in range(-int(BALL_RADIUS), int(BALL_RADIUS) + 1):
		var column := clampi(roundi(x) + dx + int(BALL_RADIUS), 0, _ground.size() - 1)
		y = minf(y, _ground[column] - sqrt(BALL_RADIUS * BALL_RADIUS - dx * dx))
	return y
