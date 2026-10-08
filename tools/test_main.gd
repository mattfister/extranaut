extends SceneTree
## Walks the screen flow: title, new game, intro, campaign, quit, continue,
## delete, ending.
## Run: godot --headless --path . --script res://tools/test_main.gd

const Progress := preload("res://save/progress.gd")
const SaveGame := preload("res://save/save_game.gd")
const TitleScript := preload("res://scenes/title.gd")
const ImageScreenScript := preload("res://scenes/image_screen.gd")
const CampaignScript := preload("res://scenes/campaign.gd")
const ChaosnautScript := preload("res://scenes/chaosnaut.gd")

var _failures := 0
var _main: Node


func _initialize() -> void:
	_run()


func _run() -> void:
	SaveGame.directory = "user://test_saves/"
	DirAccess.make_dir_recursive_absolute(SaveGame.directory)
	for slot in SaveGame.SLOTS:
		SaveGame.delete(slot)
	await process_frame
	_main = load("res://scenes/main.tscn").instantiate()
	root.add_child(_main)
	await _settle()

	_expect(_is(TitleScript), "the game opens on the title")
	_expect(_button("Slot1New") != null, "an empty slot offers New Game")
	_expect(_button("Slot1Continue") == null, "an empty slot does not offer Continue")

	# New game: writes the slot, shows the intro, then the campaign.
	_button("Slot1New").pressed.emit()
	await _settle()
	_expect(_is(ImageScreenScript), "New Game shows the intro")
	_expect(SaveGame.exists(1), "New Game writes the slot at once")
	_press_key(KEY_SPACE)
	await _settle()
	_expect(_is(CampaignScript), "dismissing the intro starts the campaign")
	if _is(CampaignScript):
		_expect(_main.screen.slot == 1, "the campaign uses the chosen slot")
		_expect(_main.screen.grid == Vector2i(4, 2), "a new game starts in room 4,2")
		_main.screen.quit_to_title.emit()
	await _settle()

	# Back on the title the slot is in use.
	_expect(_is(TitleScript), "quitting returns to the title")
	_expect(_button("Slot1Continue") != null and _button("Slot1Delete") != null, "a used slot offers Continue and Delete")
	_expect(_button("Slot1New") == null, "a used slot does not offer New Game")

	# Delete.
	_button("Slot1Delete").pressed.emit()
	await _settle()
	_expect(not SaveGame.exists(1), "Delete removes the slot file")
	_expect(_button("Slot1New") != null and _button("Slot1Delete") == null, "a deleted slot offers New Game again")

	# Continue goes straight to the campaign at the saved checkpoint.
	var progress := Progress.new()
	progress.checkpoint = Vector2i(5, 2)
	progress.max_hp = 7
	SaveGame.write(2, progress)
	_main.show_title()
	await _settle()
	_button("Slot2Continue").pressed.emit()
	await _settle()
	_expect(_is(CampaignScript), "Continue starts the campaign without the intro")
	if _is(CampaignScript):
		_expect(_main.screen.grid == Vector2i(5, 2), "Continue starts at the checkpoint")
		_expect(_main.screen.get_node("Player").max_hp == 7, "Continue restores stats")
		# Winning shows the ending, then the title.
		_main.screen.won.emit()
	await _settle()
	_expect(_is(ImageScreenScript), "winning shows the ending")
	_press_key(KEY_SPACE)
	await _settle()
	_expect(_is(TitleScript), "dismissing the ending returns to the title")
	_expect(not paused, "the tree is not left paused")

	# Chaosnaut from the title and back.
	_expect(_button("Chaosnaut") != null, "the title offers Chaosnaut")
	if _button("Chaosnaut") != null:
		_button("Chaosnaut").pressed.emit()
	await _settle()
	_expect(_is(ChaosnautScript), "the Chaosnaut button starts the mode")
	if _is(ChaosnautScript):
		_main.screen.finished.emit()
	await _settle()
	_expect(_is(TitleScript), "leaving Chaosnaut returns to the title")

	for slot in SaveGame.SLOTS:
		SaveGame.delete(slot)
	print("main test passed" if _failures == 0 else "main test FAILED: %d failures" % _failures)
	quit(1 if _failures > 0 else 0)


func _is(script: Script) -> bool:
	return _main.screen != null and _main.screen.get_script() == script


func _button(node_name: String) -> Button:
	return _main.screen.find_child(node_name, true, false) as Button


func _press_key(keycode: Key) -> void:
	var event := InputEventKey.new()
	event.keycode = keycode
	event.physical_keycode = keycode
	event.pressed = true
	Input.parse_input_event(event)


## Waits for input to be delivered and acted on, ending between frames, where
## real button presses arrive. Input is flushed once per rendered frame, so
## counting physics frames alone is not enough.
func _settle() -> void:
	await process_frame
	await process_frame
	await physics_frame
	await process_frame


func _expect(condition: bool, message: String) -> void:
	if not condition:
		_failures += 1
		printerr("FAIL: " + message)
