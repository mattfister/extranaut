extends RefCounted
## Jetpack fuel. A continuous version of the original's 100 ms impulse pulses,
## tuned so reach per tank matches (see tools/test_jetpack.gd).

const BURN_RATE := 3000.0
const REGEN_RATE := 1000.0
## After running dry the jetpack stays off until fuel recovers to this level.
const RESTART_FUEL := 500.0

var max_fuel := 2000.0
var fuel := 2000.0
var stalled := false


## Advances fuel by delta seconds. Returns true if the jetpack is thrusting.
func step(delta: float, wants_thrust: bool) -> bool:
	fuel = minf(fuel + REGEN_RATE * delta, max_fuel)
	if stalled and fuel >= RESTART_FUEL:
		stalled = false
	if not wants_thrust or stalled:
		return false
	fuel -= BURN_RATE * delta
	if fuel <= 0.0:
		fuel = 0.0
		stalled = true
	return true
