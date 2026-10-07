extends Control
## A full-screen image, dismissed by any key, click or gamepad button.
## Set texture before adding it to the tree.

signal dismissed

var texture: Texture2D

var _done := false


func _ready() -> void:
	var image := TextureRect.new()
	image.texture = texture
	image.scale = Vector2(2, 2)
	image.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(image)


func _unhandled_input(event: InputEvent) -> void:
	if _done or event.is_echo() or not event.is_pressed():
		return
	if event is InputEventKey or event is InputEventMouseButton or event is InputEventJoypadButton:
		_done = true
		dismissed.emit()
