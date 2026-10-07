class_name MonsterSpawn
extends Marker2D
## Stands in for a monster whose scene does not exist yet. The importer
## replaces these with real instances once entities/monsters/<kind>.tscn exists.

@export var kind := ""
