extends Control
## The title screen: a planet switch, then for the chosen planet a New Game
## button for each empty save slot and Continue and Delete for each used one,
## and sound and fullscreen toggles.

signal new_game(planet: String, slot: int)
signal continue_game(planet: String, slot: int)
signal chaosnaut_pressed

const UiKit := preload("res://ui/ui_kit.gd")
const SaveGame := preload("res://save/save_game.gd")
const Planets := preload("res://world/planets.gd")
const Settings := preload("res://save/settings.gd")
const Background := preload("res://assets/sprites/titleTerrainSmall.png")
const TitleSheet := preload("res://assets/sprites/extranautTitleAnimated.png")
const KopaStrip := preload("res://assets/sprites/kopa.png")
const MattStrip := preload("res://assets/sprites/matt.png")
const OptionsSheet := preload("res://assets/sprites/options.png")

const CENTER_X := 512.0
const PLANET_Y := 344.0
const ARROW_BUTTON := Vector2(34, 20)
const PLANET_LABEL_WIDTH := 300.0
const SLOTS_TOP := 384.0
const SLOT_SPACING := 60.0
const CHAOSNAUT_Y := 564.0
const SMALL_BUTTON := Vector2(140, 20)
const WIDE_BUTTON := Vector2(240, 20)
const TITLE_FRAME_TIME := 0.06
const TOGGLE_SIZE := Vector2(34, 34)
const ICON_SOUND_OFF := Rect2(0, 0, 16, 16)
const ICON_SOUND_ON := Rect2(16, 0, 16, 16)
const ICON_WINDOWED := Rect2(0, 16, 16, 16)
const ICON_FULLSCREEN := Rect2(16, 16, 16, 16)

## The planet whose save slots are shown.
var planet := Planets.ZORTA

var _planet_label: Label
var _slots: Control
var _title: Sprite2D
var _title_elapsed := 0.0
var _sound_button: Button
var _fullscreen_button: Button


func _ready() -> void:
	get_tree().call_group("audio", "play_music", "ruinsCore")
	get_tree().call_group("audio", "play", "extranautTitle")
	_add_image(Background, Vector2.ZERO, 2.0)
	_title = Sprite2D.new()
	_title.texture = TitleSheet
	_title.hframes = 4
	_title.centered = false
	_title.scale = Vector2(4, 4)
	_title.position = Vector2(250, 50)
	add_child(_title)
	_add_image(KopaStrip, Vector2(80, 250), 2.0)
	_add_image(MattStrip, Vector2(300, 300), 2.0)

	planet = Settings.last_planet()
	var half := PLANET_LABEL_WIDTH / 2.0
	var prev := _add_planet_button("PlanetPrev", "<", CENTER_X - half - ARROW_BUTTON.x, -1)
	_add_planet_button("PlanetNext", ">", CENTER_X + half, 1)
	_planet_label = UiKit.make_label("")
	_planet_label.name = "PlanetLabel"
	_planet_label.position = Vector2(CENTER_X - half, PLANET_Y)
	# As tall as the buttons really are, so the name sits level with the arrows.
	_planet_label.size = Vector2(PLANET_LABEL_WIDTH, prev.get_combined_minimum_size().y)
	_planet_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_planet_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	add_child(_planet_label)

	_slots = Control.new()
	add_child(_slots)
	_build_slots()
	var chaosnaut := UiKit.make_button("Chaosnaut", SMALL_BUTTON)
	chaosnaut.name = "Chaosnaut"
	chaosnaut.position = Vector2(CENTER_X - SMALL_BUTTON.x / 2.0, CHAOSNAUT_Y)
	chaosnaut.pressed.connect(func() -> void: chaosnaut_pressed.emit())
	add_child(chaosnaut)

	_sound_button = _add_toggle(Vector2(0, 734), _toggle_sound)
	_fullscreen_button = _add_toggle(Vector2(33, 734), _toggle_fullscreen)
	_refresh_toggles()
	var version := UiKit.make_label("Version 2.0")
	version.position = Vector2(76, 742)
	add_child(version)


