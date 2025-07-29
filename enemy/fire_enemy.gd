extends CharacterBody2D

@export var move_speed = 40
@export var attack_range := 100.0
@export var attack_cooldown := 2.0
var cooldown_timer := 0.0

@export var max_health := 50
var current_health := max_health

@export var fireball_scene: PackedScene 
@export var fire_interval := 2.0         # fire rate
@export var fire_speed := 200.0          # fire speed

@onready var fire_timer := $Timer
var player: CharacterBody2D = null

func _ready():
	fire_timer.wait_time = fire_interval
	fire_timer.start()
	player = get_tree().get_root().get_node("Main/Player")  # Adjust path to player
	fire_timer.timeout.connect(_on_fire_timer_timeout)
	
func _physics_process(delta):
	if player and is_instance_valid(player):
		var to_player = player.global_position - global_position
		var distance = to_player.length()

		# Move toward player if not in range
		if distance > attack_range:
			velocity = to_player.normalized() * move_speed
			move_and_slide()
		else:
			velocity = Vector2.ZERO
			move_and_slide()
			# Attack if cooldown is ready
			if cooldown_timer <= 0.0:
				fire_at_player()
				cooldown_timer = attack_cooldown

	# Cooldown countdown
	if cooldown_timer > 0.0:
		cooldown_timer -= delta

func fire_at_player():
	if fireball_scene and player:
		var projectile = fireball_scene.instantiate()
		get_tree().current_scene.add_child(projectile)

		projectile.global_position = global_position
		projectile.look_at(player.global_position)

		var direction = (player.global_position - global_position).normalized()
		if projectile.has_method("launch"):
			projectile.launch(direction)
		print("Fireball launched!")

func _on_fire_timer_timeout():
	if not player:
		return

	var fireball = fireball_scene.instantiate()
	fireball.global_position = global_position

	var direction = (player.global_position - global_position).normalized()
	fireball.velocity = direction * fire_speed

	get_tree().get_root().add_child(fireball)

func take_damage(amount):
	current_health -= amount
	print("Enemy hit! Current HP:", current_health)

	var label = $DamageLabel
	label.text = str(amount)
	label.visible = true
	label.modulate = Color(1, 0, 0)  # red
	label.global_position = global_position + Vector2(0, -20)

	var tween := create_tween()
	tween.tween_property(label, "position", label.position + Vector2(0, -30), 0.5)
	tween.tween_property(label, "modulate:a", 0.0, 0.5)
	tween.tween_callback(Callable(label, "hide"))

	if current_health <= 0:
		queue_free()
