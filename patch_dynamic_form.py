import re

with open("src/ui/components/dynamic_form.py", "r") as f:
    content = f.read()

# 1. Update _create_field_widget
content = content.replace(
'''    def _create_field_widget(self, attr_def: AttributeDefinition) -> QWidget:
        if attr_def.field_type == "text":
            return QLineEdit()''',
'''    def _create_field_widget(self, attr_def: AttributeDefinition) -> QWidget:
        if attr_def.field_type == "text":
            if attr_def.name in ["compatible_model", "compatible_models"]:
                text_edit = QTextEdit()
                text_edit.setFixedHeight(80) # Made it slightly taller for lists
                text_edit.setPlaceholderText("Enter compatible models separated by commas, or one per line")
                return text_edit
            return QLineEdit()'''
)

# 2. Update _populate_edit_data loop
content = content.replace(
'''            if isinstance(widget, QLineEdit):
                widget.setText(str(value))''',
'''            if isinstance(widget, QTextEdit):
                widget.setPlainText(str(value))
            elif isinstance(widget, QLineEdit):
                widget.setText(str(value))'''
)

# 3. Update _on_save loop
content = content.replace(
'''            if isinstance(widget, QLineEdit):
                attributes[attr_name] = widget.text().strip()''',
'''            if isinstance(widget, QTextEdit):
                attributes[attr_name] = widget.toPlainText().strip()
            elif isinstance(widget, QLineEdit):
                attributes[attr_name] = widget.text().strip()'''
)

with open("src/ui/components/dynamic_form.py", "w") as f:
    f.write(content)
print("done")
