extends Control
## Draws the 10x10 room map: explored rooms, known save points and the
## current room, which blinks.

enum Cell { UNKNOWN, VISITED, SAVE_POINT, CURRENT }

const GRID := Vector2i(10, 10)
const BLINK_PERIOD := 0.6
const COLORS := {
	Cell.UNKNOWN: Color(0.13, 0.13, 0.15),
	Cell.VISITED: Color(0.45, 0.45, 0.52),
	Cell.SAVE_POINT: Color(0.3, 0.6, 1.0),
	Cell.CURRENT: Color.WHITE,
}

## Pixels per room, including a one-pixel gap.
@export var cell_size := 6.0

var _visited := {}
var _save_points := {}
var _current := Vector2i(-1, -1)
var _blink := 0.0


static func cell_state(cell: Vector2i, visited: Dictionary, save_points: Dictionary, current: Vector2i) -> Cell:
	if cell == current:
		return Cell.CURRENT
	if not visited.has(cell):
		return Cell.UNKNOWN
	return Cell.SAVE_POINT if save_points.has(cell) else Cell.VISITED


## progress is a save/progress.gd object.
func show_progress(progress: RefCounted, current: Vector2i) -> void:
	_visited = progress.visited
	_save_points = progress.save_points
	_current = current
	queue_redraw()


func _process(delta: float) -> void:
	var was_lit := _is_lit()
	_blink = fmod(_blink + delta, BLINK_PERIOD)
	if was_lit != _is_lit():
		queue_redraw()


func _is_lit() -> bool:
	return _blink < BLINK_PERIOD / 2.0


func _draw() -> void:
	for y in GRID.y:
		for x in GRID.x:
			var cell := Vector2i(x, y)
			var state := cell_state(cell, _visited, _save_points, _current)
			if state == Cell.CURRENT and not _is_lit():
				# Blink to what the room would otherwise show.
				state = cell_state(cell, _visited, _save_points, Vector2i(-1, -1))
			draw_rect(Rect2(Vector2(cell) * cell_size, Vector2(cell_size - 1.0, cell_size - 1.0)), COLORS[state])
