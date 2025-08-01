extends Control

@onready var scroll_container := $PanelContainer/VBoxContainer/ScrollContainer
@onready var messages := scroll_container.get_node("Messages")
@onready var input_box := $PanelContainer/VBoxContainer/HBoxContainerBot/InputBox
@onready var send_button := $PanelContainer/VBoxContainer/HBoxContainerBot/SendButton
@onready var close_button := $PanelContainer/VBoxContainer/HBoxContainerTop/CloseButton

var is_open := false
var game_api: GameAPI
var is_waiting_for_response := false
var response_timeout_timer: Timer
func _ready():
	hide()
	input_box.text_submitted.connect(_on_input_submitted)
	send_button.pressed.connect(_on_send_pressed)
	close_button.pressed.connect(_on_close_pressed)
	
	# Initialize timeout timer
	response_timeout_timer = Timer.new()
	response_timeout_timer.wait_time = 10.0  # 10-second timeout
	response_timeout_timer.one_shot = true
	response_timeout_timer.timeout.connect(_on_response_timeout)
	add_child(response_timeout_timer)
	print("Timeout timer initialized")
	
	# GameAPI will be set via set_game_api()
	# Backup mechanism: fetch manually if set_game_api is not called
	_setup_gameapi_backup()

func _unhandled_input(event):
	if event.is_action_pressed("ui_accept"):
		if not is_open:
			open_dialogue()
		else:
			_submit_text()

func open_dialogue():
	show()
	is_open = true
	input_box.grab_focus()

func close_dialogue():
	hide()
	is_open = false

func _on_send_pressed():
	_submit_text()

func _on_input_submitted(new_text):
	_submit_text()

func _submit_text():
	var text = input_box.text.strip_edges()
	if text == "" or is_waiting_for_response:
		return
	
	print("_submit_text called - message: '", text, "'")
	
	# Display player message
	add_message("You: " + text)
	input_box.text = ""
	
	# Set waiting state
	is_waiting_for_response = true
	send_button.disabled = true
	input_box.editable = false
	print("Chat state set to waiting")
	
	# Show NPC waiting message
	add_message("NPC: ...")
	
	# Set timeout (reset after 10 seconds)
	_set_response_timeout()
	
	# Send message to backend API
	if game_api:
		print("Sending message to GameAPI...")
		game_api.send_chat_message(text)
	else:
		print("GameAPI not connected")
		_on_api_error("Game API is not connected")

func add_message(text: String):
	var label = Label.new()
	label.text = text
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	messages.add_child(label)
	await get_tree().process_frame
	scroll_container.scroll_vertical = scroll_container.get_v_scroll_bar().max_value

func _on_close_pressed():
	hide()
	is_open = false
	get_tree().get_root().get_node("Main").show_open_button()

func _on_open_pressed():
	open_dialogue()

func _on_chat_response_received(npc_response: String, stage_progress: Dictionary, map_recommendation, game_completed: bool, current_stage: int, player_info: Dictionary):
	"""Handle NPC response received from backend"""
	print("_on_chat_response_received called!")
	print("NPC response: '", npc_response, "'")
	print("Current stage: ", current_stage)
	print("Game completed: ", game_completed)
	
	# Stop timeout timer
	if response_timeout_timer and response_timeout_timer.is_stopped() == false:
		response_timeout_timer.stop()
		print("Timeout timer stopped")
	
	# Exit waiting state
	is_waiting_for_response = false
	send_button.disabled = false
	input_box.editable = true
	print("Exited waiting state")
	
	# Remove last "..." message
	var children = messages.get_children()
	if children.size() > 0:
		var last_message = children[-1] as Label
		if last_message and last_message.text.ends_with("..."):
			print("Trying to remove '...': '", last_message.text, "'")
			messages.remove_child(last_message)
			last_message.free()
			print("Removed '...' message")

	# Show actual NPC response
	if npc_response != "":
		print("Adding NPC response message: ", npc_response)
		add_message("NPC: " + npc_response)
		print("NPC message added")
	else:
		print("NPC response is empty!")
	
	# If map recommendation exists, notify Main
	if map_recommendation != null and map_recommendation.has("image_path"):
		var main = get_tree().get_root().get_node("Main")
		if main and main.has_method("_download_and_apply_map_background"):
			print("Map recommendation received during chat: ", map_recommendation.get("name", ""))
			main._download_and_apply_map_background(map_recommendation["image_path"], map_recommendation)
	
	# Check for stage completion
	if stage_progress.get("stage_completed", false):
		add_message("Stage complete! Click the 'Next Stage' button.")
		_show_next_stage_button()
	
	# Check for game completion
	if game_completed:
		add_message("Congratulations! You completed all stages!")
		input_box.editable = false
		send_button.disabled = true

