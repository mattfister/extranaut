extends Control
## The strip down the right of the screen: HP and fuel pips stacked from the
## bottom, and artifacts collected. A notice in the top left of the screen
## shows when the game saves. The minimap is a child node.

const UiKit := preload("res://ui/ui_kit.gd")
const BarsTexture := preload("res://assets/sprites/bars.png")
const CollectiblesTexture := preload("res://assets/animations/collectibles.png")

const STRIP := Rect2(960, 0, 64, 768)
const PIP_SIZE := 32.0
const HP_REGION := Rect2(0, 0, 16, 16)
const FUEL_REGION := Rect2(16, 0, 16, 16)
const ARTIFACT_REGION := Rect2(0, 16, 16, 16)
const FUEL_PER_PIP := 500.0
const ARTIFACTS_TOP := 72.0
const SAVED_NOTICE_TIME := 1.5
const SAVED_NOTICE_AT := Vector2(8, 8)

var _hp := 0
var _fuel_pips := 0
var _artifacts := 0
var _saved_timer := 0.0
var _saved_label: Label


static func fuel_pips(fuel: float) -> int:
	return int(fuel / FUEL_PER_PIP)


func _ready() -> void:
	_saved_label = UiKit.make_label("SAVED")
	_saved_label.position = SAVED_NOTICE_AT
	_saved_label.hide()
	add_child(_saved_label)


func set_status(hp: int, fuel: float, artifacts: int) -> void:
	var pips := fuel_pips(fuel)
	if hp != _hp or pips != _fuel_pips or artifacts != _artifacts:
		_hp = hp
		_fuel_pips = pips
		_artifacts = artifacts
		queue_redraw()


func show_saved() -> void:
	_saved_label.show()
	_saved_timer = SAVED_NOTICE_TIME


func _process(delta: float) -> void:
	if _saved_timer > 0.0:
		_saved_timer -= delta
		if _saved_timer <= 0.0:
			_saved_label.hide()


func _draw() -> void:
	draw_rect(STRIP, Color.BLACK)
	var bottom := STRIP.position.y + STRIP.size.y
	for i in _hp:
		var at := Vector2(STRIP.position.x, bottom - PIP_SIZE * (i + 1))
		draw_texture_rect_region(BarsTexture, Rect2(at, Vector2(PIP_SIZE, PIP_SIZE)), HP_REGION)
	for i in _fuel_pips:
		var at := Vector2(STRIP.position.x + PIP_SIZE, bottom - PIP_SIZE * (i + 1))
		draw_texture_rect_region(BarsTexture, Rect2(at, Vector2(PIP_SIZE, PIP_SIZE)), FUEL_REGION)
	for i in _artifacts:
		var at := Vector2(STRIP.position.x + PIP_SIZE * (i % 2), ARTIFACTS_TOP + PIP_SIZE * (i / 2))
		draw_texture_rect_region(CollectiblesTexture, Rect2(at, Vector2(PIP_SIZE, PIP_SIZE)), ARTIFACT_REGION)
