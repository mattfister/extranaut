extends CanvasLayer
## Camera shake, and an overlay across the room view for flashes and fades.
## Reached through the "screen_fx" group:
##   get_tree().call_group("screen_fx", "shake", 0.5)

const ROOM_VIEW := Vector2(960, 768)
## Camera offset in pixels at full trauma.
const MAX_OFFSET := 10.0
## Trauma lost per second.
const DECAY := 2.5
const FLASH_COLOR := Color(1, 1, 1, 0.35)
const FLASH_TIME := 0.12

## The camera to shake. Set by the owner.
var camera: Camera2D
## 0 to 1. The offset scales with its square, so small knocks stay subtle.
var trauma := 0.0

var _overlay: ColorRect
var _overlay_tween: Tween


func _ready() -> void:
	add_to_group("screen_fx")
	_overlay = ColorRect.new()
	_overlay.size = ROOM_VIEW
	_overlay.color = Color(0, 0, 0, 0)
	_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_overlay)


func shake(strength: float) -> void:
	trauma = minf(maxf(trauma, strength), 1.0)


func flash() -> void:
	_overlay.color = FLASH_COLOR
	_tween_overlay(Color(FLASH_COLOR, 0.0), FLASH_TIME)


func fade_out(time: float) -> void:
	_overlay.color = Color(0, 0, 0, 0)
	_tween_overlay(Color(0, 0, 0, 1), time)


func fade_in(time: float) -> void:
	_overlay.color = Color(0, 0, 0, 1)
	_tween_overlay(Color(0, 0, 0, 0), time)


func overlay_color() -> Color:
	return _overlay.color


func _process(delta: float) -> void:
	trauma = maxf(trauma - DECAY * delta, 0.0)
	if camera != null:
		camera.offset = Vector2(randf_range(-1.0, 1.0), randf_range(-1.0, 1.0)) * MAX_OFFSET * trauma * trauma


func _tween_overlay(target: Color, time: float) -> void:
	if _overlay_tween != null:
		_overlay_tween.kill()
	_overlay_tween = create_tween()
	_overlay_tween.tween_property(_overlay, "color", target, time)
