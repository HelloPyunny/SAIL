extends Node2D

class_name EnemyManager

signal all_enemies_defeated()

@export var enemy_scene: PackedScene
@export var enemies_per_stage: int = 5
@export var spawn_radius: float = 300.0

var enemies: Array[Node] = []
var enemies_defeated: int = 0
var stage_complete: bool = false
var game_api: GameAPI

func _ready():
	# GameAPI find instance
	await get_tree().process_frame
	var main = get_tree().get_root().get_node("Main")
	if main and main.has_method("get_game_api"):
		game_api = main.get_game_api()
	
	print("EnemyManager ready", enemies_per_stage, "spawning")

func spawn_enemies(spawn_center: Vector2):
	"""spawn"""
	print("spawning enemies - location: ", spawn_center)
	
	enemies.clear()
	enemies_defeated = 0
	stage_complete = false
	
	if not enemy_scene:
		print("enemy scence not setted correctly")
		return
	
	for i in range(enemies_per_stage):
		var enemy = enemy_scene.instantiate()
		add_child(enemy)
		
		# random spawn
		var angle = randf() * 4 * PI
		var distance = randf_range(50, spawn_radius)
		var spawn_pos = spawn_center + Vector2(cos(angle), sin(angle)) * distance
		
		enemy.global_position = spawn_pos
		enemies.append(enemy)
		
		# 적이 죽을 때 신호 연결
		if enemy.has_signal("enemy_died"):
			enemy.enemy_died.connect(_on_enemy_died)
		else:
			print("⚠️ no signal - enemy_died")
		
		print("enemy spawned - ", i+1, "/", enemies_per_stage, " location: ", spawn_pos)
	
	print("enemy spawned - count: ", enemies.size())

func _on_enemy_died():
	"""call when enemy defeated"""
	enemies_defeated += 1
	print("enemy defeated! ", enemies_defeated, "/", enemies_per_stage)
	
	# check if all enemy defeated
	if enemies_defeated >= enemies_per_stage:
		_all_enemies_defeated()

func _all_enemies_defeated():
	"""call when all enemy defeated"""
	if stage_complete:
		return
	
	stage_complete = true
	print("All enemy defeated!")
	
	# call backend API
	if game_api:
		game_api.enemy_defeated()
		print("Enemy defeated notification to backend")
	else:
		print("❌ can't find GameAPT")
	
	# Signal sent
	emit_signal("all_enemies_defeated")

func get_remaining_enemies() -> int:
	"""return left enemy count"""
	return enemies_per_stage - enemies_defeated

func is_stage_complete() -> bool:
	"""return stage complete"""
	return stage_complete

func reset():
	"""Enemy manager reset (on new stage start)"""
	for enemy in enemies:
		if is_instance_valid(enemy):
			enemy.queue_free()
	
	enemies.clear()
	enemies_defeated = 0
	stage_complete = false
	print("EnemyManager reset complete")
