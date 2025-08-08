extends Area2D

@export var damage := 5
@export var speed := 200.0
@export var max_lifetime := 5.0
const STUCK_CHECK_INTERVAL := 0.2  # how often to sample for stuck detection
const MIN_MOVE_DISTANCE := 1.0     # movement threshold to consider "moving"
const GRACE_PERIOD := 0.05         # initial grace before enabling collisions

var velocity: Vector2 = Vector2.ZERO
var shooter: Node = null

# internal timers
var time_alive := 0.0
var time_since_last_stuck_check := 0.0
var time_since_spawn := 0.0
var last_checked_position: Vector2

func _ready():
	last_checked_position = global_position

	# connect signal if not already
	if not is_connected("body_entered", Callable(self, "_on_body_entered")):
		connect("body_entered", Callable(self, "_on_body_entered"))

	# temporarily disable collision to avoid immediate overlap with shooter
	if $CollisionShape2D:
		$CollisionShape2D.disabled = true
		get_tree().create_timer(GRACE_PERIOD).timeout.connect(func():
			if is_instance_valid($CollisionShape2D):
				$CollisionShape2D.disabled = false)

func _physics_process(delta):
	time_alive += delta
	time_since_spawn += delta
	time_since_last_stuck_check += delta

	# no velocity = die
	if velocity == Vector2.ZERO:
		queue_free()
		return

	# move
	position += velocity * delta

	# stuck detection only after an initial period and at intervals
	if time_since_spawn > GRACE_PERIOD and time_since_last_stuck_check >= STUCK_CHECK_INTERVAL:
		var moved = global_position.distance_to(last_checked_position)
		if moved < MIN_MOVE_DISTANCE:
			# considered stuck
			queue_free()
			return
		last_checked_position = global_position
		time_since_last_stuck_check = 0.0

	# lifetime cap
	if time_alive >= max_lifetime:
		queue_free()

func _on_body_entered(body):
	# 1) Don’t hurt the shooter
	if body == shooter:
		return
	# 2) If they can take damage, apply it
	if body.has_method("take_damage"):
		body.take_damage(damage)
	# 3) Either way, the fireball disappears
	queue_free()
