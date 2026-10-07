extends "res://entities/monsters/monster.gd"
## Blocks the way until the player holds all four alien artifacts.

const ARTIFACTS_NEEDED := 4


func _behave(_delta: float, player: Node2D) -> void:
	if player != null and player.artifacts >= ARTIFACTS_NEEDED:
		die()