func _process(delta: float) -> void:
	_title_elapsed += delta
	if _title_elapsed >= TITLE_FRAME_TIME:
		_title_elapsed -= TITLE_FRAME_TIME
		_title.frame = (_title.frame + 1) % _title.hframes


func _add_planet_button(node_name: String, text: String, x: float, step: int) -> Button:
	var button := UiKit.make_button(text, ARROW_BUTTON)
	button.name = node_name
	button.position = Vector2(x, PLANET_Y)
	button.pressed.connect(_step_planet.bind(step))
	add_child(button)
	return button


func _step_planet(step: int) -> void:
	var index := Planets.ORDER.find(planet)
	planet = Planets.ORDER[posmod(index + step, Planets.ORDER.size())]
	Settings.set_last_planet(planet)
	_build_slots()


func _build_slots() -> void:
	_planet_label.text = Planets.title(planet)
	for child in _slots.get_children():
		_slots.remove_child(child)
		child.free()
	for slot: int in SaveGame.SLOTS:
		var y: float = SLOTS_TOP + SLOT_SPACING * (slot - 1)
		if SaveGame.read(planet, slot) != null:
			var resume := _add_slot_button("Slot%dContinue" % slot, "Continue Game %d" % slot, Vector2(CENTER_X - SMALL_BUTTON.x - 25.0, y), SMALL_BUTTON)
			resume.pressed.connect(func() -> void: continue_game.emit(planet, slot))
			var delete := _add_slot_button("Slot%dDelete" % slot, "Delete Game %d" % slot, Vector2(CENTER_X + 25.0, y), SMALL_BUTTON)
			delete.pressed.connect(_delete_slot.bind(slot))
		else:
			var fresh := _add_slot_button("Slot%dNew" % slot, "New Game %d" % slot, Vector2(CENTER_X - WIDE_BUTTON.x / 2.0, y), WIDE_BUTTON)
			fresh.pressed.connect(func() -> void: new_game.emit(planet, slot))
	(_slots.get_child(0) as Button).grab_focus.call_deferred()


func _delete_slot(slot: int) -> void:
	SaveGame.delete(planet, slot)
	# Deferred: rebuilding frees the button whose signal is being handled.
	_build_slots.call_deferred()


func _add_slot_button(node_name: String, text: String, at: Vector2, button_size: Vector2) -> Button:
	var button := UiKit.make_button(text, button_size)
	button.name = node_name
	button.position = at
	_slots.add_child(button)
	return button


func _add_image(image: Texture2D, at: Vector2, image_scale: float) -> void:
	var rect := TextureRect.new()
	rect.texture = image
	rect.position = at
	rect.scale = Vector2(image_scale, image_scale)
	rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(rect)


func _add_toggle(at: Vector2, on_pressed: Callable) -> Button:
	var button := UiKit.make_button("", TOGGLE_SIZE)
	button.position = at
	button.expand_icon = true
	button.pressed.connect(on_pressed)
	add_child(button)
	return button


func _toggle_sound() -> void:
	AudioServer.set_bus_mute(0, not AudioServer.is_bus_mute(0))
	_refresh_toggles()


func _toggle_fullscreen() -> void:
	var fullscreen := DisplayServer.window_get_mode() == DisplayServer.WINDOW_MODE_FULLSCREEN
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED if fullscreen else DisplayServer.WINDOW_MODE_FULLSCREEN)
	_refresh_toggles()


func _refresh_toggles() -> void:
	_sound_button.icon = _icon(ICON_SOUND_OFF if AudioServer.is_bus_mute(0) else ICON_SOUND_ON)
	var fullscreen := DisplayServer.window_get_mode() == DisplayServer.WINDOW_MODE_FULLSCREEN
	_fullscreen_button.icon = _icon(ICON_FULLSCREEN if fullscreen else ICON_WINDOWED)


func _icon(region: Rect2) -> AtlasTexture:
	var icon := AtlasTexture.new()
	icon.atlas = OptionsSheet
	icon.region = region
	return icon
