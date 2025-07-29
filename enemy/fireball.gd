extends Area2D

var velocity := Vector2.ZERO
var shooter: Node = null
func _process(delta):
	position += velocity * delta

func _on_body_entered(body):
	if body == shooter:
		return
	if body.name == "Player":
		print("Player hit by fireball!")
		if body.has_method("take_damage"):
			body.take_damage(5)  
		queue_free()
