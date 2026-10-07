extends SceneTree
## Checks that the continuous jetpack reaches the same height as the original
## pulsed one. Run: godot --headless --path . --script res://tools/test_jetpack.gd

const Jetpack := preload("res://entities/player/jetpack.gd")
const GRAVITY := 900.0
const THRUST_ACCEL := 1750.0
const DT := 1.0 / 60.0
const FRAMES := 900

var _failures := 0


func _init() -> void:
	for max_fuel in [2000.0, 2500.0, 3000.0, 3500.0, 4000.0, 4500.0, 5000.0]:
		var original := _original_apex(max_fuel)
		var ported := _ported_apex(max_fuel)
		var error := absf(ported - original) / original
		print("max fuel %d: original %d px, ported %d px, error %.1f%%" % [max_fuel, original, ported, error * 100.0])
		if error > 0.05:
			_failures += 1
			printerr("FAIL: apex differs by more than 5% at max fuel ", max_fuel)
	_check_stall_and_restart()
	print("jetpack test passed" if _failures == 0 else "jetpack test FAILED")
	quit(1 if _failures > 0 else 0)


## Port of the jetpack part of PlayerCharacter.update with up held, stepped at
## 60 fps with the integer millisecond frame times pygame reported.
func _original_apex(max_fuel: float) -> float:
	var frame_ms := [17, 17, 16]
	var fuel := max_fuel
	var pulse_timer := 0
	var regen_timer := 40
	var velocity := 0.0
	var height := 0.0
	var apex := 0.0
	for frame in FRAMES:
		velocity -= GRAVITY * DT
		height += velocity * DT
		apex = maxf(apex, height)
		var ms: int = frame_ms[frame % 3]
		if pulse_timer > 0:
			pulse_timer = maxi(pulse_timer - ms, 0)
		if fuel > 300.0 and pulse_timer <= 0:
			pulse_timer = 100
			velocity += 175.0
			fuel -= 300.0
		regen_timer -= ms
		if regen_timer <= 0:
			fuel = minf(fuel + 50.0, max_fuel)
			regen_timer = 40
	return apex


func _ported_apex(max_fuel: float) -> float:
	var jetpack := Jetpack.new()
	jetpack.max_fuel = max_fuel
	jetpack.fuel = max_fuel
	var velocity := 0.0
	var height := 0.0
	var apex := 0.0
	for frame in FRAMES:
		var thrusting := jetpack.step(DT, true)
		velocity += ((THRUST_ACCEL if thrusting else 0.0) - GRAVITY) * DT
		height += velocity * DT
		apex = maxf(apex, height)
	return apex


func _check_stall_and_restart() -> void:
	var jetpack := Jetpack.new()
	jetpack.fuel = 10.0
	_expect(jetpack.step(DT, true), "thrusts with a little fuel left")
	_expect(not jetpack.step(DT, true), "stalls once empty")
	_expect(jetpack.fuel >= 0.0, "fuel never goes negative")
	for i in 12:
		_expect(not jetpack.step(DT, true), "stays stalled below the restart level")
	for i in 20:
		jetpack.step(DT, false)
	_expect(jetpack.step(DT, true), "restarts after regenerating")
	jetpack.fuel = jetpack.max_fuel
	jetpack.step(1.0, false)
	_expect(jetpack.fuel == jetpack.max_fuel, "regeneration stops at max fuel")


func _expect(condition: bool, message: String) -> void:
	if not condition:
		_failures += 1
		printerr("FAIL: " + message)
