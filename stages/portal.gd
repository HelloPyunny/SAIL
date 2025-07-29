extends Area2D

@export var next_stage_path: String = "res://stages/stage2-7_dynamic/Stage2.tscn"

signal portal_activated(path: String)

func _ready():
	print(">> Portal ready!")
	connect("body_entered", Callable(self, "_on_body_entered"))
	var sprite = $Portal
	if sprite is AnimatedSprite2D:
		print("animation playing")
		sprite.play("Portal")

func _on_body_entered(body):
	print("Something entered Portal:", body.name)
	if body.name == "Player":
		print("Player entered portal!")
		emit_signal("portal_activated", next_stage_path)
