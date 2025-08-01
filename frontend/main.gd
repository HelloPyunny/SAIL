extends Node2D

@onready var map_root = $MapRoot
@onready var player = $Player 
#@onready var archer = $ArcherPlayer
@onready var npc = $Npc
@onready var open_button = $UI/OpenButton
@onready var dialogue_box = $UI/DialogueBox
@onready var http_request = $HTTPRequest

var current_player: CharacterBody2D = null
var game_api: GameAPI
var enemy_manager: EnemyManager
var current_map_background: Sprite2D = null  # Downloaded background map
var map_http_request: HTTPRequest = null  # For map image download
var pending_map_data: Dictionary = {}  # Map information being downloaded

func _ready():
	print("Main._ready() started")
	
	print("Initializing UI elements...")
	open_button.show()
	dialogue_box.hide()
	open_button.pressed.connect(_on_open_pressed)
	print("UI elements initialized successfully - dialogue_box: ", dialogue_box)
	
	print("Setting player...")
	current_player = player
	current_player.is_active_player = true
	#archer.is_active_player = false
	print("Palyer set")
	
	# Initialize GameAPI 
	print("Initializing GameAPI...")
	_initialize_game_api()
	
	# Initialize EnemyManager
	print("Initializing EnemyManager...")
	_initialize_enemy_manager()
	
	# Initialize HTTP request for map image download
	print("Initializing HTTP request...")
	_initialize_map_downloader()
	
	# Loading first stage (tutorial uses a fixed scene)
	print("Stage loading...")
	load_stage("res://stages/stage1_tutorial/Stage1.tscn")
	print("Tutorial stage loaded – using fixed map")

func _initialize_game_api():
	"""Initializing GameAPI and creating new game"""
	print("🔧 _initialize_game_api start")
	
	# Create GameAPI instance
	game_api = GameAPI.new()
	add_child(game_api)
	print("GameAPI instance created successfully")
	
	# Set GameAPI in dialogue box
	print("Reference to dialogue_box: ", dialogue_box)
	if dialogue_box:
		print("dialogue_box.set_game_api calling...")
		dialogue_box.set_game_api(game_api)
		print("dialogue_box.set_game_api called")
	else:
		print("❌ dialogue_box is null")
	
	# Connecting game start event
	game_api.game_started.connect(_on_game_started)
	game_api.stage_advanced.connect(_on_stage_advanced)
	game_api.error_occurred.connect(_on_game_api_error)
	print("GameAPI event connected")
	
	# Create new game
	print("new game creating...")
	game_api.create_new_game()

func _on_game_started(player_id: String, welcome_message: String):
	"""call when game start"""
	print("game started - Player ID: ", player_id)
	
	# display welcome message 
	if welcome_message != "":
		dialogue_box.add_message("NPC: " + welcome_message)

func _on_stage_advanced(result: Dictionary):
	"""call when stage is progressed"""
	var current_stage = result.get("current_stage", 1)
	var stage_intro_message = result.get("stage_intro_message", "")
	var game_completed = result.get("game_completed", false)
	
	print("Stage completed - Stage: ", current_stage, ", Completed: ", game_completed)
	
	# check the completiion of the game
	if game_completed:
		print("Game Completed!")
		dialogue_box.add_message("Congratulations! You have completed all stages.!")
		return
	
	# Loading scene by stage
	var stage_path = _get_stage_path(current_stage)
	if stage_path != "":
		load_stage(stage_path)
	
	# If a map recommendation exists, download the background image
	var map_recommendation = result.get("map_recommendation", {})
	if map_recommendation.has("image_path"):
		var image_url = map_recommendation["image_path"]
		print("map image dowloading... : ", image_url)
		_download_and_apply_map_background(image_url, map_recommendation)
	
	# Notify backend of enemy state reset (on new stage start)
	if game_api:
		game_api.reset_enemy_status()
	
	# Add stage introduction message to the dialogue box
	if stage_intro_message != "":
		dialogue_box.add_message("NPC: " + stage_intro_message)

func _get_stage_path(stage_number: int) -> String:
	match stage_number:
		1:
			# Tutorial uses fixed map
			return "res://stages/stage1_tutorial/Stage1.tscn"
		2:
			return "res://stages/stage2-7_dynamic/Stage2.tscn"
		3:
			return "res://stages/stage2-7_dynamic/Stage3.tscn"
		4:
			return "res://stages/stage2-7_dynamic/Stage4.tscn"
		5:
			return "res://stages/stage2-7_dynamic/Stage5.tscn"
		6:
			return "res://stages/stage2-7_dynamic/Stage6.tscn"
		7:
			return "res://stages/stage2-7_dynamic/Stage7.tscn"
		8:
			return "res://stages/stage8_final/Stage8.tscn"
		_:
			print("❌ Can't find Stage number: ", stage_number)
			return ""

