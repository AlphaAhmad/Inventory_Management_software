with open("src/services/inventory_service.py", "r") as f:
    text = f.read()

insert = """
    def create_subcategory(self, subcategory) -> 'Subcategory':
        return self.repo.create_subcategory(subcategory)

    def create_product_type(self, product_type) -> 'ProductType':
        return self.repo.create_product_type(product_type)

    def create_attribute_definition(self, attr) -> 'AttributeDefinition':
        return self.repo.create_attribute_definition(attr)
"""
text = text.replace("    def get_category_by_name(self, name: str) -> Category | None:", insert + "\n    def get_category_by_name(self, name: str) -> Category | None:")

with open("src/services/inventory_service.py", "w") as f:
    f.write(text)