func _on_api_error(message: String):
	"""Handle API error"""
	
	# Exit waiting state
	is_waiting_for_response = false
	send_button.disabled = false
	input_box.editable = true
	
	# Remove last "..." message
	var children = messages.get_children()
	if children.size() > 0:
		var last_message = children[-1] as Label
		if last_message and last_message.text.ends_with("..."):
			messages.remove_child(last_message)
			last_message.free()
	
	# Show error message
	add_message("Error: " + message)
	print("API Error: ", message)

func _show_next_stage_button():
	"""Display next stage button (temporarily replaced with message)"""
	# TODO: Implement actual button UI
	add_message("To proceed to the next stage, close the chat and use the portal!")

func _setup_gameapi_backup():
	"""GameAPI fallback - manually fetch if set_game_api was not called"""
	print("Starting GameAPI fallback mechanism")
	
	# Wait a bit and try to get GameAPI
	await get_tree().create_timer(0.5).timeout
	
	if not game_api:
		print("GameAPI not set, trying manual fetch...")
		var main = get_tree().get_root().get_node("Main")
		if main and main.has_method("get_game_api"):
			var api = main.get_game_api()
			if api:
				print("Successfully fetched GameAPI via fallback")
				# Avoid duplicate connections in fallback
				game_api = api
				if game_api and not game_api.chat_response_received.is_connected(_on_chat_response_received):
					game_api.chat_response_received.connect(_on_chat_response_received)
					print("Fallback: chat_response_received signal connected")
				if game_api and not game_api.error_occurred.is_connected(_on_api_error):
					game_api.error_occurred.connect(_on_api_error)
					print("Fallback: error_occurred signal connected")
			else:
				print("❌ main.get_game_api() returned null")
		else:
			print("❌ Main node not found or get_game_api method missing")
	else:
		print("✅ GameAPI already set")

func set_game_api(api: GameAPI):
	"""Set the GameAPI instance"""
	print("🔗 set_game_api called")
	game_api = api
	if game_api:
		print("Connecting GameAPI signals...")
		# Prevent duplicate connections
		if not game_api.chat_response_received.is_connected(_on_chat_response_received):
			game_api.chat_response_received.connect(_on_chat_response_received)
			print("chat_response_received signal connected")
		else:
			print("chat_response_received already connected")
		
		if not game_api.error_occurred.is_connected(_on_api_error):
			game_api.error_occurred.connect(_on_api_error)
			print("error_occurred signal connected")
		else:
			print("error_occurred already connected")
		
		print("GameAPI signal connections completed!")
	else:
		print("GameAPI is null!")

func _set_response_timeout():
	"""Start response timeout"""
	if response_timeout_timer:
		response_timeout_timer.start()
		print("Response timeout started (10 seconds)")

func _on_response_timeout():
	"""Handle response timeout"""
	print("Response timeout occurred!")
	
	# Force exit from waiting state
	is_waiting_for_response = false
	send_button.disabled = false
	input_box.editable = true
	
	# Remove last "..." message
	var children = messages.get_children()
	if children.size() > 0:
		var last_message = children[-1] as Label
		if last_message and last_message.text.ends_with("..."):
			messages.remove_child(last_message)
			last_message.free()
	
	# Show timeout message
	add_message("❌ Response timeout - please try again.")
	print("Timeout recovery completed")
