extends Control
## The title screen: a planet switch, then for the chosen planet a New Game
## button for each empty save slot and Continue and Delete for each used one,
## and sound and fullscreen toggles.
##
## The layout lives in title.tscn and the look in ui/ui_theme.tres; move and
## restyle things there. This script only wires the buttons up and decides
## which of each slot's buttons to show. It finds nodes by name, so keep the
## names when rearranging.

signal new_game(planet: String, slot: int)
signal continue_game(planet: String, slot: int)
signal chaosnaut_pressed

const SaveGame := preload("res://save/save_game.gd")
const Planets := preload("res://world/planets.gd")
const Settings := preload("res://save/settings.gd")
const OptionsSheet := preload("res://assets/sprites/options.png")

const TITLE_FRAME_TIME := 0.06
const ICON_SOUND_OFF := Rect2(0, 0, 16, 16)
const ICON_SOUND_ON := Rect2(16, 0, 16, 16)
const ICON_WINDOWED := Rect2(0, 16, 16, 16)
const ICON_FULLSCREEN := Rect2(16, 16, 16, 16)

## The planet whose save slots are shown.
var planet := Planets.ZORTA

var _title_elapsed := 0.0

@onready var _logo: Sprite2D = $Logo
@onready var _planet_label: Label = $PlanetLabel
@onready var _slots: Control = $Slots
@onready var _sound_button: Button = $SoundToggle
@onready var _fullscreen_button: Button = $FullscreenToggle


func _ready() -> void:
	get_tree().call_group("audio", "play_music", "ruinsCore")
	get_tree().call_group("audio", "play", "extranautTitle")
	planet = Settings.last_planet()
	$PlanetPrev.pressed.connect(_step_planet.bind(-1))
	$PlanetNext.pressed.connect(_step_planet.bind(1))
	for slot: int in SaveGame.SLOTS:
		_slot_button(slot, "New").pressed.connect(func() -> void: new_game.emit(planet, slot))
		_slot_button(slot, "Continue").pressed.connect(func() -> void: continue_game.emit(planet, slot))
		_slot_button(slot, "Delete").pressed.connect(_delete_slot.bind(slot))
	$Chaosnaut.pressed.connect(func() -> void: chaosnaut_pressed.emit())
	_sound_button.pressed.connect(_toggle_sound)
	_fullscreen_button.pressed.connect(_toggle_fullscreen)
	_refresh_slots()
	_refresh_toggles()


func _process(delta: float) -> void:
	_title_elapsed += delta
	if _title_elapsed >= TITLE_FRAME_TIME:
		_title_elapsed -= TITLE_FRAME_TIME
		_logo.frame = (_logo.frame + 1) % _logo.hframes


## One of a slot's three buttons: "New", "Continue" or "Delete".
func _slot_button(slot: int, action: String) -> Button:
	return _slots.get_node("Slot%d%s" % [slot, action])


func _step_planet(step: int) -> void:
	var index := Planets.ORDER.find(planet)
	planet = Planets.ORDER[posmod(index + step, Planets.ORDER.size())]
	Settings.set_last_planet(planet)
	_refresh_slots()


## Shows New Game for each empty slot of the planet, and Continue and Delete
## for each used one.
func _refresh_slots() -> void:
	_planet_label.text = Planets.title(planet)
	for slot: int in SaveGame.SLOTS:
		var used := SaveGame.read(planet, slot) != null
		_slot_button(slot, "New").visible = not used
		_slot_button(slot, "Continue").visible = used
		_slot_button(slot, "Delete").visible = used
	var first: int = SaveGame.SLOTS[0]
	var top := _slot_button(first, "New")
	if not top.visible:
		top = _slot_button(first, "Continue")
	top.grab_focus.call_deferred()


func _delete_slot(slot: int) -> void:
	SaveGame.delete(planet, slot)
	_refresh_slots()


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
