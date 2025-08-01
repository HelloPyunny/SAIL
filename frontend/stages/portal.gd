extends Area2D

@export var next_stage_path: String = "res://stages/stage2-7_dynamic/Stage2.tscn"

signal portal_activated(path: String)

var is_active: bool = false
var game_api: GameAPI

func _ready():
	print(">> Portal ready!")
	connect("body_entered", Callable(self, "_on_body_entered"))
	
	# Connect to GameAPI
	await get_tree().process_frame
	var main = get_tree().get_root().get_node("Main")
	if main and main.has_method("get_game_api"):
		game_api = main.get_game_api()
		if game_api:
			game_api.chat_response_received.connect(_on_api_response)
	
	# Start with the portal deactivated
	deactivate_portal()

func _on_body_entered(body):
	print("Something entered Portal:", body.name)
	if body.name == "Player":
		if is_active:
			print("✅ Portal activated! Proceed to the next stage")
			emit_signal("portal_activated", next_stage_path)
		else:
			print("❌ Portal deactivated! Complete the stage first")
			_show_portal_message()

func activate_portal():
	"""Activate portal (upon stage completion)"""
	is_active = true
	print("Activate portal!")
	
	var sprite = $Portal
	if sprite is AnimatedSprite2D:
		sprite.modulate = Color.WHITE
		sprite.play("Portal")
	
	if has_node("ActivationEffect"):
		$ActivationEffect.visible = true

func deactivate_portal():
	"""Deactivate portal (at stage start)"""
	is_active = false
	print("Portal deactivated")
	
	var sprite = $Portal
	if sprite is AnimatedSprite2D:
		sprite.modulate = Color(0.5, 0.5, 0.5, 0.7)
		sprite.play("Portal")
	
	if has_node("ActivationEffect"):
		$ActivationEffect.visible = false

func _on_api_response(npc_response: String, stage_progress: Dictionary, map_recommendation, game_completed: bool, current_stage: int, player_info: Dictionary):
	"""Handle backend API response"""
	print("Portal received API response!")
	print("stage_progress: ", stage_progress)
	print("game_completed: ", game_completed)
	print("current_stage: ", current_stage)
	
	var stage_complete = stage_progress.get("stage_completed", false)
	print("stage_completed value: ", stage_complete)
	
	if stage_complete:
		print("Stage marked as completed by backend! Activating portal")
		activate_portal()
	else:
		print("Stage not yet completed - keeping portal deactivated")

func _show_portal_message():
	"""Display message when portal is locked"""
	print("Defeat all enemies and finish dialogue with the NPC!")
