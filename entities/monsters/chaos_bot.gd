extends "res://entities/monsters/monster.gd"
## Chaosnaut's enemy. Drifts left at a fixed speed with random vertical
## kicks. The arena makes it angry, and faster, when it reaches the left edge.

const SPEED := 100.0
const ANGRY_SPEED := 300.0
const KICK := 3000.0
const ANGRY_PUSH := 1000.0
const CALM_ROW := 1
const ANGRY_ROW := 2

var angry := false

var _kick_timer := randf_range(0.0, 0.1)


func _integrate_forces(state: PhysicsDirectBodyState2D) -> void:
	var velocity := state.linear_velocity
	velocity.x = -ANGRY_SPEED if angry else -SPEED
	state.linear_velocity = velocity


func _behave(delta: float, _player: Node2D) -> void:
	exhaust(delta, 14.0, 5)
	sprite.frame_coords.y = ANGRY_ROW if angry else CALM_ROW
	_kick_timer -= delta
	if _kick_timer < 0.0:
		_kick_timer = randf_range(0.5, 1.0)
		apply_central_impulse(Vector2(ANGRY_PUSH if angry else 0.0, randf_range(-KICK, KICK)))
