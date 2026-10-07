extends "res://entities/projectiles/projectile.gd"
## The player's shot. Flies straight and also dies when it slows below MIN_SPEED.

const MIN_SPEED := 400.0


func _ready() -> void:
	super()
	add_to_group("player_shots")


func _physics_process(delta: float) -> void:
	super(delta)
	if linear_velocity.length() < MIN_SPEED:
		queue_free()
