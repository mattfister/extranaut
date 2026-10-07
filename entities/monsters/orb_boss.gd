extends "res://entities/monsters/monster.gd"
## Alternates every 5 to 10 s between chasing the player and flying upward
## while throwing grenades. Used by OrbBoss and FallenExtranaut.

enum Mode { CHASING, FLYING }

const DRIFTS := [-1000.0, 0.0, 1000.0]
const AIMED_MUZZLE := 36.0

@export var grenade_offset := Vector2(32, -32)
## Throw grenades upward. When false they are thrown flat.
@export var lob_grenades := true
## Also fire an aimed shot every 2 s while chasing.
@export var fires_when_chasing := false
## Show sprite row 0 when chasing and row 1 when flying.
@export var row_per_mode := true

var _mode: Mode = [Mode.CHASING, Mode.FLYING].pick_random()
var _mode_timer := randf_range(5.0, 10.0)
var _force_timer := randf_range(0.0, 5.0)
var _grenade_timer := 1.0
var _fire_timer := 2.0


func _behave(delta: float, player: Node2D) -> void:
	_mode_timer -= delta
	if _mode_timer <= 0.0:
		_mode_timer = randf_range(5.0, 10.0)
		_mode = Mode.FLYING if _mode == Mode.CHASING else Mode.CHASING
	if row_per_mode:
		sprite.frame_coords.y = 0 if _mode == Mode.CHASING else 1
	_force_timer -= delta
	if _mode == Mode.FLYING:
		_fly(delta)
	elif player != null:
		_chase(delta, player)


func _fly(delta: float) -> void:
	if _force_timer < 0.0:
		_force_timer = randf_range(0.0, 0.1)
		apply_central_impulse(Vector2(DRIFTS.pick_random(), -15000.0))
	_grenade_timer -= delta
	if _grenade_timer <= 0.0:
		_grenade_timer = 1.0
		for i in 3:
			var up := randf_range(-15000.0, -10000.0) if lob_grenades else 0.0
			fire(EnergyGrenadeScene, grenade_offset, Vector2(randf_range(-10000.0, 10000.0), up))


func _chase(delta: float, player: Node2D) -> void:
	var corner := player_corner(player)
	if _force_timer < 0.0:
		_force_timer = 0.06
		var sideways := 5000.0 if corner.x > global_position.x else -5000.0
		var vertical := 5000.0 if corner.y > global_position.y else -15000.0
		apply_central_impulse(Vector2(sideways, vertical))
	if fires_when_chasing:
		_fire_timer -= delta
		if _fire_timer <= 0.0:
			_fire_timer = 2.0
			var impulse := aim_at(player)
			var offset := Vector2(
				AIMED_MUZZLE if impulse.x > 0.0 else -AIMED_MUZZLE,
				AIMED_MUZZLE if impulse.y > 0.0 else -AIMED_MUZZLE
			)
			fire(EnemyEnergyBallScene, offset, impulse)
