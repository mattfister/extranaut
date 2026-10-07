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
