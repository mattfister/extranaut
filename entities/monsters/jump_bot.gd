extends "res://entities/monsters/monster.gd"
## Hops once a second, toward the player when it is within 150 px on both axes.

const NEAR := 150.0

var _jump_timer := 1.0
## While positive the bot shows its jumping frame.
var _airborne_timer := 0.5


func _behave(delta: float, player: Node2D) -> void:
	_airborne_timer -= delta
	_jump_timer -= delta
	if _jump_timer < 0.0:
		_jump_timer = 1.0
		_airborne_timer = 0.5
		var push := 0.0
		if player != null:
			var to_player := player_corner(player) - global_position
			if absf(to_player.x) < NEAR and absf(to_player.y) < NEAR:
				push = 5000.0 if to_player.x > 0.0 else -5000.0
		apply_central_impulse(Vector2(push, -8000.0))


func _animate(_delta: float) -> void:
	sprite.frame_coords.x = 1 if _airborne_timer > 0.0 else 0
