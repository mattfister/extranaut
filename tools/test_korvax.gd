extends SceneTree
## Headless play test of the generated planet: the things the generator's own
## model of the player takes on trust, checked with the real physics.
## Run: godot --headless --path . --script res://tools/test_korvax.gd

const Planets := preload("res://world/planets.gd")

const PLANET := "korvax"
const TILE := 32.0
## How many ceiling openings to fly up through.
const CLIMBS := 6

var _failures := 0
var _world: Dictionary


func _initialize() -> void:
	_run()


func _run() -> void:
	_world = JSON.parse_string(FileAccess.get_file_as_string(Planets.DATA[PLANET].world_json))
	await process_frame
	await _check_climbs()
	await _check_gate()
	await _check_final_boss()
	await _check_final_room()
	print("korvax test passed" if _failures == 0 else "korvax test FAILED: %d failures" % _failures)
	quit(1 if _failures > 0 else 0)


## From the ledge beside a ceiling opening the player can fly into the room
## above and land beside the hole there.
func _check_climbs() -> void:
	var tried := 0
	for data in _world.rooms:
		# Lock-free rooms only: hostiles would knock the scripted flight about.
		if not data.links.has("N") or tried >= CLIMBS or data.kind == "boss":
			continue
		tried += 1
		var at := Vector2i(int(data.x), int(data.y))
		var above := at + Vector2i.UP
		var column := int(data.links["N"])
		var campaign := _start(at)
		var player: RigidBody2D = campaign.get_node("Player")
		_clear_monsters(campaign)
		var ledge_column := column + 3 if column < 14 else column - 1
		player.global_position = campaign.room.position + Vector2((ledge_column + 0.5) * TILE, 6.0 * TILE - 13.0)
		player.linear_velocity = Vector2.ZERO
		await _frames(20)
		var local: Vector2 = player.global_position - campaign.room.position
		_expect(absf(local.y - (6.0 * TILE - 13.0)) < 2.0, "%s: there is a ledge beside the ceiling opening, y %.1f" % [at, local.y])

		var hole_x := (column + 1.5) * TILE
		var landing_x := (column + 3.5) * TILE
		var rested := 0
		for i in 600:
			if campaign.grid == at:
				_steer(player, campaign.room.position.x + hole_x)
				Input.action_press("jetpack")
			else:
				_clear_monsters(campaign)
				local = player.global_position - campaign.room.position
				_steer(player, campaign.room.position.x + landing_x)
				if local.y < 690.0:
					Input.action_release("jetpack")
				rested = rested + 1 if player.linear_velocity.length() < 5.0 else 0
				if rested >= 20:
					break
			await physics_frame
		_release_all()
		local = player.global_position - campaign.room.position
		_expect(campaign.grid == above, "%s: flying up reaches the room above, ended in %s" % [at, campaign.grid])
		_expect(rested >= 20 and local.y < 742.0, "%s: the player lands beside the hole, at %s" % [at, local])
		await _stop(campaign)
	_expect(tried == CLIMBS, "found %d ceiling openings to try" % tried)


## The artifact door holds until the player has four artifacts.
func _check_gate() -> void:
	var data := _room_of_kind("gate")
	var campaign := _start(Vector2i(int(data.x), int(data.y)))
	var player: RigidBody2D = campaign.get_node("Player")
	var door: RigidBody2D
	for entity in campaign.room.get_node("Entities").get_children():
		if entity.name.begins_with("ArtifactDoor"):
			door = entity
	_expect(door != null, "the gate room has an artifact door")
	if door != null:
		var door_start := door.position
		_clear_monsters(campaign, door)
		player.artifacts = 3
		await _frames(120)
		_expect(is_instance_valid(door) and door.position.distance_to(door_start) < 4.0, "the artifact door stays put with 3 artifacts")
		player.artifacts = 4
		await _frames(5)
		_expect(not is_instance_valid(door), "the artifact door opens with 4 artifacts")
	await _stop(campaign)


