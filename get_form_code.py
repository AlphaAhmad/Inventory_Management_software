with open("src/ui/components/dynamic_form.py", "r") as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if "phone_shared_form" in line or "color_input" in line or "self.brand_input =" in line:
        print(f"{i}: {line.strip()}")