func _on_game_api_error(message: String):
	"""Handle Game API error"""
	print("❌ Game API error: ", message)
	
func get_game_api() -> GameAPI:
	"""Method to retrieve the GameAPI instance from the DialogueBox"""
	return game_api

func _initialize_enemy_manager():
	"""Initialize EnemyManager"""
	enemy_manager = EnemyManager.new()
	add_child(enemy_manager)
	
	# Set enemy scene (using fire_enemy)
	enemy_manager.enemy_scene = preload("res://enemy/fire_enemy.tscn")
	enemy_manager.enemies_per_stage = 5
	
	# Connect signal for when all enemies are defeated
	enemy_manager.all_enemies_defeated.connect(_on_all_enemies_defeated)
	
	print("EnemyManager Initialize Complete")

func _on_all_enemies_defeated():
	"""call when all enemies defeated"""
	print("Main: all enemies defeated!")

func _initialize_map_downloader():
	"""Initialize HTTP request for map image download"""
	map_http_request = HTTPRequest.new()
	add_child(map_http_request)
	map_http_request.request_completed.connect(_on_map_image_downloaded)
	print("Map downloader initialized successfully")

func _download_and_apply_map_background(image_url: String, map_data: Dictionary):
	"""Download the map image and apply it as the background"""
	print("Downloading map image: ", image_url)
	
	# Store information of the map being downloaded
	pending_map_data = map_data
	pending_map_data["image_url"] = image_url
	
	# start HTTP request
	var error = map_http_request.request(image_url)
	if error != OK:
		print("Map image download request failed: ", error)
	else:
		print("Map image download request start...")

func _on_map_image_downloaded(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray):
	
	if result != HTTPRequest.RESULT_SUCCESS:
		print("❌ Map image download request failed: ", result)
		return
	
	if response_code != 200:
		print("❌ Map image HTTP error: ", response_code)
		return
	
	print("Map image download complete! size: ", body.size(), " bytes")
	
	# create image
	var image = Image.new()
	
	# Try PNG first
	var error = image.load_png_from_buffer(body)
	if error != OK:
		print("❌ Failed to load PNG (", error, "), trying JPG...")
		# Try JPG
		error = image.load_jpg_from_buffer(body)
		if error != OK:
			print("❌ Failed to load JPG (", error, "), trying WebP...")
			# Try WebP
			error = image.load_webp_from_buffer(body)
			if error != OK:
				print("❌ Failed to load all image formats - PNG:", error)
				return
			else:
				print("✅ Successfully loaded WebP image!")
		else:
			print("✅ Successfully loaded JPG image!")
	else:
		print("✅ Successfully loaded PNG image!")
	
	print("🔍 Image Info - Size: ", image.get_size(), ", Format: ", image.get_format())
	
	# Check if image is empty
	if image.get_size() == Vector2i.ZERO:
		print("❌ Image size is 0!")
		return
	
	# Create texture (Godot 4 method)
	var texture = ImageTexture.new()
	texture.set_image(image)  # In Godot 4, use set_image
	
	print("🔍 Texture Info - Size: ", texture.get_size())
	
	# Re-check texture size
	if texture.get_size() == Vector2.ZERO:
		print("❌ Texture creation failed, attempting fallback...")
		# Fallback method: ImageTexture.create_from_image (static method)
		texture = ImageTexture.create_from_image(image)
		print("Fallback Texture Info - Size: ", texture.get_size())
	
	# Apply background sprite
	_apply_map_background(texture)
	
	# Log map info
	var map_name = pending_map_data.get("name", "Unknown Map")
	var map_desc = pending_map_data.get("description", "")
	print("Map Applied: ", map_name)
	print("Map Description: ", map_desc)

