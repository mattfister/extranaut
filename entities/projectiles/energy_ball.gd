extends "res://entities/projectiles/projectile.gd"
## The player's shot. Flies straight and also dies when it slows below MIN_SPEED.

const MIN_SPEED := 400.0
## A hit slows the shot a frame before either body is told about the contact,
## so the shot must stay slow this long before it gives up. Dying sooner would
## remove it before the monster it hit hears about it.
const SLOW_FRAMES_TO_DIE := 3

var _slow_frames := 0


func _ready() -> void:
	super()
	add_to_group("player_shots")


func _physics_process(delta: float) -> void:
	super(delta)
	if linear_velocity.length() < MIN_SPEED:
		_slow_frames += 1
		if _slow_frames >= SLOW_FRAMES_TO_DIE:
			queue_free()
	else:
		_slow_frames = 0
