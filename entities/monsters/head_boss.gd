extends "res://entities/monsters/monster.gd"
## A stationary head that fires aimed shots faster as it is hurt, and is
## shielded for 2 s after each hit. Its frame follows the player's height.

const SHIELD_TIME := 2.0
## The original aimed 32 px down and right of the player's sprite corner.
const AIM_LEAD := Vector2(32, 32)
## Muzzle offset when firing right and when firing left. The right-hand one
## overlaps the boss, so those shots die at once, as in the original.
const MUZZLE_RIGHT := Vector2(34, -16)
const MUZZLE_LEFT := Vector2(-50, -16)

var _shoot_timer := 1.0
var _shield := 0.0


func _behave(delta: float, player: Node2D) -> void:
	_shield -= delta
	sprite.frame_coords.y = 1 if _shield > 0.0 else 0
	if player == null:
		return
	_shoot_timer -= delta
	if _shoot_timer <= 0.0:
		_shoot_timer = 1.0 - (max_hp - hp) * 0.05
		var impulse := aim_at(player, AIM_LEAD)
		fire(EnemyEnergyBallScene, MUZZLE_RIGHT if impulse.x > 0.0 else MUZZLE_LEFT, impulse)
	var height := player_corner(player).y - global_position.y
	if height < -500.0:
		sprite.frame_coords.x = 2
	elif height < -100.0:
		sprite.frame_coords.x = 1
	else:
		sprite.frame_coords.x = 0


func hit() -> void:
	if _shield <= 0.0:
		_shield = SHIELD_TIME
		super()
