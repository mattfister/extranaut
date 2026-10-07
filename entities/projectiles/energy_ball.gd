extends RigidBody2D
## The player's shot. Flies straight, and dies when it touches anything,
## slows below MIN_SPEED, or leaves the room it was fired in.

const MIN_SPEED := 400.0
const FRAME_TIME := 0.06
const BOUNDS_MARGIN := 32.0

## The room's rectangle in world coordinates. Set by whoever spawns the shot.
var bounds := Rect2()

var _frame_elapsed := 0.0

@onready var _sprite: Sprite2D = $Sprite2D


func _ready() -> void:
	body_entered.connect(func(_body: Node) -> void: queue_free())


func _physics_process(delta: float) -> void:
	_frame_elapsed += delta
	if _frame_elapsed >= FRAME_TIME:
		_frame_elapsed -= FRAME_TIME
		_sprite.frame_coords.x = (_sprite.frame_coords.x + 1) % _sprite.hframes
	if linear_velocity.length() < MIN_SPEED:
		queue_free()
	elif bounds.has_area() and not bounds.grow(BOUNDS_MARGIN).has_point(global_position):
		queue_free()
