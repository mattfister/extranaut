extends RefCounted
## Registers the game's input actions. Call setup() once at startup.
## Ctrl and Esc are deliberately unbound: browsers intercept them.

const ACTIONS := {
	"move_left": {
		"keys": [KEY_LEFT, KEY_A],
		"buttons": [JOY_BUTTON_DPAD_LEFT],
		"axis": [JOY_AXIS_LEFT_X, -1.0],
	},
	"move_right": {
		"keys": [KEY_RIGHT, KEY_D],
		"buttons": [JOY_BUTTON_DPAD_RIGHT],
		"axis": [JOY_AXIS_LEFT_X, 1.0],
	},
	"jetpack": {
		"keys": [KEY_UP, KEY_W],
		"buttons": [JOY_BUTTON_DPAD_UP, JOY_BUTTON_A],
		"axis": [JOY_AXIS_LEFT_Y, -1.0],
	},
	"fire": {
		"keys": [KEY_Z, KEY_X, KEY_SPACE],
		"buttons": [JOY_BUTTON_X],
	},
	"pause": {
		"keys": [KEY_P, KEY_ENTER],
		"buttons": [JOY_BUTTON_START],
	},
}


static func setup() -> void:
	for action in ACTIONS:
		if InputMap.has_action(action):
			continue
		InputMap.add_action(action, 0.5)
		var binding: Dictionary = ACTIONS[action]
		for key in binding.get("keys", []):
			var event := InputEventKey.new()
			event.physical_keycode = key
			InputMap.action_add_event(action, event)
		for button in binding.get("buttons", []):
			var event := InputEventJoypadButton.new()
			event.button_index = button
			InputMap.action_add_event(action, event)
		if binding.has("axis"):
			var event := InputEventJoypadMotion.new()
			event.axis = binding.axis[0]
			event.axis_value = binding.axis[1]
			InputMap.action_add_event(action, event)
