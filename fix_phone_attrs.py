with open("src/database/seed_data.py", "r") as f:
    text = f.read()

# Replace PHONE_ATTRS definition
import re
text = re.sub(
    r"PHONE_ATTRS = \[\s+_attr\(\"compatible_model\", \"text\", True, \"Compatible Model\"\),\s+\]",
    "PHONE_ATTRS = []",
    text
)

with open("src/database/seed_data.py", "w") as f:
    f.write(text)
