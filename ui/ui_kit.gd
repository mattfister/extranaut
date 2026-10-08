extends RefCounted
## Shared look for menus and the HUD built in code: the original's font, and
## its black buttons with a one-pixel border. The look itself is defined once,
## in ui_theme.tres, which scenes such as the title use directly.

const THEME := preload("res://ui/ui_theme.tres")
const FONT := preload("res://assets/fonts/KARNIVOR.ttf")
const FONT_SIZE := 13


static func make_label(text: String) -> Label:
	var label := Label.new()
	label.text = text
	label.theme = THEME
	return label


static func make_button(text: String, button_size: Vector2) -> Button:
	var button := Button.new()
	button.text = text
	button.custom_minimum_size = button_size
	button.size = button_size
	button.theme = THEME
	return button
