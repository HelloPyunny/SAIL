extends CharacterBody2D

@export var walk_speed : float = 60.0
@export var run_speed : float = 100.0

@onready var health_panel: CanvasLayer = get_node_or_null("/root/Main/HealthPanel")
@onready var archer = get_node("/root/Main/ArcherPlayer") 

var direction := Vector2.ZERO
var is_running := false
var is_attacking := false
var is_active_player := false
var can_swap := false
var animated_sprite: AnimatedSprite2D

@export var max_health := 100
var current_health := max_health
var respawn_position := Vector2.ZERO

# attack damage
@export var q_atk_dmg = 10
@export var w_atk_dmg = 15
@export var e_atk_dmg = 20

var attack_base_offsets: Dictionary = {}

func _ready():
	animated_sprite = $Player_animation
	respawn_position = global_position
	health_panel = get_node_or_null("/root/Main/HealthPanel")
	if health_panel:
		health_panel.set_health(current_health)
	else:
		print("health_panel not found; UI won't update.")
		#swap interaction area
	$InteractArea.body_entered.connect(_on_body_entered)
	$InteractArea.body_exited.connect(_on_body_exited)
	
	# cache base attack area offsets
	for key in ["Q", "W", "E"]:
		var node = get_node_or_null("Attack_" + key)
		if node:
			attack_base_offsets[key] = node.position
		#else:
			#print("Missing attack area at startup: Attack_%s" % key)

func _input(event):
	if is_attacking:
		return
	if not is_active_player:
		return
	
	# Ignore game input if the chat window is open
	if _is_chat_open():
		return
	
	if event.is_action_pressed("interact") and can_swap:
		get_node("/root/Main").swap_to(archer)
	if event is InputEventKey and event.pressed:
		match event.keycode:
			KEY_Q:
				_play_attack("Knight_ATTACK1")
				perform_attack("Q")
			KEY_W:
				_play_attack("Knight_ATTACK2")
				perform_attack("W")
			KEY_E:
				_play_attack("Knight_ATTACK3")
				perform_attack("E")

		
	# Chat box
	if event.is_action_pressed("ui_accept"):  # Enter
		print("Enter key pressed")
		var dialogue_box = get_node("/root/Main/UI/DialogueBox")
		if dialogue_box:
			print("open_dialogue")
			dialogue_box.open_dialogue()
		else:
			print("DialogueBox not found")


func _physics_process(delta):
	if not is_active_player:
		return
	if is_attacking:
		velocity = Vector2.ZERO
		move_and_slide()
		return
	
	# Movement disabled while the chat window is open
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

func _update_animation():
	if is_attacking:
		return

	if direction == Vector2.ZERO:
		animated_sprite.play("Knight_IDLE")
		return

	if is_running:
		animated_sprite.play("Knight_RUN")
	else:
		animated_sprite.play("Knight_WALK")

	if direction.x > 0:
		animated_sprite.flip_h = false
		_flip_attack_hitboxes(false)
	elif direction.x < 0:
		animated_sprite.flip_h = true
		_flip_attack_hitboxes(true)
	

func perform_attack(key: String):
	var attack_area = get_node_or_null("Attack_" + key)
	if not attack_area:
		print("ERROR: Attack_%s not found" % key)
		return

	var dmg := 0

	match key:
		"Q":
			dmg = q_atk_dmg
		"W":
			dmg = w_atk_dmg
		"E":
			dmg = e_atk_dmg
		_:
			dmg = 0


	#print("Attack ", key , " triggered with ", dmg, " damage")

	var bodies = attack_area.get_overlapping_bodies()
	#print("Found %d bodies in Attack_%s" % [bodies.size(), key])

	for body in bodies:
		#print("Hit body:", body.name)
		if body == self:
			continue
		if body.has_method("take_damage"):
			body.take_damage(dmg)

func _play_attack(anim_name: String):
	is_attacking = true
	direction = Vector2.ZERO
	velocity = Vector2.ZERO

	animated_sprite.play(anim_name)
	await animated_sprite.animation_finished

	is_attacking = false

func take_damage(amount: int):
	current_health -= amount
	current_health = clamp(current_health, 0, max_health)
	#print("Player took ", amount, " damage. HP now: ", current_health)

	# update health UI
	if health_panel:
		health_panel.set_health(current_health)

	if current_health <= 0:
		respawn()


func respawn():
	print("Player has died. Respawning...")
	global_position = respawn_position
	current_health = max_health
	if health_panel:
		health_panel.set_health(current_health)

func _on_body_entered(body):
	if body.name == "ArcherPlayer":
		can_swap = true

func _on_body_exited(body):
	if body.name == "ArcherPlayer":
		can_swap = false
		
func _flip_attack_hitboxes(facing_left: bool):
	for key in ["Q", "W", "E"]:
		var attack_area = get_node_or_null("Attack_" + key)
		if attack_area:
			var original_pos = attack_area.position
			attack_area.position.x = abs(original_pos.x) * (-1 if facing_left else 1)
		else:
			print("Missing attack area: Attack_", key)

func _is_chat_open() -> bool:
	"""check if dialogue_box is opened"""
	var dialogue_box = get_node_or_null("/root/Main/UI/DialogueBox")
	if dialogue_box:
		# if is_open use the value, if not == visible
		if "is_open" in dialogue_box:
			return dialogue_box.is_open
		else:
			return dialogue_box.visible
	return false
