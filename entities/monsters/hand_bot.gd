extends "res://entities/monsters/monster.gd"
## A big bot that thrusts upward while the player is above it and within
## 100 px horizontally.

const NEAR_X := 100.0
## Upward impulse per frame at 60 fps, as in the original.
const LIFT := 5000.0


func _behave(delta: float, player: Node2D) -> void:
	if player == null:
		return
	var corner := player_corner(player)
	if absf(global_position.x - corner.x) < NEAR_X and corner.y < global_position.y:
		apply_central_impulse(Vector2(0.0, -LIFT * delta * 60.0))
