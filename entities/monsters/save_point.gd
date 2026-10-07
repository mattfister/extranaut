extends "res://entities/monsters/monster.gd"
## Shoot it to save. It activates once per visit to the room.

var activated := false


func _integrate_forces(state: PhysicsDirectBodyState2D) -> void:
	state.linear_velocity = Vector2.ZERO


func hit() -> void:
	if not activated:
		activated = true
		sprite.frame_coords.y = 1
		save_requested.emit(self)
