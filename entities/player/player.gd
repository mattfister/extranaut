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
