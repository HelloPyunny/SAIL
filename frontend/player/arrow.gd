extends Area2D

@export var speed := 300
@export var damage := 15
var direction := Vector2.ZERO

func _ready():
	connect("body_entered", _on_body_entered)
	
func _physics_process(delta):
	if direction == Vector2.ZERO:
		queue_free()
		return

	position += direction * speed * delta
	
func _on_body_entered(body):
	if body.has_method("take_damage"):
		body.take_damage(damage)
	queue_free()
