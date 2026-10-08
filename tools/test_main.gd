extends SceneTree
## Walks the screen flow: title, new game, intro, campaign, quit, continue,
## delete, ending.
## Run: godot --headless --path . --script res://tools/test_main.gd

const Planets := preload("res://world/planets.gd")
const Settings := preload("res://save/settings.gd")
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
	_clear_saves()
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
	_expect(SaveGame.exists("zorta", 1), "New Game writes the slot at once")
	_press_key(KEY_SPACE)
	await _settle()
	_expect(_is(CampaignScript), "dismissing the intro starts the campaign")
	if _is(CampaignScript):
		_expect(_main.screen.slot == 1, "the campaign uses the chosen slot")
		_expect(_main.screen.planet == "zorta", "the first planet offered is Zorta")
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
	_expect(not SaveGame.exists("zorta", 1), "Delete removes the slot file")
	_expect(_button("Slot1New") != null and _button("Slot1Delete") == null, "a deleted slot offers New Game again")

	# Continue goes straight to the campaign at the saved checkpoint.
	var progress = Planets.new_progress("zorta")
	progress.checkpoint = Vector2i(5, 2)
	progress.max_hp = 7
	SaveGame.write("zorta", 2, progress)
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
	_expect(_main.screen.scene_file_path == "res://scenes/title.tscn", "the title is a scene that can be laid out in the editor")
	_expect(_main.screen.theme != null, "the title takes its look from a theme")
	var credits: Node = _main.screen.find_child("MenuCredits", true, false)
	_expect(credits != null, "the title shows the credits")
	if credits != null:
		var lines: Array[String] = []
		for child in credits.get_node("VBoxContainer").get_children():
			lines.append(String(child.name))
		_expect(lines == ["NameVersionLabel", "CreatedByLabel", "DiscordLabel"], "the credits hold the name, creator and Discord lines, got %s" % [lines])
		_expect(credits.get_node("%NameVersionLabel").text == "Extranaut v2.0", "the credits name the game and its version")
		_expect(_main.screen.find_child("Version", true, false) == null, "the version is shown once, in the credits")
		_expect(credits.get_node("%CreatedByLabel").text.contains("freezebeam.bsky.social"), "the credits link to Bluesky")
		_expect(credits.get_node("%DiscordLabel").text.contains("discord.gg"), "the credits link to Discord")
	if _button("Chaosnaut") != null:
		_button("Chaosnaut").pressed.emit()
	await _settle()
	_expect(_is(ChaosnautScript), "the Chaosnaut button starts the mode")
	if _is(ChaosnautScript):
		_main.screen.finished.emit()
	await _settle()
	_expect(_is(TitleScript), "leaving Chaosnaut returns to the title")

	# The planet switch shows the other planet's slots and starts its campaign.
	SaveGame.write("zorta", 3, Planets.new_progress("zorta"))
	_main.show_title()
	await _settle()
	_expect(_label("PlanetLabel") == "Planet Zorta (classic)", "the label names Zorta as classic")
	_expect(_button("Slot3Continue") != null, "Zorta's slot 3 is in use")
	_button("PlanetNext").pressed.emit()
	await _settle()
	_expect(_main.screen.planet == "korvax", "the switch moves to Korvax")
	_expect(_label("PlanetLabel") == "Zorta Depths (new - 2026)", "the label names the new planet as new - 2026")
	_expect(_button("Slot3New") != null and _button("Slot3Continue") == null, "Korvax's slot 3 is empty")
	_button("Slot3New").pressed.emit()
	await _settle()
	_expect(SaveGame.exists("korvax", 3), "a Korvax new game writes a Korvax slot")
	_press_key(KEY_SPACE)
	await _settle()
	_expect(_is(CampaignScript), "dismissing the intro starts the Korvax campaign")
	if _is(CampaignScript):
		_expect(_main.screen.planet == "korvax", "the campaign is on Korvax")
		_expect(_main.screen.grid == Vector2i(2, 0), "Korvax starts in room 2,0")
		_main.screen.quit_to_title.emit()
	await _settle()
	_expect(_is(TitleScript) and _main.screen.planet == "korvax", "the title remembers the last planet")
	_expect(_button("Slot3Continue") != null, "the Korvax slot is now in use")
	_button("Slot3Delete").pressed.emit()
	await _settle()
	_expect(not SaveGame.exists("korvax", 3) and SaveGame.exists("zorta", 3), "Delete removes only that planet's slot")
	_button("PlanetPrev").pressed.emit()
	await _settle()
	_expect(_main.screen.planet == "zorta", "the switch moves back to Zorta")
	_expect(_button("Slot3Continue") != null, "Zorta's slot 3 is still there")

	_clear_saves()
	print("main test passed" if _failures == 0 else "main test FAILED: %d failures" % _failures)
	quit(1 if _failures > 0 else 0)


func _clear_saves() -> void:
	for planet: String in Planets.ORDER:
		for slot in SaveGame.SLOTS:
			SaveGame.delete(planet, slot)
	if FileAccess.file_exists(Settings.path()):
		DirAccess.remove_absolute(Settings.path())


func _label(node_name: String) -> String:
	var label := _main.screen.find_child(node_name, true, false) as Label
	return "" if label == null else label.text


func _is(script: Script) -> bool:
	return _main.screen != null and _main.screen.get_script() == script


## A button the screen is showing, or null. The title keeps every slot's
## buttons in its scene and hides the ones that do not apply.
func _button(node_name: String) -> Button:
	var button := _main.screen.find_child(node_name, true, false) as Button
	return button if button != null and button.is_visible_in_tree() else null


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
