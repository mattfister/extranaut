extends "res://entities/projectiles/projectile.gd"
## A ballistic enemy shot. Explodes at once on a body, or FUSE seconds after
## first touching a wall. Hurts the player on contact either way.

const FUSE := 3.0

## Negative until the grenade has touched a wall.
var _fuse := -1.0


func _ready() -> void:
	super()
	add_to_group("enemy_shots")


func _physics_process(delta: float) -> void:
	super(delta)
	if _fuse >= 0.0:
		_fuse -= delta
		if _fuse < 0.0:
			_explode()


func _on_body_entered(body: Node) -> void:
	if body is StaticBody2D:
		if _fuse < 0.0:
			_fuse = FUSE
	else:
		_explode()


func _explode() -> void:
	if is_queued_for_deletion():
		return
	get_tree().call_group("particle_field", "emit", "energy", global_position, randi_range(10, 20))
	queue_free()
