extends "res://entities/monsters/monster.gd"
## Blocks the way until the room is cleared. The count includes this door and
## every other monster-class entity in the room, as in the original.

## MonsterDoor opens at 1 (only the door left); MonsterDoor2 opens at 2.
@export var open_when_count := 1


func _behave(_delta: float, _player: Node2D) -> void:
	if monsters_in_room() == open_when_count:
		die()
