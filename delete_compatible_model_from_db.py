from src.database.supabase_client import get_client

client = get_client()

# Fetch the ProductType IDs for Phones
product_types_resp = client.table("product_types").select("id, name").in_("name", ["Used Phone", "Box Pack Phone", "Keypad Phone"]).execute()

for pt in product_types_resp.data:
    client.table("attribute_definitions").delete().eq("product_type_id", pt["id"]).eq("name", "compatible_model").execute()
    print(f"Deleted compatible_model from {pt['name']}")

print("Done")
