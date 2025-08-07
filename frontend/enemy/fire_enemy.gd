extends CharacterBody2D

signal enemy_died

@export var move_speed := 40.0

# instead of a single attack_range, expose a range:
@export var min_attack_range: float = 20.0
@export var max_attack_range: float = 300.0

var attack_range: float  

@export var fire_interval := 2.0
@export var fire_speed := 200.0
@export var max_health := 50
@export var fireball_scene: PackedScene

# how much randomness in movement so they don't stack
@export var jitter_strength := 0.3

var current_health := max_health
var player: CharacterBody2D = null
var rng := RandomNumberGenerator.new()

@onready var animated_sprite: AnimatedSprite2D = $AnimatedSprite2D

func _ready():
	# seed
	rng.randomize()

	# pick a per enemy attack range
	attack_range = rng.randf_range(min_attack_range, max_attack_range)
	print("%s attack_range set to %0.1f" % [name, attack_range])

	# small delay so player is in tree
	await get_tree().create_timer(0.05).timeout
	player = get_tree().get_root().get_node_or_null("Main/Player")
	if not player:
		push_error("FireEnemy: Player node not found!")

	# if starting out of range begin walking anim
	if global_position.distance_to(player.global_position) > attack_range:
		animated_sprite.play("fire_walking")

	_fire_loop()

func _physics_process(delta):
	if not (player and is_instance_valid(player)):
		return

	var to_player = player.global_position - global_position
	var dist = to_player.length()

	# flip to face player
	animated_sprite.flip_h = to_player.x < 0

	if dist > attack_range:
		# move + jitter
		var dir = to_player.normalized()
		var jitter = Vector2(
			rng.randf_range(-1, 1),
			rng.randf_range(-1, 1)
		).normalized() * jitter_strength
		velocity = (dir + jitter).normalized() * move_speed
		move_and_slide()

		# walking anim
		if animated_sprite.animation != "fire_walking":
			animated_sprite.play("fire_walking")
	else:
		velocity = Vector2.ZERO
		move_and_slide()

func _fire_loop() -> void:
	while true:
		await get_tree().create_timer(fire_interval).timeout
		if not (player and is_instance_valid(player)):
			continue
		var to_player = player.global_position - global_position
		if to_player.length() <= attack_range:
			# face then attack
			animated_sprite.flip_h = to_player.x < 0
			animated_sprite.play("fire_attack")
			_spawn_fireball(to_player.normalized())

func _spawn_fireball(dir: Vector2) -> void:
	if not fireball_scene:
		return
	var fb = fireball_scene.instantiate()
	fb.global_position = global_position + dir * 16
	fb.velocity = dir * fire_speed
	fb.shooter = self
	get_tree().current_scene.add_child(fb)
	
func take_damage(amount):
	current_health -= amount
	print("Enemy hit! Current HP:", current_health)
	# show damage label if exists
	if has_node("DamageLabel"):
		var label = $DamageLabel
		label.text = str(amount)
		label.visible = true
		label.modulate = Color(1, 0, 0) # red
		label.global_position = global_position + Vector2(0, -20)

		var tween := create_tween()
		tween.tween_property(label, "position", label.position + Vector2(0, -30), 0.5)
		tween.tween_property(label, "modulate:a", 0.0, 0.5)
		tween.tween_callback(Callable(label, "hide"))

	if current_health <= 0:
		emit_signal("enemy_died")
		queue_free()