## The way out of the final room stays plugged until the final boss and its
## escorts are dead.
func _check_final_boss() -> void:
	var data := _room_of_kind("final")
	var campaign := _start(Vector2i(int(data.x), int(data.y)))
	var player: RigidBody2D = campaign.get_node("Player")
	var entities: Node = campaign.room.get_node("Entities")
	var door: RigidBody2D
	var boss: Node
	for entity in entities.get_children():
		if entity.name.begins_with("MonsterDoor"):
			door = entity
		elif entity.name.begins_with("FallenExtranaut"):
			boss = entity
	_expect(door != null and boss != null, "the final room has a door and the final boss")
	if door != null and boss != null:
		var door_start := door.position
		for i in 180:
			await physics_frame
			# Keep the player alive while the fight goes on around it.
			player.hp = player.max_hp
		_expect(is_instance_valid(door) and door.position.distance_to(door_start) < 4.0, "the way out stays plugged while the boss lives")
		for entity in entities.get_children():
			if entity != door and entity != boss and is_instance_valid(entity):
				entity.die()
		await _frames(5)
		_expect(is_instance_valid(door), "killing the escorts alone does not open the way out")
		boss.die()
		await _frames(5)
		_expect(not is_instance_valid(door), "the way out opens when the final boss is dead")
	await _stop(campaign)


## Dropping through the final room's floor wins the game.
func _check_final_room() -> void:
	var data := _room_of_kind("final")
	var campaign := _start(Vector2i(int(data.x), int(data.y)))
	var player: RigidBody2D = campaign.get_node("Player")
	_clear_monsters(campaign)
	var wins := [0]
	campaign.won.connect(func() -> void: wins[0] += 1)
	await _frames(30)
	_expect(wins[0] == 0, "standing in the final room does not win")
	var hole: int = String(data.cells[23]).find(".")
	_expect(hole >= 0, "the final room has a hole in its floor")
	player.global_position = campaign.room.position + Vector2((hole + 1.5) * TILE, 21.5 * TILE)
	player.linear_velocity = Vector2.ZERO
	await _frames(60)
	_expect(wins[0] == 1, "falling through the hole wins once, count %d" % wins[0])
	await _stop(campaign)


func _room_of_kind(kind: String) -> Dictionary:
	for data in _world.rooms:
		if data.kind == kind:
			return data
	_fail("no %s room" % kind)
	return {}


func _start(at: Vector2i) -> Node2D:
	var campaign: Node2D = load("res://scenes/campaign.tscn").instantiate()
	campaign.planet = PLANET
	campaign.progress = Planets.new_progress(PLANET)
	campaign.progress.checkpoint = at
	root.add_child(campaign)
	return campaign


func _stop(campaign: Node2D) -> void:
	_release_all()
	paused = false
	root.remove_child(campaign)
	campaign.free()
	await _frames(2)


func _clear_monsters(campaign: Node2D, keep: Node = null) -> void:
	for entity in campaign.room.get_node("Entities").get_children():
		if entity != keep and not entity.is_queued_for_deletion():
			entity.queue_free()


func _steer(player: RigidBody2D, target_x: float) -> void:
	var offset := target_x - player.global_position.x
	if offset > 4.0:
		Input.action_release("move_left")
		Input.action_press("move_right")
	elif offset < -4.0:
		Input.action_release("move_right")
		Input.action_press("move_left")
	else:
		Input.action_release("move_left")
		Input.action_release("move_right")


func _release_all() -> void:
	for action in ["move_left", "move_right", "jetpack"]:
		Input.action_release(action)


func _frames(count: int) -> void:
	for i in count:
		await physics_frame


func _expect(condition: bool, message: String) -> void:
	if not condition:
		_fail(message)


func _fail(message: String) -> void:
	_failures += 1
	printerr("FAIL: " + message)
