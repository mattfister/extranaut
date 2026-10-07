extends "res://entities/monsters/monster.gd"
## Lobs a grenade upward every 3 s.

var _fire_timer := randf_range(0.0, 3.0)


func _behave(delta: float, _player: Node2D) -> void:
	_fire_timer -= delta
	if _fire_timer < 0.0:
		_fire_timer = 3.0
		var impulse := Vector2(randf_range(-10000.0, 10000.0), randf_range(-15000.0, -10000.0))
		fire(EnergyGrenadeScene, Vector2(8, -32), impulse)
