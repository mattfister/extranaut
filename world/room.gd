class_name Room
extends Node2D
## Root of a generated room scene. See tools/import_world.gd.

const SIZE := Vector2(960, 768)

@export var grid_pos := Vector2i.ZERO
## Track name in assets/sounds, or empty to keep whatever is playing.
@export var music := ""
@export var has_player_start := false
@export var player_start := Vector2.ZERO
