extends Node2D
## A port of the original's particle system: particles are plain records in
## an array, advanced and drawn here. Anything can add to it through the
## "particle_field" group:
##   get_tree().call_group("particle_field", "emit", "explosion", position, 40)

const BotSheet := preload("res://assets/animations/botParticles.png")
const JetSheet := preload("res://assets/animations/jetPackParticles.png")

const FRAME_TIME := 0.06
const FRAMES := 4
const SOURCE_SIZE := 16.0
const DRAW_SIZE := 32.0
## Particles start within this distance of the emit position on each axis.
const SPAWN_JITTER := 4.0


class Particle:
	var position: Vector2
	var velocity: Vector2
	var friction: float
	var life: float
	var age: float
	var sheet: Texture2D
	var row: int


## Velocity ranges are in px/s, life in seconds, friction in px/s².
var _kinds := {
	"explosion": {"sheet": BotSheet, "row": 0, "vx": [-100.0, 100.0], "vy": [-100.0, 100.0], "life": [0.8, 1.5], "friction": 0.0},
	"exhaust": {"sheet": BotSheet, "row": 0, "vx": [-10.0, 10.0], "vy": [50.0, 100.0], "life": [0.2, 0.3], "friction": 0.0},
	"jet_fire": {"sheet": JetSheet, "row": 0, "vx": [-100.0, 100.0], "vy": [50.0, 100.0], "life": [0.8, 1.5], "friction": 0.0},
	"jet_smoke": {"sheet": JetSheet, "row": 2, "vx": [-100.0, 100.0], "vy": [-100.0, 100.0], "life": [0.8, 1.5], "friction": 100.0},
	"energy": {"sheet": JetSheet, "row": 3, "vx": [-100.0, 100.0], "vy": [-100.0, 100.0], "life": [0.4, 0.6], "friction": 0.0},
}
var _particles: Array[Particle] = []


func _ready() -> void:
	add_to_group("particle_field")


## at is in this node's coordinates, which are world coordinates in the campaign.
## life_scale shortens or lengthens how long these particles last.
func emit(kind: String, at: Vector2, amount: int = 1, life_scale: float = 1.0) -> void:
	var spec: Dictionary = _kinds[kind]
	for i in amount:
		var particle := Particle.new()
		particle.position = at + Vector2(randf_range(-SPAWN_JITTER, SPAWN_JITTER), randf_range(-SPAWN_JITTER, SPAWN_JITTER))
		particle.velocity = Vector2(randf_range(spec.vx[0], spec.vx[1]), randf_range(spec.vy[0], spec.vy[1]))
		particle.friction = spec.friction
		particle.life = randf_range(spec.life[0], spec.life[1]) * life_scale
		particle.sheet = spec.sheet
		particle.row = spec.row
		_particles.append(particle)
	queue_redraw()


func count() -> int:
	return _particles.size()


func particle_velocity(index: int) -> Vector2:
	return _particles[index].velocity


func clear() -> void:
	_particles.clear()
	queue_redraw()


func advance(delta: float) -> void:
	for i in range(_particles.size() - 1, -1, -1):
		var particle := _particles[i]
		particle.age += delta
		if particle.age >= particle.life:
			_particles.remove_at(i)
			continue
		particle.velocity.x = move_toward(particle.velocity.x, 0.0, particle.friction * delta)
		particle.velocity.y = move_toward(particle.velocity.y, 0.0, particle.friction * delta)
		particle.position += particle.velocity * delta


func _process(delta: float) -> void:
	if _particles.is_empty():
		return
	advance(delta)
	queue_redraw()


func _draw() -> void:
	var half := Vector2(DRAW_SIZE, DRAW_SIZE) / 2.0
	for particle in _particles:
		var frame := int(particle.age / FRAME_TIME) % FRAMES
		var source := Rect2(frame * SOURCE_SIZE, particle.row * SOURCE_SIZE, SOURCE_SIZE, SOURCE_SIZE)
		draw_texture_rect_region(particle.sheet, Rect2(particle.position - half, half * 2.0), source)
