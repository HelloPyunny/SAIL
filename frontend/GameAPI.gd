extends Node

# Central manager responsible for all communication with the backend API
class_name GameAPI

const BASE_URL = "http://localhost:8000"

var http_request: HTTPRequest
var current_player_id: String = ""
var current_stage: int = 1
var game_completed: bool = false
var player_info: Dictionary = {}

signal game_started(player_id: String, welcome_message: String)
signal chat_response_received(npc_response: String, stage_progress: Dictionary, map_recommendation: Dictionary, game_completed: bool, current_stage: int, player_info: Dictionary)
signal stage_advanced(result: Dictionary)
signal error_occurred(message: String)

func _ready():
	http_request = HTTPRequest.new()
	add_child(http_request)
	http_request.request_completed.connect(_on_request_completed)

var pending_requests: Dictionary = {}

func create_new_game():
	"""creating new game"""
	var request_id = "new_game"
	pending_requests[request_id] = "new_game"
	
	var error = http_request.request(
		BASE_URL + "/game/new",
		[],
		HTTPClient.METHOD_POST
	)
	
	if error != OK:
		emit_signal("error_occurred", "Game creation request failed: " + str(error))

func send_chat_message(message: String):
	"""interact with NPC"""
	print("💬 send_chat_message called - message: '", message, "'")
	print("💬 current player_id: '", current_player_id, "'")
	
	if current_player_id == "":
		print("❌ Game not started")
		emit_signal("error_occurred", "Game not started")
		return
	
	var request_id = "chat"
	pending_requests[request_id] = "chat"
	print("💬 pending_requests 설정됨: ", pending_requests)
	
	var json_data = JSON.stringify({
		"player_id": current_player_id,
		"message": message
	})
	print("💬 JSON data to be sent: ", json_data)
	
	var headers = ["Content-Type: application/json"]
	var error = http_request.request(
		BASE_URL + "/game/chat",
		headers,
		HTTPClient.METHOD_POST,
		json_data
	)
	
	if error != OK:
		print("❌ HTTP request failed: ", error)
		emit_signal("error_occurred", "Conversation request failed: " + str(error))
	else:
		print("HTTP request sent successfully")

func advance_to_next_stage():
	"""advance to the next stage"""
	if current_player_id == "":
		emit_signal("error_occurred", "game has not started")
		return
	
	var request_id = "next_stage"
	pending_requests[request_id] = "next_stage"
	
	var error = http_request.request(
		BASE_URL + "/game/next-stage/" + current_player_id,
		[],
		HTTPClient.METHOD_POST
	)
	
	if error != OK:
		emit_signal("error_occurred", "Stage progression request failed: " + str(error))

func _on_request_completed(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray):
	"""HTTP request completed"""
	print("HTTP request completed - result: ", result, ", response_code: ", response_code)
	
	if result != HTTPRequest.RESULT_SUCCESS:
		print("❌ Network error: ", result)
		emit_signal("error_occurred", "Network error: " + str(result))
		return
	
	if response_code != 200:
		print("❌ Server error: HTTP ", response_code)
		emit_signal("error_occurred", "Server error: HTTP " + str(response_code))
		return
	
	var response_text = body.get_string_from_utf8()
	print("response text: ", response_text)
	
	var json = JSON.new()
	var parse_result = json.parse(response_text)
	
	if parse_result != OK:
		print("❌ JSON parsing error: ", parse_result)
		emit_signal("error_occurred", "Response parsing error")
		return
	
	var response_data = json.data
	print("Parsed response data: ", response_data)
	
	# Handling by Request Type
	if len(pending_requests) > 0:
		var request_type = pending_requests.values()[0]
		print("request type: ", request_type)
		pending_requests.clear()
		
		match request_type:
			"new_game":
				_handle_new_game_response(response_data)
			"chat":
				_handle_chat_response(response_data)
			"next_stage":
				_handle_next_stage_response(response_data)
			"enemy_defeated":
				_handle_enemy_defeated_response(response_data)
			"reset_enemy":
				_handle_reset_enemy_response(response_data)
	else:
		print("pending_requests is empty")

