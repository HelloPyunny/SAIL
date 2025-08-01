extends CharacterBody2D

@onready var label = $Label

func take_damage(amount):
	print("Dummy hit! Damage received:", amount)
	label.text = "-%s" % amount
	label.show()
	await get_tree().create_timer(1.0).timeout
	label.hide()
