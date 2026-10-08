extends "res://entities/monsters/monster.gd"
## A pickup applied when the player touches it. Used by HpPowerup, FuelPowerup,
## GunPowerup and AlienArtifact, which differ in kind.

const FUEL_BONUS := 500.0
const MAX_GUN_LEVEL := 4
const SOUNDS := {
	"hp": "armorUpgrade",
	"fuel": "jetpackUpgrade",
	"gun": "gunUpgrade",
	"artifact": "alienArtifactAcquired",
}

## One of "hp", "fuel", "gun", "artifact".
@export var kind := "hp"

var _applied := false


func _integrate_forces(state: PhysicsDirectBodyState2D) -> void:
	state.linear_velocity = Vector2.ZERO


func apply_powerup(player: Node2D) -> void:
	if _applied:
		return
	_applied = true
	match kind:
		"hp":
			player.max_hp += 1
			player.hp = player.max_hp
		"fuel":
			player.jetpack.max_fuel += FUEL_BONUS
		"gun":
			player.gun_level = mini(player.gun_level + 1, MAX_GUN_LEVEL)
		"artifact":
			player.artifacts += 1
	get_tree().call_group("audio", "play", SOUNDS[kind])
	save_requested.emit(self)
	die()