func _handle_new_game_response(data: Dictionary):
	"""Handling response for new game creation"""
	current_player_id = data.get("player_id", "")
	var welcome_message = data.get("welcome_message", "")
	
	print("New game created - Player ID: ", current_player_id)
	emit_signal("game_started", current_player_id, welcome_message)

func _handle_chat_response(data: Dictionary):
	"""handle chat response"""
	print("_handle_chat_response called")
	print("response data: ", data)
	
	var npc_response = data.get("npc_response", "")
	var stage_progress = data.get("stage_progress", {})
	var map_recommendation = data.get("map_recommendation", {})
	var game_completed = data.get("game_completed", false)
	var current_stage_num = data.get("current_stage", 1)
	var player_info_data = data.get("player_info", {})
	
	print("NPC response: '", npc_response, "'")
	print("Stage: ", current_stage_num)
	print("Game completed: ", game_completed)
	
	# Update game state
	current_stage = current_stage_num
	self.game_completed = game_completed
	player_info = player_info_data
	
	print("Received conversation response - Stage: ", current_stage, ", Completed: ", game_completed)
	print("Emitting chat_response_received signal ...")
	emit_signal("chat_response_received", npc_response, stage_progress, map_recommendation, game_completed, current_stage, player_info_data)
	print("chat_response_received siganl emit complete")

func _handle_next_stage_response(data: Dictionary):
	"""Handling response for stage progression"""
	if data.has("error"):
		emit_signal("error_occurred", data["error"])
		return
	
	var new_stage = data.get("current_stage", current_stage)
	var message = data.get("message", "Proceeding to the next stage!")
	var stage_progress = data.get("stage_progress", {})
	var map_recommendation = data.get("map_recommendation", {})
	var game_completed = data.get("game_completed", false)
	var player_info_data = data.get("player_info", {})
	
	# Update game state
	current_stage = new_stage
	self.game_completed = game_completed
	player_info = player_info_data
	
	print("Stage progressed - New Stage: ", current_stage, ", Completed: ", game_completed)
	emit_signal("stage_advanced", {
		"message": message,
		"stage_progress": stage_progress,
		"map_recommendation": map_recommendation,
		"game_completed": game_completed,
		"current_stage": current_stage,
		"player_info": player_info_data,
		"stage_intro_message": data.get("stage_intro_message", "")
	})

func get_current_stage() -> int:
	return current_stage

func get_player_info() -> Dictionary:
	return player_info

func is_game_completed() -> bool:
	return game_completed

func _handle_enemy_defeated_response(data: Dictionary):
	"""Handling response for enemy defeat"""
	var message = data.get("message", "")
	var stage_complete = data.get("stage_complete", false)
	var can_advance = data.get("can_advance", false)
	
	print("Enemy defeated - Stage Complete: ", stage_complete, ", Can Advance: ", can_advance)
	
	if stage_complete:
		print("Stage complete! Use the portal to proceed to the next stage!")

func _handle_reset_enemy_response(data: Dictionary):
	"""Handling response for enemy state reset"""
	var message = data.get("message", "")
	print("Enemy state reset complete: ", message)

func enemy_defeated():
	"""Called when an enemy is defeated"""
	if current_player_id == "":
		emit_signal("error_occurred", "Game has not been started")
		return
	
	var request_id = "enemy_defeated"
	pending_requests[request_id] = "enemy_defeated"
	
	var error = http_request.request(
		BASE_URL + "/game/enemy-defeated/" + current_player_id,
		[],
		HTTPClient.METHOD_POST
	)
	
	if error != OK:
		emit_signal("error_occurred", "Enemy defeat request failed: " + str(error))

func reset_enemy_status():
	"""reset_enemy_status when new stage starts"""
	if current_player_id == "":
		emit_signal("error_occurred", "Game has not been started")
		return
	
	var request_id = "reset_enemy"
	pending_requests[request_id] = "reset_enemy"
	
	var error = http_request.request(
		BASE_URL + "/game/reset-enemy-status/" + current_player_id,
		[],
		HTTPClient.METHOD_POST
	)
	
	if error != OK:
		emit_signal("error_occurred", "Enemy reset request failed: " + str(error))
