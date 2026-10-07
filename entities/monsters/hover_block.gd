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
