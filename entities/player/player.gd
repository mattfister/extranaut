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
