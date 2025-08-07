extends CanvasLayer

@export var max_health: int = 100
var current_health: int

@onready var bar: TextureProgressBar = $Background/Fill
@onready var label: Label = $Background/HealthLabel
@onready var flash: ColorRect = $Background/Flash

func _ready():
	current_health = max_health
	bar.min_value = 0
	bar.max_value = max_health
	bar.value = current_health
	_update_label()
	flash.visible = false
	_update_fill_color()

func set_health(new_hp: int):
	print("bar is:", bar)  
	new_hp = clamp(new_hp, 0, max_health)
	var old = current_health
	current_health = new_hp

	# Smoothly tween the bar value over 0.4 seconds
	var tween = create_tween()
	tween.tween_property(bar, "value", current_health, 0.4).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)

	_update_label()
	_update_fill_color()

	if new_hp < old:
		_flash_damage()

func _update_label():
	label.text = "%d / %d" % [current_health, max_health]

func _flash_damage():
	flash.visible = true
	flash.modulate = Color(1, 0, 0, 0.5)
	var tween = create_tween()
	tween.tween_property(flash, "modulate:a", 0.0, 0.35).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tween.tween_callback(Callable(flash, "hide"))

func _update_fill_color():
	var ratio = float(current_health) / max_health
	var color: Color
	if ratio > 0.5:
		color = Color(1,1,0).lerp(Color(0,1,0), (ratio - 0.5) * 2.0)
	else:
		color = Color(1,0,0).lerp(Color(1,1,0), ratio * 2.0)

	# Grab the existing StyleBoxFlat used for the fill
	var style = bar.get_theme_stylebox("progress")
	if style and style is StyleBoxFlat:
		var new_style = style.duplicate() as StyleBoxFlat
		new_style.bg_color = color
		bar.add_theme_stylebox_override("progress", new_style)
