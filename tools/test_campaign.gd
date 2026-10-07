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
	# Checked now, while paused: once the slide ends, monsters in the new room
	# fire shots of their own.
	var live_shots := 0
	for shot in shots.get_children():
		if not shot.is_queued_for_deletion():
			live_shots += 1
	_expect(live_shots == 0, "shots are cleared on transition")
	await _frames(40)
	_expect(not paused, "tree resumes after the slide")
	_expect(campaign.get_node("World").get_child_count() == 1, "old room is freed")
	_expect(campaign.room.position == Vector2(5 * 960, 2 * 768), "new room is placed in world space")
	local = player.global_position - campaign.room.position
	_expect(local.x >= 17.0 and local.x < 300.0, "player enters at the left, x %.1f" % local.x)
	var camera: Camera2D = campaign.get_node("Camera2D")
	_expect(camera.position == campaign.room.position + Vector2(512, 384), "camera is on the new room")

	await _check_checkpoint_and_respawn(campaign, player)
	_check_powerups_taken(campaign)
	root.remove_child(campaign)
	campaign.free()
	await _check_one_tile_shaft()

	print("campaign test passed" if _failures == 0 else "campaign test FAILED: %d failures" % _failures)
	quit(1 if _failures > 0 else 0)


## Room (3, 2) has a hidden one-tile shaft in its floor: x 96 to 128, from
## y 640 down to the bottom of the room. The player must fit through it, both
## dropped in from above and when running up to it and letting go.
func _check_one_tile_shaft() -> void:
	for approach in ["drop", "run"]:
		var campaign: Node2D = load("res://scenes/campaign.tscn").instantiate()
		campaign.grid = Vector2i(3, 2)
		root.add_child(campaign)
		var player: RigidBody2D = campaign.get_node("Player")
		await _frames(2)
		if approach == "drop":
			player.global_position = campaign.room.position + Vector2(112, 600)
		else:
			player.global_position = campaign.room.position + Vector2(200, 620)
			Input.action_press("move_left")
		player.linear_velocity = Vector2.ZERO
		var waited := 0
		while campaign.grid != Vector2i(3, 3) and waited < 180:
			await physics_frame
			waited += 1
			# Running straight across at full speed skips the hole, as it would
			# have in the original; letting go over it must be enough.
			if player.global_position.x - campaign.room.position.x <= 120.0:
				Input.action_release("move_left")
		Input.action_release("move_left")
		var local: Vector2 = player.global_position - campaign.room.position
		_expect(campaign.grid == Vector2i(3, 3), "%s: falls through the one-tile shaft, ended at %s in %s" % [approach, local, campaign.grid])
		await _frames(40)
		root.remove_child(campaign)
		campaign.free()


## Runs in room (5, 2), reached by the transition check above.
func _check_checkpoint_and_respawn(campaign: Node2D, player: RigidBody2D) -> void:
	_expect(campaign.checkpoint == Vector2i(4, 2), "the checkpoint starts at the start room")
	# Dying returns the player to the checkpoint room with full hp.
	player.revive()
	player.hp = 1
	player.hit()
	var waited := 0
	while campaign.grid != Vector2i(4, 2) and waited < 180:
		await physics_frame
		waited += 1
	_expect(campaign.grid == Vector2i(4, 2), "death respawns in the checkpoint room, grid %s" % campaign.grid)
	_expect(player.hp == player.max_hp and not player.is_dead(), "respawn restores full hp")
	var local: Vector2 = player.global_position - campaign.room.position
	_expect(local.distance_to(Vector2(480, 352)) < 80.0, "respawn is at the room's player start, at %s" % local)
	_expect(campaign.get_node("World").get_child_count() == 1, "only the checkpoint room is loaded")
	await _frames(30)

	# Shooting the start room's save point sets the checkpoint and heals.
	var save_point: Node = campaign.room.get_node("Entities").get_child(0)
	campaign.checkpoint = Vector2i(0, 0)
	player.hp = 2
	save_point.hit()
	_expect(campaign.checkpoint == Vector2i(4, 2), "a save point sets the checkpoint")
	_expect(player.hp == player.max_hp, "a save point heals the player")


func _check_powerups_taken(campaign: Node2D) -> void:
	var world = JSON.parse_string(FileAccess.get_file_as_string("res://tools/zorta.json"))
	var at := Vector2i(-1, -1)
	for data in world.rooms:
		for m in data.monsters:
			if m[0] == "HpPowerup":
				at = Vector2i(int(data.x), int(data.y))
	_expect(at != Vector2i(-1, -1), "found a room with an hp powerup")
	var fresh: Node2D = campaign.load_room(at)
	_expect(_count_powerups(fresh) == 1, "an untouched room has its powerup")
	fresh.free()
	campaign.powerups_taken[at] = true
	var revisited: Node2D = campaign.load_room(at)
	_expect(_count_powerups(revisited) == 0, "a taken powerup does not come back")
	revisited.free()
	campaign.powerups_taken.erase(at)


func _count_powerups(room: Node2D) -> int:
	var count := 0
	for entity in room.get_node("Entities").get_children():
		if entity.is_powerup:
			count += 1
	return count


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
