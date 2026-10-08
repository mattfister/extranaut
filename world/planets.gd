extends RefCounted
## The campaign planets: where each one's rooms and saves live.

const Progress := preload("res://save/progress.gd")

const ZORTA := "zorta"
const KORVAX := "korvax"
## Order shown on the title screen.
const ORDER := [ZORTA, KORVAX]

const DATA := {
	ZORTA: {
		"name": "Planet Zorta",
		"label": "classic",
		"rooms_dir": "res://world/rooms",
		"world_json": "res://tools/zorta.json",
		"save_prefix": "save_",
		"start_room": Vector2i(4, 2),
	},
	KORVAX: {
		"name": "Zorta Depths",
		"label": "new - 2026",
		"rooms_dir": "res://world/rooms_korvax",
		"world_json": "res://tools/korvax.json",
		"save_prefix": "save_korvax_",
		"start_room": Vector2i(2, 0),
	},
}


static func exists(planet: String) -> bool:
	return DATA.has(planet)


## The name as the title screen shows it, such as "Planet Zorta (classic)".
static func title(planet: String) -> String:
	return "%s (%s)" % [DATA[planet].name, DATA[planet].label]


static func room_path(planet: String, at: Vector2i) -> String:
	return "%s/room_%d_%d.tscn" % [DATA[planet].rooms_dir, at.x, at.y]


## A new game's progress on a planet.
static func new_progress(planet: String) -> RefCounted:
	var progress := Progress.new()
	progress.checkpoint = DATA[planet].start_room
	return progress
