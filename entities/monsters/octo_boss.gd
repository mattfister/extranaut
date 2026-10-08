extends "res://entities/monsters/monster.gd"
## Hovers, fires an aimed shot every second, drops three grenades every 5 s,
## and lurches every 2 s, harder the more it has been hurt.

const AIMED_MUZZLE := 34.0

var _shoot_timer := 1.0
var _grenade_timer := 5.0
var _lurch_timer := 2.0


func _behave(delta: float, player: Node2D) -> void:
	exhaust(delta, 32.0, 1)
	_shoot_timer -= delta
	if _shoot_timer <= 0.0 and player != null:
		_shoot_timer = 1.0
		var impulse := aim_at(player)
		var offset := Vector2(
			AIMED_MUZZLE if impulse.x > 0.0 else -AIMED_MUZZLE,
			AIMED_MUZZLE if impulse.y > 0.0 else -AIMED_MUZZLE
		)
		fire(EnemyEnergyBallScene, offset, impulse)

	_grenade_timer -= delta
	if _grenade_timer <= 0.0:
		_grenade_timer = 5.0
		for i in 3:
			fire(EnergyGrenadeScene, Vector2(0, 48), Vector2(randf_range(-10000.0, 10000.0), 0.0))

	_lurch_timer -= delta
	if _lurch_timer <= 0.0:
		_lurch_timer = 2.0
		var extra := 2000.0 * (max_hp - hp)
		var sideways: float = [30000.0 + extra, -30000.0 - extra].pick_random()
		var vertical: float = [1000.0 + extra, -1000.0 - extra].pick_random()
		apply_central_impulse(Vector2(sideways, vertical))