func _apply_map_background(texture: ImageTexture):
	"""Apply the downloaded texture as background"""
	
	# Remove existing background
	if current_map_background:
		current_map_background.queue_free()
	
	# Create new background sprite
	current_map_background = Sprite2D.new()
	current_map_background.texture = texture
	current_map_background.z_index = -100  # Send to back
	
	# Center alignment
	current_map_background.position = Vector2(640, 360)  # Center of screen
	
	# Resize to fit the screen
	var screen_size = get_viewport().get_visible_rect().size
	var texture_size = texture.get_size()
	
	print("Screen Size: ", screen_size)
	print("Texture Size: ", texture_size)
	
	# Prevent divide by zero
	if texture_size.x <= 0 or texture_size.y <= 0:
		print("❌ Invalid texture size - failed to apply map")
		return
	
	var scale_factor = max(screen_size.x / texture_size.x, screen_size.y / texture_size.y)
	current_map_background.scale = Vector2(scale_factor, scale_factor)
	
	# Add to map root (place behind everything)
	map_root.add_child(current_map_background)
	map_root.move_child(current_map_background, 0)  # Move to first child (send to back)
	
	print("Background map applied - Screen size: ", screen_size, ", Texture size: ", texture_size, ", Scale: ", scale_factor)

# Removed old fixed map download function - now using real-time generated maps
	
func _on_open_pressed():
	dialogue_box.show()
	open_button.hide()

func show_open_button():  # Call from DialogueBox
	open_button.show()

func load_stage(path: String):
	print("Loading stage: ", path)
	
	# Initialize enemy manager (remove existing enemies)
	if enemy_manager:
		enemy_manager.reset()
	
	# Free original map
	for child in map_root.get_children():
		child.queue_free()

	# Load/add new map
	var scene = load(path)
	if scene == null:
		push_error("map loading failed: " + path)
		return

	var instance = scene.instantiate()
	map_root.add_child(instance)

	# Hide hardcoded TileMap for dynamic stages 2-7
	var current_stage = game_api.get_current_stage() if game_api else 1
	if current_stage >= 2 and current_stage <= 7:
		print("Dynamic stage detected - hiding hardcoded TileMap...")
		_hide_hardcoded_tilemaps(instance)

	# Connect to portal and deactivate it
	if instance.has_node("Portal"):
		var portal = instance.get_node("Portal")
		if portal.has_signal("portal_activated"):
			portal.connect("portal_activated", Callable(self, "_on_portal_triggered"))
		# Deactivate portal at start of new stage
		if portal.has_method("deactivate_portal"):
			portal.deactivate_portal()
			
	await get_tree().process_frame  # Wait for map to load
	
	# Set player position
	var start = instance.get_node_or_null("StartPosition")
	if start:
		player.global_position = start.global_position
	else:
		print("No StartPosition node found in map!")
		
	# Set NPC position
	var npc_start = instance.get_node_or_null("NpcStartPosition")
	if npc_start:
		npc.global_position = npc_start.global_position
	
	# Spawn enemies (set spawn position)
	if enemy_manager:
		var spawn_center = Vector2(400, 300)  # Default spawn position
		
		# If EnemySpawn node exists, use its position
		var enemy_spawn = instance.get_node_or_null("EnemySpawn")
		if enemy_spawn:
			spawn_center = enemy_spawn.global_position
		
		enemy_manager.spawn_enemies(spawn_center)
		print("enemy Spawned ", enemy_manager.enemies_per_stage, " enemies")
	
	print("✅ Stage loaded: ", path)

func _on_portal_triggered(next_path: String):
	print("Portal triggered! Advancing to next stage...")
	
	# Advance to next stage via backend API
	if game_api:
		game_api.advance_to_next_stage()
	else:
		print("❌ GameAPI is not initialized")
		# Fallback: load stage directly
		load_stage(next_path)

func swap_to(new_player: CharacterBody2D):
	if current_player:
		current_player.set_process_input(false)
		current_player.is_active_player = false

	new_player.set_process_input(true)
	new_player.is_active_player = true
	current_player = new_player
	print("✅ Swapped to:", new_player.name)

func _hide_hardcoded_tilemaps(stage_instance: Node):
	"""Hide hardcoded TileMap nodes in stage instance"""
	print("Searching for TileMap nodes...")
	
	# Iterate through all child nodes and find TileMaps
	var tilemaps_found = _search_and_hide_tilemaps(stage_instance, 0)
	
	print("✅ Total ", tilemaps_found, " TileMap nodes hidden")

func _search_and_hide_tilemaps(node: Node, found_count: int) -> int:
	"""Recursively find and hide TileMap nodes"""
	var count = found_count
	
	# Check if current node is TileMap
	if node is TileMap:
		print("Found TileMap: ", node.name, " - hiding...")
		node.visible = false
		count += 1
	
	# Recursively search all children
	for child in node.get_children():
		count = _search_and_hide_tilemaps(child, count)
	
	return count
