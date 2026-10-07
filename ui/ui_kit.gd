extends RefCounted
## Shared look for menus and the HUD: the original's font, and its black
## buttons with a one-pixel border.

const FONT := preload("res://assets/fonts/KARNIVOR.ttf")
const FONT_SIZE := 13
const BORDER := Color.WHITE
const BORDER_FOCUS := Color(1.0, 0.85, 0.2)


static func make_label(text: String) -> Label:
	var label := Label.new()
	label.text = text
	label.add_theme_font_override("font", FONT)
	label.add_theme_font_size_override("font_size", FONT_SIZE)
	return label


static func make_button(text: String, button_size: Vector2) -> Button:
	var button := Button.new()
	button.text = text
	button.custom_minimum_size = button_size
	button.size = button_size
	button.add_theme_font_override("font", FONT)
	button.add_theme_font_size_override("font_size", FONT_SIZE)
	button.add_theme_stylebox_override("normal", _box(Color.BLACK, BORDER))
	button.add_theme_stylebox_override("hover", _box(Color.BLACK, BORDER_FOCUS))
	button.add_theme_stylebox_override("focus", _box(Color.BLACK, BORDER_FOCUS))
	button.add_theme_stylebox_override("pressed", _box(Color(0.25, 0.25, 0.25), BORDER_FOCUS))
	return button


static func _box(fill: Color, border: Color) -> StyleBoxFlat:
	var box := StyleBoxFlat.new()
	box.bg_color = fill
	box.border_color = border
	box.set_border_width_all(1)
	return box
