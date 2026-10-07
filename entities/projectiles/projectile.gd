extends RigidBody2D
## Base for all shots: animates the sprite, dies on touching anything, and
## frees itself once outside the room it was fired in.

const FRAME_TIME := 0.06
const BOUNDS_MARGIN := 32.0

## The room's rectangle in world coordinates. Set by whoever spawns the shot.
## Left empty, the shot is never culled.
var bounds := Rect2()

var _frame_elapsed := 0.0

@onready var _sprite: Sprite2D = $Sprite2D


func _ready() -> void:
	body_entered.connect(_on_body_entered)


func _physics_process(delta: float) -> void:
	_frame_elapsed += delta
	if _frame_elapsed >= FRAME_TIME:
		_frame_elapsed -= FRAME_TIME
		_sprite.frame_coords.x = (_sprite.frame_coords.x + 1) % _sprite.hframes
	if bounds.has_area() and not bounds.grow(BOUNDS_MARGIN).has_point(global_position):
		queue_free()


func _on_body_entered(_body: Node) -> void:
	queue_free()
