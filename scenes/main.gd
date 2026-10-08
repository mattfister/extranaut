extends Node
## The screen flow. Shows one screen at a time: the title, an image screen
## (intro or ending) or the campaign.
## Development options after "--" on the command line:
##   --room=X,Y   skip the title and start an unsaved campaign in that room
##   --planet=ID  skip the title and start an unsaved campaign on that planet
##   --chaosnaut  skip the title and start Chaosnaut
##   --shot=PATH  save a screenshot after one second and quit

const Controls := preload("res://input/controls.gd")
const SaveGame := preload("res://save/save_game.gd")
const Planets := preload("res://world/planets.gd")
const TitleScene := preload("res://scenes/title.tscn")
const ImageScreenScript := preload("res://scenes/image_screen.gd")
const CampaignScene := preload("res://scenes/campaign.tscn")
const ChaosnautScene := preload("res://scenes/chaosnaut.tscn")
const IntroImage := preload("res://assets/sprites/intro.png")
const EndingImage := preload("res://assets/sprites/ending.png")

## The screen currently shown.
var screen: Node


func _ready() -> void:
	Controls.setup()
	var shot_path := ""
	var skip_title := false
	var chaosnaut := false
	var planet := Planets.ZORTA
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--room="):
			skip_title = true
		elif arg.begins_with("--planet=") and Planets.exists(arg.trim_prefix("--planet=")):
			planet = arg.trim_prefix("--planet=")
			skip_title = true
		elif arg == "--chaosnaut":
			chaosnaut = true
		elif arg.begins_with("--shot="):
			shot_path = arg.trim_prefix("--shot=")
	if chaosnaut:
		_start_chaosnaut()
	elif skip_title:
		_start_campaign(planet, 0)
	else:
		show_title()
	if shot_path != "":
		await get_tree().create_timer(1.0).timeout
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png(shot_path)
		get_tree().quit()


func show_title() -> void:
	var title := TitleScene.instantiate()
	title.new_game.connect(_on_new_game, CONNECT_DEFERRED)
	title.continue_game.connect(_start_campaign, CONNECT_DEFERRED)
	title.chaosnaut_pressed.connect(_start_chaosnaut, CONNECT_DEFERRED)
	_show(title)


func _on_new_game(planet: String, slot: int) -> void:
	SaveGame.write(planet, slot, Planets.new_progress(planet))
	_show_image(IntroImage, _start_campaign.bind(planet, slot))
	get_tree().call_group("audio", "play", "intro")


## slot 0 plays without saving.
func _start_campaign(planet: String, slot: int) -> void:
	var campaign := CampaignScene.instantiate()
	campaign.planet = planet
	campaign.slot = slot
	if slot > 0:
		campaign.progress = SaveGame.read(planet, slot)
	campaign.won.connect(_show_image.bind(EndingImage, show_title), CONNECT_DEFERRED)
	campaign.quit_to_title.connect(show_title, CONNECT_DEFERRED)
	_show(campaign)


func _start_chaosnaut() -> void:
	var chaosnaut := ChaosnautScene.instantiate()
	chaosnaut.finished.connect(show_title, CONNECT_DEFERRED)
	_show(chaosnaut)


func _show_image(image: Texture2D, then: Callable) -> void:
	var image_screen := Control.new()
	image_screen.set_script(ImageScreenScript)
	image_screen.texture = image
	image_screen.dismissed.connect(then, CONNECT_DEFERRED)
	_show(image_screen)


func _show(next: Node) -> void:
	if screen != null:
		remove_child(screen)
		screen.queue_free()
	get_tree().paused = false
	screen = next
	add_child(screen)
