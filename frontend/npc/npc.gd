extends CharacterBody2D

@export var player: CharacterBody2D
@export var follow_distance: float = 40.0
@export var walk_speed: float = 60.0
@export var run_speed: float = 100.0

var animated_sprite: AnimatedSprite2D
var move_direction := Vector2.ZERO
var direction := Vector2.ZERO

func _ready():
	animated_sprite = $AnimatedSprite2D

func _physics_process(delta):
	if player == null:
		print("No player assigned!")
		return

	if not ("direction" in player and "velocity" in player):
		print("Missing player direction or velocity")
		return

	var player_dir = player.direction
	var player_pos = player.global_position
	var player_speed = player.velocity.length()

	# taget position for npc (behind the player)
	var target_position = player_pos - player_dir * follow_distance
	var to_target = target_position - global_position
	var distance = to_target.length()

	# set same speed (player = npc)
	var current_speed = 0.0
	var anim_name = ""

	if player_speed > 80:
		current_speed = run_speed
		anim_name = "Cat_RUN"
	elif player_speed > 5:
		current_speed = walk_speed
		anim_name = "Cat_WALK"
	else:
		current_speed = 0.0
		anim_name = "Cat_IDLE"

	if distance > 10.0 and current_speed > 0.0:
		move_direction = to_target.normalized()
		velocity = move_direction * current_speed
		move_and_slide()
	else:
		velocity = Vector2.ZERO
		move_and_slide()

	# play animation
	animated_sprite.play(anim_name)

	# direction flip
	if move_direction.x > 0:
		animated_sprite.flip_h = true
	elif move_direction.x < 0:
		animated_sprite.flip_h = false
