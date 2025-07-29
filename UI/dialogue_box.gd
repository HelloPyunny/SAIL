extends Control

@onready var scroll_container := $PanelContainer/VBoxContainer/ScrollContainer
@onready var messages := scroll_container.get_node("Messages")
@onready var input_box := $PanelContainer/VBoxContainer/HBoxContainerBot/InputBox
@onready var send_button := $PanelContainer/VBoxContainer/HBoxContainerBot/SendButton
@onready var close_button := $PanelContainer/VBoxContainer/HBoxContainerTop/CloseButton

var is_open := false

func _ready():
	hide()
	input_box.text_submitted.connect(_on_input_submitted)
	send_button.pressed.connect(_on_send_pressed)
	close_button.pressed.connect(_on_close_pressed)

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
	if text == "":
		return
	add_message("You: " + text)
	input_box.text = ""
	await get_tree().process_frame
	await get_tree().create_timer(0.2).timeout
	add_message("NPC: That's interesting!")  # 하드코딩 응답

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
