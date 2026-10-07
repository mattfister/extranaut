class_name AnimatedTile
extends Sprite2D
## Cycles through the frames of one row of an animation sheet.

const FRAME_TIME := 0.09

var _elapsed := 0.0


func _process(delta: float) -> void:
	_elapsed += delta
	if _elapsed >= FRAME_TIME:
		_elapsed -= FRAME_TIME
		frame_coords.x = (frame_coords.x + 1) % hframes
