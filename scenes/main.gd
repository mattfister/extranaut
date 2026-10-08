extends Node
## The screen flow. Shows one screen at a time: the title, an image screen
## (intro or ending) or the campaign.
## Development options after "--" on the command line:
##   --room=X,Y   skip the title and start an unsaved campaign in that room
##   --shot=PATH  save a screenshot after one second and quit

const Controls := preload("res://input/controls.gd")
const Progress := preload("res://save/progress.gd")
const SaveGame := preload("res://save/save_game.gd")
const TitleScript := preload("res://scenes/title.gd")
const ImageScreenScript := preload("res://scenes/image_screen.gd")
const CampaignScene := preload("res://scenes/campaign.tscn")
const IntroImage := preload("res://assets/sprites/intro.png")
const EndingImage := preload("res://assets/sprites/ending.png")

## The screen currently shown.
var screen: Node


func _ready() -> void:
	Controls.setup()
	var shot_path := ""
	var skip_title := false
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--room="):
			skip_title = true
		elif arg.begins_with("--shot="):
			shot_path = arg.trim_prefix("--shot=")
	if skip_title:
		_start_campaign(0)
	else:
		show_title()
	if shot_path != "":
		await get_tree().create_timer(1.0).timeout
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png(shot_path)
		get_tree().quit()


func show_title() -> void:
	var title := Control.new()
	title.set_script(TitleScript)
	title.new_game.connect(_on_new_game, CONNECT_DEFERRED)
	title.continue_game.connect(_start_campaign, CONNECT_DEFERRED)
	_show(title)


func _on_new_game(slot: int) -> void:
	SaveGame.write(slot, Progress.new())
	_show_image(IntroImage, _start_campaign.bind(slot))
	get_tree().call_group("audio", "play", "intro")


## slot 0 plays without saving.
func _start_campaign(slot: int) -> void:
	var campaign := CampaignScene.instantiate()
	campaign.slot = slot
	if slot > 0:
		campaign.progress = SaveGame.read(slot)
	campaign.won.connect(_show_image.bind(EndingImage, show_title), CONNECT_DEFERRED)
	campaign.quit_to_title.connect(show_title, CONNECT_DEFERRED)
	_show(campaign)


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
