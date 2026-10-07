extends "res://entities/monsters/monster.gd"
## Floats upward and is knocked down and sideways at random intervals.

const KICKS := [-5000.0, 0.0, 5000.0]

var _kick_timer := randf_range(0.0, 5.0)


func _behave(delta: float, _player: Node2D) -> void:
	_kick_timer -= delta
	if _kick_timer < 0.0:
		_kick_timer = randf_range(0.0, 3.0)
		apply_central_impulse(Vector2(KICKS.pick_random(), randf_range(5000.0, 10000.0)))
