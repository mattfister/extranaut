extends "res://entities/projectiles/projectile.gd"
## A straight-flying enemy shot. Hurts the player on contact.


func _ready() -> void:
	super()
	add_to_group("enemy_shots")
