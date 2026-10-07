extends SceneTree
## Headless play test of the campaign scene.
## Run: godot --headless --path . --script res://tools/test_campaign.gd

const CampaignScript := preload("res://scenes/campaign.gd")

var _failures := 0


func _initialize() -> void:
	_run()


func _run() -> void:
	_check_exit_rules()

	var campaign: Node2D = load("res://scenes/campaign.tscn").instantiate()
	root.add_child(campaign)
	var player: RigidBody2D = campaign.get_node("Player")
	var shots: Node = campaign.get_node("Shots")
	await _frames(120)

	# Comes to rest on the ground of the start room.
	var local: Vector2 = player.global_position - campaign.room.position
	_expect(player.linear_velocity.length() < 5.0, "player rests, velocity %s" % player.linear_velocity)
	_expect(local.y > 352.0 and local.y < 768.0, "player is on the ground, y %.1f" % local.y)

	# Runs right at the original speed, off the ledge at x = 512, then stops.
	Input.action_press("move_right")
	await _frames(20)
	_expect(absf(player.linear_velocity.x - 200.0) < 20.0, "runs at 200, got %.1f" % player.linear_velocity.x)
	Input.action_release("move_right")
	await _frames(30)
	local = player.global_position - campaign.room.position
	_expect(local.x > 530.0, "runs past the ledge without snagging, x %.1f" % local.x)
	_expect(absf(player.linear_velocity.x) < 5.0, "stops when input is released")
	_expect(player.facing == 1, "faces right")

	# Jetpack lifts and burns fuel.
	await _frames(90)
	var start_y := player.global_position.y
	Input.action_press("jetpack")
	await _frames(30)
	Input.action_release("jetpack")
	_expect(player.global_position.y < start_y - 30.0, "jetpack lifts the player")
	_expect(player.jetpack.fuel < player.jetpack.max_fuel, "jetpack burns fuel")

	# Fires one shot to the right, and respects the cooldown.
	Input.action_press("fire")
	await _frames(3)
	Input.action_release("fire")
	_expect(shots.get_child_count() == 1, "one shot fired, got %d" % shots.get_child_count())
	if shots.get_child_count() > 0:
		_expect(shots.get_child(0).linear_velocity.x > 400.0, "shot flies right")

	# A fast fall does not pass through the floor (y = 640 at x = 64).
	player.global_position = campaign.room.position + Vector2(64, 300)
	player.linear_velocity = Vector2(0, 1500)
	await _frames(60)
	local = player.global_position - campaign.room.position
	_expect(local.y < 640.0, "fast fall stops on the floor, y %.1f" % local.y)
	player.global_position = campaign.room.position + Vector2(64, 300)
	player.linear_velocity = Vector2(0, 4000)
	await _frames(60)
	local = player.global_position - campaign.room.position
	_expect(local.y < 640.0, "very fast fall stops on the floor, y %.1f" % local.y)

	# Walking off the right edge moves to room (5, 2).
	player.global_position = campaign.room.position + Vector2(920, 440)
	player.linear_velocity = Vector2.ZERO
	await _frames(30)
	Input.action_press("move_right")
	var waited := 0
	while campaign.grid != Vector2i(5, 2) and waited < 120:
		await physics_frame
		waited += 1
	Input.action_release("move_right")
	_expect(campaign.grid == Vector2i(5, 2), "entered room 5,2, grid is %s" % campaign.grid)
	_expect(paused, "tree is paused during the slide")
	await _frames(40)
	_expect(not paused, "tree resumes after the slide")
	_expect(campaign.get_node("World").get_child_count() == 1, "old room is freed")
	_expect(campaign.room.position == Vector2(5 * 960, 2 * 768), "new room is placed in world space")
	local = player.global_position - campaign.room.position
	_expect(local.x >= 17.0 and local.x < 300.0, "player enters at the left, x %.1f" % local.x)
	var camera: Camera2D = campaign.get_node("Camera2D")
	_expect(camera.position == campaign.room.position + Vector2(512, 384), "camera is on the new room")
	_expect(shots.get_child_count() == 0, "shots are cleared on transition")

	print("campaign test passed" if _failures == 0 else "campaign test FAILED: %d failures" % _failures)
	quit(1 if _failures > 0 else 0)


func _check_exit_rules() -> void:
	_expect(CampaignScript.exit_step(Vector2(480, 384)) == Vector2i.ZERO, "no exit mid-room")
	_expect(CampaignScript.exit_step(Vector2(943, 384)) == Vector2i.RIGHT, "exit right at 943")
	_expect(CampaignScript.exit_step(Vector2(942.9, 384)) == Vector2i.ZERO, "no exit at 942.9")
	_expect(CampaignScript.exit_step(Vector2(16.9, 384)) == Vector2i.LEFT, "exit left at 16.9")
	_expect(CampaignScript.exit_step(Vector2(17, 384)) == Vector2i.ZERO, "no exit at 17")
	_expect(CampaignScript.exit_step(Vector2(480, 742)) == Vector2i.DOWN, "exit down at 742")
	_expect(CampaignScript.exit_step(Vector2(480, 26.9)) == Vector2i.UP, "exit up at 26.9")
	_expect(CampaignScript.exit_step(Vector2(480, 27)) == Vector2i.ZERO, "no exit at y 27")
	_expect(CampaignScript.entry_position(Vector2i.RIGHT, Vector2(943, 300)) == Vector2(17, 300), "enter from left side")
	_expect(CampaignScript.entry_position(Vector2i.LEFT, Vector2(16, 300)) == Vector2(943, 300), "enter from right side")
	_expect(CampaignScript.entry_position(Vector2i.DOWN, Vector2(200, 742)) == Vector2(200, 16), "enter from top")
	_expect(CampaignScript.entry_position(Vector2i.UP, Vector2(200, 26)) == Vector2(200, 720), "enter from bottom")
	# Entry positions are outside the exit zone on the side just crossed, or
	# inside it only where the armed flag covers the bounce (vertical entries).
	_expect(CampaignScript.exit_step(Vector2(17, 300)) == Vector2i.ZERO, "left entry is clear of the exit zone")
	_expect(CampaignScript.exit_step(Vector2(943, 300)) == Vector2i.RIGHT, "right entry relies on the armed flag")


func _frames(count: int) -> void:
	for i in count:
		await physics_frame


func _expect(condition: bool, message: String) -> void:
	if not condition:
		_failures += 1
		printerr("FAIL: " + message)
