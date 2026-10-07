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
			queue_free()


func _on_body_entered(body: Node) -> void:
	if body is StaticBody2D:
		if _fuse < 0.0:
			_fuse = FUSE
	else:
		queue_free()
