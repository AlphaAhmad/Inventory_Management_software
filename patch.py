import re

with open("src/ui/components/product_info_dialog.py", "r") as f:
    content = f.read()

# Make QTextEdit available
if "QTextEdit" not in content:
    content = content.replace("QPushButton, QHBoxLayout", "QPushButton, QHBoxLayout, QTextEdit")

# Update add_row logic to use QTextEdit for attributes with "compatible" in name or large text
content = content.replace(
'''        def add_row(key, val):
            if val is not None and val != "":
                lbl_val = QLabel(str(val))
                lbl_val.setWordWrap(True)
                lbl_val.setStyleSheet(f"color: {COLORS.get('text_primary', '#fff')};")
                form.addRow(f"{key}:", lbl_val)''',
'''        def add_row(key, val):
            if val is not None and val != "":
                if "compatible" in key.lower() or "\\n" in str(val):
                    text_edit = QTextEdit()
                    text_edit.setReadOnly(True)
                    text_edit.setPlainText(str(val))
                    text_edit.setFixedHeight(100)
                    text_edit.setStyleSheet(f"color: {COLORS.get('text_primary', '#fff')}; background: transparent; border: 1px solid #333;")
                    form.addRow(f"{key}:", text_edit)
                else:
                    lbl_val = QLabel(str(val))
                    lbl_val.setWordWrap(True)
                    lbl_val.setStyleSheet(f"color: {COLORS.get('text_primary', '#fff')};")
                    form.addRow(f"{key}:", lbl_val)'''
)

with open("src/ui/components/product_info_dialog.py", "w") as f:
    f.write(content)
print("patch successful")
