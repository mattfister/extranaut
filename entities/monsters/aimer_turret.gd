extends "res://entities/monsters/monster.gd"
## Fires an aimed shot at the player every 2 s.

## Muzzle offset per axis, by the sign of the aim. The original's values are
## lopsided: a shot aimed up and left spawns inside the turret and dies.
const MUZZLE_POSITIVE := 36.0
const MUZZLE_NEGATIVE := -8.0

var _fire_timer := 2.0


func _behave(delta: float, player: Node2D) -> void:
	_fire_timer -= delta
	if _fire_timer < 0.0 and player != null:
		_fire_timer = 2.0
		var impulse := aim_at(player)
		var offset := Vector2(
			MUZZLE_POSITIVE if impulse.x > 0.0 else MUZZLE_NEGATIVE,
			MUZZLE_POSITIVE if impulse.y > 0.0 else MUZZLE_NEGATIVE
		)
		fire(EnemyEnergyBallScene, offset, impulse)
