extends CanvasLayer
## The pause overlay: a large map with Resume and Quit to Title.

signal resume_pressed
signal quit_pressed

const UiKit := preload("res://ui/ui_kit.gd")
const MapView := preload("res://ui/map_view.gd")

const SCREEN := Vector2(1024, 768)
const MAP_CELL := 24.0
const BUTTON_SIZE := Vector2(140, 20)

## Set false before adding to the tree for modes that have no map.
@export var show_map := true

var _map: Control
var _resume: Button


func _ready() -> void:
	var dim := ColorRect.new()
	dim.color = Color(0, 0, 0, 0.8)
	dim.size = SCREEN
	add_child(dim)

	var heading := UiKit.make_label("PAUSED")
	heading.position = Vector2(0, 80)
	heading.size = Vector2(SCREEN.x, 20)
	heading.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(heading)

	_map = Control.new()
	_map.set_script(MapView)
	_map.cell_size = MAP_CELL
	_map.position = Vector2((SCREEN.x - MAP_CELL * 10.0) / 2.0, 130)
	_map.size = Vector2(MAP_CELL * 10.0, MAP_CELL * 10.0)
	add_child(_map)
	_map.visible = show_map

	_resume = _add_button("Resume", "Resume Game", 420.0)
	_resume.pressed.connect(func() -> void: resume_pressed.emit())
	var quit := _add_button("Quit", "Quit to Title", 470.0)
	quit.pressed.connect(func() -> void: quit_pressed.emit())


## progress is a save/progress.gd object, or null when there is no map.
func open(progress: RefCounted, current: Vector2i) -> void:
	if progress != null:
		_map.show_progress(progress, current)
	_resume.grab_focus()


func _add_button(node_name: String, text: String, y: float) -> Button:
	var button := UiKit.make_button(text, BUTTON_SIZE)
	button.name = node_name
	button.position = Vector2((SCREEN.x - BUTTON_SIZE.x) / 2.0, y)
	add_child(button)
	return button
