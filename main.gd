extends Node2D

@onready var map_root = $MapRoot
@onready var player = $Player 
@onready var archer = $ArcherPlayer
@onready var npc = $Npc
@onready var open_button = $UI/OpenButton
@onready var dialogue_box = $UI/DialogueBox
@onready var http_request = $HTTPRequest
@export var map_url = "https://sail-blackhwack.s3.us-east-2.amazonaws.com/maps/dab0ecdb-cc5b-45da-a646-4b0cc3467257.png"

var current_player: CharacterBody2D = null

func _ready():
	open_button.show()
	dialogue_box.hide()
	open_button.pressed.connect(_on_open_pressed)
	
	current_player = player
	current_player.is_active_player = true
	archer.is_active_player = false
	
	load_stage("res://stages/stage1_tutorial/Stage1.tscn")
	http_request.request_completed.connect(_on_request_completed)
	var error = http_request.request(map_url)
	if error != OK:
		print("❌ Failed to start HTTP request")

func _on_request_completed(result, response_code, headers, body):
	if result != HTTPRequest.RESULT_SUCCESS:
		print(" HTTP Request failed:", result)
		return

	var img = Image.new()
	var err = img.load_png_from_buffer(body)
	if err != OK:
		print(" Failed to load image from buffer")
		return
		
	img.save_png("user://map.png")
	print("Saved to: ", ProjectSettings.globalize_path("user://map.png"))
	
func _on_open_pressed():
	dialogue_box.show()
	open_button.hide()

func show_open_button():  # Call from DialogueBox
	open_button.show()

func load_stage(path: String):
	# free original map
	for child in map_root.get_children():
		child.queue_free()

	# load/add new map
	var scene = load(path)
	if scene == null:
		push_error("map loading failed: " + path)
		return

	var instance = scene.instantiate()
	map_root.add_child(instance)

	# connect to portal
	if instance.has_node("Portal"):
		var portal = instance.get_node("Portal")
		if portal.has_signal("portal_activated"):
			portal.connect("portal_activated", Callable(self, "_on_portal_triggered"))
			
	await get_tree().process_frame  # wait for map to load
	var start = instance.get_node_or_null("StartPosition")
	if start:
		player.global_position = start.global_position
	else:
		print("No StartPosition node found in map!")
		
	var npc_start = instance.get_node_or_null("NpcStartPosition")
	if npc_start:
		npc.global_position = npc_start.global_position

func _on_portal_triggered(next_path: String):
	print("Portal triggered! Loading:", next_path)
	load_stage(next_path)

func swap_to(new_player: CharacterBody2D):
	if current_player:
		current_player.set_process_input(false)
		current_player.is_active_player = false

	new_player.set_process_input(true)
	new_player.is_active_player = true
	current_player = new_player
	print("✅ Swapped to:", new_player.name)
