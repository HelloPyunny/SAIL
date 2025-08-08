extends CharacterBody2D

@export var e_atk_cd := 4.0 #seconds
var can_shoot_arrow := true
@export var arrow_scene: PackedScene
@onready var arrow_spawn = $ArrowSpawn
@export var walk_speed := 60
@export var run_speed : float = 100.0

@onready var knight = get_node("/root/Main/Player")
@onready var interact_area = $InteractArea
@onready var animated_sprite = $AnimatedSprite2D
var is_active_player := false
var can_swap := false
var direction := Vector2.ZERO
var is_running := false
var is_attacking := false

func _ready():
	set_process_input(false)
	interact_area.body_entered.connect(_on_body_entered)
	interact_area.body_exited.connect(_on_body_exited)

func _input(event):
	if not is_active_player:
		return
	
	# 채팅창이 열려있으면 게임 입력 무시
	if _is_chat_open():
		return
	
	if event.is_action_pressed("interact") and can_swap:
		get_node("/root/Main").swap_to(knight)
	if event.is_action_pressed("e") and can_shoot_arrow:
		_play_attack("Archer_ATTACK")
		shoot_arrow()
	
func _physics_process(delta):
	if not is_active_player:
		return
	if is_attacking:
		velocity = Vector2.ZERO
		move_and_slide()
		return
	
	# 채팅창이 열려있으면 이동 불가
	if _is_chat_open():
		velocity = Vector2.ZERO
		move_and_slide()
		return

	direction = Vector2.ZERO
	is_running = Input.is_action_pressed("shift")

	if Input.is_action_pressed("ui_right"):
		direction.x += 1
	if Input.is_action_pressed("ui_left"):
		direction.x -= 1
	if Input.is_action_pressed("ui_down"):
		direction.y += 1
	if Input.is_action_pressed("ui_up"):
		direction.y -= 1

	direction = direction.normalized()
	var current_speed = run_speed if is_running else walk_speed
	velocity = direction * current_speed
	move_and_slide()

	_update_animation()

func _on_body_entered(body):
	if body.name == "Player":
		can_swap = true

func _on_body_exited(body):
	if body.name == "Player":
		can_swap = false
		
func _update_animation():
	if is_attacking:
		return

	if direction == Vector2.ZERO:
		animated_sprite.play("idle")
		return

	if is_running:
		animated_sprite.play("running")
	else:
		animated_sprite.play("walking")

	if direction.x > 0:
		animated_sprite.flip_h = false
	elif direction.x < 0:
		animated_sprite.flip_h = true
		
func _play_attack(anim_name: String):
	is_attacking = true
	direction = Vector2.ZERO
	velocity = Vector2.ZERO

	animated_sprite.play(anim_name)
	await animated_sprite.animation_finished

	is_attacking = false
	
func shoot_arrow():
	can_shoot_arrow = false
	if arrow_scene == null:
		print("Arrow scene not assigned!")
		return

	var arrow = arrow_scene.instantiate()
	#var dir = Vector2.RIGHT

	var offset = Vector2(10, 0)
	if $AnimatedSprite2D.flip_h:
		offset.x *= -1
		
	var dir = Vector2.RIGHT if not $AnimatedSprite2D.flip_h else Vector2.LEFT
	arrow.position = global_position + dir * 16  # offset so it doesn't spawn inside archer
	arrow.direction = dir.normalized()
	get_tree().current_scene.add_child(arrow)

	var sprite = arrow.get_node_or_null("Sprite2D")
	if sprite:
		sprite.flip_h = (dir == Vector2.LEFT)

	get_tree().current_scene.add_child(arrow)
	await get_tree().create_timer(e_atk_cd).timeout
	can_shoot_arrow = true
	print("Arrow shot! dir:", direction, " pos:", position)

func _is_chat_open() -> bool:
	"""채팅창이 열려있는지 확인"""
	var dialogue_box = get_node_or_null("/root/Main/UI/DialogueBox")
	if dialogue_box:
		# is_open 변수가 있으면 그 값을 사용, 없으면 visible 상태로 판단
		if "is_open" in dialogue_box:
			return dialogue_box.is_open
		else:
			return dialogue_box.visible
	return false
