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
	exhaust(delta, 14.0, 5)
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
