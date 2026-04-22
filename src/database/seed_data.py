"""
Seed data script for Mobile Phone Shop Inventory Management System.

Populates Supabase tables in order:
  1. categories
  2. subcategories
  3. product_types
  4. attribute_definitions

Uses upsert with on_conflict so the script is idempotent and safe to run
multiple times.
"""

import os
import sys


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _upsert_row(client, table: str, data: dict, on_conflict: str) -> str:
    """Upsert a single row and return its ``id`` (UUID)."""
    result = (
        client.table(table)
        .upsert(data, on_conflict=on_conflict)
        .execute()
    )
    return result.data[0]["id"]


# ---------------------------------------------------------------------------
# 1. Categories
# ---------------------------------------------------------------------------

CATEGORIES = [
    {"name": "Phones", "display_order": 1},
    {"name": "Glass Protectors", "display_order": 2},
    {"name": "Branded Accessories", "display_order": 3},
    {"name": "Camera Lens", "display_order": 4},
    {"name": "Accessories", "display_order": 5},
    {"name": "Phone Cases", "display_order": 6},
    {"name": "Tablet Accessories", "display_order": 7},
]


def seed_categories(client) -> dict:
    """Seed categories and return {name: id} mapping."""
    mapping = {}
    for cat in CATEGORIES:
        cat_id = _upsert_row(client, "categories", cat, on_conflict="name")
        mapping[cat["name"]] = cat_id
    return mapping


# ---------------------------------------------------------------------------
# 2. Subcategories
# ---------------------------------------------------------------------------

# Keyed by parent category name
SUBCATEGORIES = {
    "Phones": [
        "Used Phones",
        "Box Pack Phones",
        "Keypad Phones",
    ],
    "Glass Protectors": [
        "iPhone Glass",
        "Android Glass",
    ],
    "Branded Accessories": [
        "Ronin",
        "Space",
        "Login",
        "Audionic",
        "Cherry",
        "Faster",
        "Orimo",
        "Taar",
    ],
    "Camera Lens": [
        "iPhone Lens",
        "Android Lens",
    ],
    "Accessories": [
        "General Accessories",
    ],
    "Phone Cases": [
        "TPU Bumper Case",
        "Original Branded Case",
        "Local Branded Case",
    ],
    "Tablet Accessories": [
        "iPad Accessories",
        "Samsung Tablet Accessories",
        "General Tablet Accessories",
    ],
}


def seed_subcategories(client, category_ids: dict) -> dict:
    """Seed subcategories and return {name: id} mapping."""
    mapping = {}
    for cat_name, subs in SUBCATEGORIES.items():
        cat_id = category_ids[cat_name]
        for idx, sub_name in enumerate(subs, start=1):
            row = {
                "name": sub_name,
                "category_id": cat_id,
                "display_order": idx,
            }
            sub_id = _upsert_row(
                client, "subcategories", row, on_conflict="category_id,name"
            )
            mapping[sub_name] = sub_id
    return mapping


# ---------------------------------------------------------------------------
# 3. Product Types
# ---------------------------------------------------------------------------

# Keyed by subcategory name
PRODUCT_TYPES = {
    # --- Phones ---
    "Used Phones": ["Used Phone"],
    "Box Pack Phones": ["Box Pack Phone"],
    "Keypad Phones": ["Keypad Phone"],

    # --- Glass Protectors ---
    "iPhone Glass": [
        "OG Glass",
        "Youksh Privacy Glass",
        "Youksh Clear Glass",
        "Flayer Glass",
        "Kuzoom Privacy Glass",
        "Kuzoom Clear Glass",
        "Coblu Privacy Glass",
        "Coblu Clear Glass",
        "Blue Shark Glass",
        "Soqoo Glass",
        "Borderless Glass",
        "Milake Privacy Glass",
    ],
    "Android Glass": [
        "OG Glass",
        "9D Glass",
    ],

    # --- Branded Accessories: Ronin ---
    "Ronin": [
        "Power Bank",
        "Ear Buds",
        "Neckband",
        "Charger",
        "20W Adapter",
        "Speaker",
        "Sound Bar",
        "2 in 1 Cable",
        "3 in 1 Cable",
        "Car Charger",
        "Gaming Handfree",
        "Wireless Headphone",
        "Cable",
        "Smart Watch",
    ],

    # --- Branded Accessories: Space ---
    "Space": [
        "Power Bank",
        "3 in 1 Wireless Power Bank",
        "Wireless Power Bank",
        "Neckband",
        "Charger",
        "Sound Bar",
        "Ear Buds",
        "3 Amp Charger",
        "Aux Cable",
        "USB Cable",
        "Handfree",
        "Car Charger",
        "3 in 1 Cable",
        "Headphone",
        "Smart Watch",
    ],

    # --- Branded Accessories: Login ---
    "Login": [
        "12W Charger",
        "20W Charger",
        "18W Charger",
        "Silica Gel Cable",
        "35W Type-C Cable",
        "22.5W Cable",
        "C to C Cable",
        "C to Lightning Cable",
        "Handfree",
        "Handfree iPhone",
        "Car Charger",
        "Speaker",
        "Headphone",
        "Gaming Headphone",
        "Sound Bar",
        "Power Bank",
        "65W Power Bank",
        "Wireless Power Bank",
        "Smart Watch",
    ],

    # --- Branded Accessories: Audionic ---
    "Audionic": [
        "Power Bank",
        "Ear Buds",
        "Handfree",
        "Car Charger",
        "Charging Cable",
        "Wireless Speaker",
    ],

    # --- Branded Accessories: Cherry ---
    "Cherry": [
        "Handfree",
        "Charging Cable",
    ],

    # --- Branded Accessories: Faster ---
    "Faster": [
        "Power Bank",
        "Wireless Power Bank",
        "Handfree",
        "Car Charger",
        "C-type Charger",
        "B-type Charger",
        "3 in 1 Cable",
        "2 in 1 Cable",
        "2 Meter Cable",
        "Jumbo Speaker",
        "Sound Bar",
        "Wireless Headphone",
        "Bike Mobile Charger",
        "C to C Cable",
        "Lightning to Lightning Cable",
    ],

    # --- Branded Accessories: Orimo ---
    "Orimo": [
        "Handfree",
        "Lightning Cable",
        "2 Meter Cable",
        "C to C Cable",
        "Speaker",
        "Neckband",
    ],

    # --- Branded Accessories: Taar ---
    "Taar": [
        "C to Lightning Cable",
        "USB Cable",
        "12W Charger",
        "18W Charger",
    ],

    # --- Camera Lens ---
    "iPhone Lens": ["Blue Shark iPhone Lens"],
    "Android Lens": ["Blue Shark Android Lens"],

    # --- Accessories ---
    "General Accessories": [
        "3 Pin Charging Adapter",
        "2 Pin Charging Adapter",
        "iPhone Copy Cable",
        "Samsung 45W Adapter",
        "Original IC Adapter",
        "Converter",
        "Type-C to Type-C Cable Local",
        "Type-C to Lightning Cable Local",
        "Wireless MagSafe Charger",
        "Wireless Power Bank",
        "Huawei Adapter",
        "Oppo Adapter",
        "Samsung Blue Port Adapter",
        "Stylus Pen",
        "Jelly Sheet",
        "Membrane Sheet",
        "Jionee Handfree",
        "Local Charging Cable",
        "Anchar Car Charger",
        "iPhone 13 Car Charger",
        "Local Car Charger",
        "FM Player Car Charger",
        "Extension",
        "AUX Handfree",
        "Charging Cable",
        "Cooling Fan",
        "Car Mobile Holder",
        "Headphone",
        "Keyboard",
        "Mouse",
        "Mouse Pad",
        "RGB Mouse Pad",
        "Speaker",
        "Sound Bar",
        "Wired Mike",
        "Boya Wireless Mike",
        "Sx8 Wireless Mike",
        "Selfie Stick",
        "Neepho Mobile Stand",
        "360 Degree Mobile Holder",
        "Selfie Stand Holder",
        "Local Mobile Stand",
        "Ring Light",
        "USB to Lightning Adapter",
        "HDMI Cable",
        "LAN Cable",
        "VGA Cable",
        "C-type to VGA Converter",
        "C-type to HDMI Converter",
        "VGA to HDMI Converter",
        "Display Port to VGA Converter",
        "USB Port Extender",
        "USB 3.0 Hub",
        "C-type USB Hub",
        "Printer Cable",
        "Swarovski Phone Cover",
        "Ladies Phone Cover",
        "Soft TPU Cover",
        "MagSafe TPU Cover",
        "Hard TPU Cover",
        "Color MagSafe Cover",
        "AirPods Cover",
        "Smart Watch Strap",
        "Phone Card Holder",
        "C-type Smart Watch Charger",
        "USB Smart Watch Charger",
        "Tablet",
    ],

    # --- Phone Cases ---
    "TPU Bumper Case": [
        "iPhone TPU Bumper",
        "Android TPU Bumper",
    ],
    "Original Branded Case": [
        "iPhone Original Case",
        "Android Original Case",
    ],
    "Local Branded Case": [
        "Local Branded Case",
        "Polo Logo Case",
    ],

    # --- Tablet Accessories ---
    "iPad Accessories": [
        "iPad Back Cover",
        "iPad Glass Protector",
    ],
    "Samsung Tablet Accessories": [
        "Samsung Tablet Cover",
        "Samsung Tablet Glass",
    ],
    "General Tablet Accessories": [
        "Universal Glass Protector",
        "Memory Card",
        "USB Drive",
        "Laptop Power Cable",
        "Computer Power Cable",
        "Laptop Cooling Pad",
    ],
}


def seed_product_types(client, subcategory_ids: dict) -> dict:
    """Seed product types and return {(subcategory_name, product_type_name): id}."""
    mapping = {}
    for sub_name, products in PRODUCT_TYPES.items():
        sub_id = subcategory_ids[sub_name]
        for idx, pt_name in enumerate(products, start=1):
            row = {
                "name": pt_name,
                "subcategory_id": sub_id,
                "display_order": idx,
            }
            pt_id = _upsert_row(
                client, "product_types", row, on_conflict="subcategory_id,name"
            )
            mapping[(sub_name, pt_name)] = pt_id
    return mapping


# ---------------------------------------------------------------------------
# 4. Attribute Definitions
# ---------------------------------------------------------------------------

def _attr(name, field_type, required, label, options=None, display_order=1):
    """Build an attribute definition dict (without product_type_id yet)."""
    d = {
        "name": name,
        "field_type": field_type,
        "is_required": required,
        "label": label,
        "display_order": display_order,
    }
    if options is not None:
        d["options"] = options
    return d


# ---- Reusable attribute sets ----

PHONE_ATTRS = []

GLASS_PROTECTOR_ATTRS = [
    _attr("compatible_models", "text", True, "Compatible Phone Models"),
]

GLASS_9D_ATTRS = [
    _attr("compatible_models", "text", True, "Compatible Phone Models"),
    _attr("glass_finish", "select", True, "Glass Finish",
          options=["Simple", "Polish"]),
]

POWER_BANK_ATTRS = [
    _attr("mah_capacity", "number", True, "Capacity (mAh)", display_order=1),
    _attr("wattage", "number", False, "Wattage (W)", display_order=2),
    _attr("connector_type", "select", True, "Connector Type",
          options=["USB", "Type-C", "Both"], display_order=3),
    _attr("is_wireless", "boolean", False, "Wireless", display_order=4),
    _attr("charging_type", "select", False, "Charging Type",
          options=["Simple", "PD", "Both"], display_order=5),
]

EAR_BUDS_NECKBAND_ATTRS = [
    _attr("color", "text", False, "Color"),
    _attr("connectivity", "select", True, "Connectivity",
          options=["Wireless", "Wired"]),
]

CHARGER_ATTRS = [
    _attr("wattage", "number", True, "Wattage (W)", display_order=1),
    _attr("connector_type", "select", True, "Connector Type",
          options=["C to C", "USB to C", "USB to Type-B",
                   "USB to Lightning", "C to Lightning"],
          display_order=2),
    _attr("cable_included", "boolean", False, "Cable Included",
          display_order=3),
]

SPEAKER_ATTRS = [
    _attr("wattage", "number", False, "Wattage (W)", display_order=1),
    _attr("is_wireless", "boolean", False, "Wireless", display_order=2),
    _attr("size", "select", False, "Size",
          options=["Small", "Medium", "Large", "Jumbo"], display_order=3),
]

CABLE_ATTRS = [
    _attr("cable_type", "select", True, "Cable Type",
          options=["C to C", "USB to C", "USB to Type-B",
                   "USB to Lightning", "C to Lightning",
                   "Lightning to Lightning", "2 in 1", "3 in 1", "AUX"],
          display_order=1),
    _attr("length", "select", False, "Length",
          options=["1m", "1.5m", "2m"], display_order=2),
    _attr("material", "select", False, "Material",
          options=["Simple", "Silica Gel", "Braided"], display_order=3),
]

CAR_CHARGER_ATTRS = [
    _attr("wattage", "number", False, "Wattage (W)", display_order=1),
    _attr("connector_type", "select", True, "Connector Type",
          options=["USB", "Type-C", "Type-B", "Both"], display_order=2),
    _attr("cable_included", "boolean", False, "Cable Included",
          display_order=3),
]

HANDFREE_ATTRS = [
    _attr("connector_type", "select", True, "Connector Type",
          options=["AUX", "Type-C", "Lightning", "Wireless"],
          display_order=1),
    _attr("variant", "text", False, "Variant", display_order=2),
]

HEADPHONE_ATTRS = [
    _attr("connectivity", "select", True, "Connectivity",
          options=["Wired", "Wireless"], display_order=1),
    _attr("connector_type", "select", False, "Connector Type",
          options=["AUX", "Type-C", "USB", "Bluetooth"], display_order=2),
]

SMART_WATCH_ATTRS = [
    _attr("color", "text", False, "Color", display_order=1),
    _attr("strap_type", "text", False, "Strap Type", display_order=2),
]

CAMERA_LENS_ATTRS = [
    _attr("compatible_models", "text", True, "Compatible Phone Models",
          display_order=1),
    _attr("lens_type", "text", False, "Lens Type", display_order=2),
]

ADAPTER_ATTRS = [
    _attr("wattage", "number", True, "Wattage (W)", display_order=1),
    _attr("pin_type", "select", False, "Pin Type",
          options=["2 Pin", "3 Pin"], display_order=2),
    _attr("compatible_brand", "select", True, "Compatible Brand",
          options=["Samsung", "iPhone", "Huawei", "Oppo", "Universal"],
          display_order=3),
]

CONVERTER_ATTRS = [
    _attr("from_type", "select", True, "From Type",
          options=["Type-C", "Lightning", "VGA", "Display Port", "USB"],
          display_order=1),
    _attr("to_type", "select", True, "To Type",
          options=["AUX", "VGA", "HDMI", "USB", "Type-C"], display_order=2),
]

COVER_CASE_ATTRS = [
    _attr("compatible_model", "text", True, "Compatible Model",
          display_order=1),
    _attr("color", "text", False, "Color", display_order=2),
    _attr("case_material", "select", False, "Material",
          options=["Soft TPU", "Hard TPU", "MagSafe TPU",
                   "Silicone", "Leather"],
          display_order=3),
]

SHEET_ATTRS = [
    _attr("compatible_model", "text", True, "Compatible Model",
          display_order=1),
    _attr("sheet_type", "select", True, "Sheet Type",
          options=["Jelly", "Membrane"], display_order=2),
]

MIKE_ATTRS = [
    _attr("mike_type", "select", False, "Mike Type",
          options=["Single", "Dual"], display_order=1),
    _attr("connectivity", "select", True, "Connectivity",
          options=["Wired", "Wireless"], display_order=2),
    _attr("connector_type", "select", False, "Connector Type",
          options=["AUX", "Type-C", "Lightning"], display_order=3),
]

STAND_HOLDER_ATTRS = [
    _attr("stand_type", "text", False, "Type", display_order=1),
    _attr("material", "select", False, "Material",
          options=["Aluminium", "Plastic", "Metal"], display_order=2),
    _attr("has_light", "boolean", False, "Has Light", display_order=3),
    _attr("has_bluetooth", "boolean", False, "Bluetooth Enabled",
          display_order=4),
]

RING_LIGHT_ATTRS = [
    _attr("light_type", "select", True, "Light Type",
          options=["RGB", "Simple"], display_order=1),
    _attr("size", "text", False, "Size", display_order=2),
]

INFRA_CABLE_ATTRS = [
    _attr("length", "select", True, "Length",
          options=["1m", "1.5m", "2m", "3m", "5m", "10m"], display_order=1),
    _attr("cable_category", "text", False, "Cable Category",
          display_order=2),
]

USB_HUB_ATTRS = [
    _attr("port_count", "number", False, "Number of Ports",
          display_order=1),
    _attr("hub_type", "select", True, "Hub Type",
          options=["USB 2.0", "USB 3.0", "Type-C"], display_order=2),
]

MEMORY_USB_ATTRS = [
    _attr("storage_gb", "select", True, "Storage (GB)",
          options=["4", "8", "16", "32", "64", "128", "256"],
          display_order=1),
    _attr("brand_type", "select", True, "Brand",
          options=["SanDisk", "Samsung Copy", "Other"], display_order=2),
]

STYLUS_PEN_ATTRS = [
    _attr("compatible_model", "text", False, "Compatible Model",
          display_order=1),
    _attr("pen_type", "text", False, "Type", display_order=2),
]

SMART_WATCH_STRAP_CHARGER_ATTRS = [
    _attr("compatible_model", "text", True, "Compatible Watch Model",
          display_order=1),
    _attr("strap_material", "text", False, "Material", display_order=2),
    _attr("is_branded", "boolean", False, "Branded", display_order=3),
]

PHONE_CARD_HOLDER_ATTRS = [
    _attr("color", "text", False, "Color", display_order=1),
    _attr("material", "text", False, "Material", display_order=2),
]

EXTENSION_ATTRS = [
    _attr("length", "text", False, "Length", display_order=1),
    _attr("port_count", "number", False, "Number of Ports",
          display_order=2),
]

COOLING_FAN_ATTRS = [
    _attr("fan_type", "text", False, "Type", display_order=1),
    _attr("connectivity", "select", False, "Connectivity",
          options=["USB", "Type-C", "Clip-on"], display_order=2),
]

KEYBOARD_MOUSE_ATTRS = [
    _attr("connectivity", "select", True, "Connectivity",
          options=["Wired", "Wireless"], display_order=1),
    _attr("brand", "text", False, "Brand", display_order=2),
    _attr("is_branded", "boolean", False, "Branded", display_order=3),
]

MOUSE_PAD_ATTRS = [
    _attr("size", "select", False, "Size",
          options=["Small", "Medium", "Large", "XL"], display_order=1),
    _attr("is_rgb", "boolean", False, "RGB", display_order=2),
    _attr("is_branded", "boolean", False, "Branded", display_order=3),
]

POWER_CABLE_ATTRS = [
    _attr("cable_type", "select", True, "Cable Type",
          options=["Laptop", "Computer"], display_order=1),
    _attr("length", "text", False, "Length", display_order=2),
]

LAPTOP_COOLING_PAD_ATTRS = [
    _attr("fan_count", "number", False, "Number of Fans", display_order=1),
    _attr("size", "text", False, "Size", display_order=2),
]

TABLET_ATTRS = [
    _attr("brand", "text", True, "Brand", display_order=1),
    _attr("model", "text", True, "Model", display_order=2),
    _attr("storage_gb", "number", False, "Storage (GB)", display_order=3),
    _attr("screen_size", "text", False, "Screen Size", display_order=4),
]

TABLET_COVER_ATTRS = [
    _attr("compatible_model", "text", True, "Compatible Model",
          display_order=1),
    _attr("cover_type", "select", True, "Cover Type",
          options=["Handle Cover", "Book Cover"], display_order=2),
    _attr("color", "text", False, "Color", display_order=3),
]

TABLET_GLASS_ATTRS = [
    _attr("compatible_model", "text", True, "Compatible Model",
          display_order=1),
    _attr("glass_size", "text", False, "Glass Size", display_order=2),
]

BIKE_MOBILE_CHARGER_ATTRS = [
    _attr("wattage", "number", False, "Wattage (W)", display_order=1),
    _attr("mount_type", "text", False, "Mount Type", display_order=2),
]

FM_PLAYER_CAR_CHARGER_ATTRS = [
    _attr("has_fm", "boolean", True, "FM Player", display_order=1),
    _attr("connector_type", "select", False, "Connector Type",
          options=["USB", "Type-C", "Type-B"], display_order=2),
]

LOCAL_BRANDED_CASE_ATTRS = [
    _attr("compatible_model", "text", True, "Compatible Model",
          display_order=1),
    _attr("color", "text", False, "Color", display_order=2),
    _attr("price_range", "select", False, "Price Range",
          options=["150-250 Rs", "250-500 Rs", "500+ Rs"], display_order=3),
]

ORIGINAL_CASE_ATTRS = [
    _attr("compatible_model", "text", True, "Compatible Model",
          display_order=1),
    _attr("color", "text", False, "Color", display_order=2),
]

WIRELESS_MAGSAFE_CHARGER_ATTRS = [
    _attr("wattage", "number", False, "Wattage (W)", display_order=1),
    _attr("compatible_model", "text", False, "Compatible Model",
          display_order=2),
]

LOCAL_CHARGING_CABLE_ATTRS = [
    _attr("cable_type", "select", True, "Cable Type",
          options=["USB to iPhone", "USB to Type-B", "USB to Type-C",
                   "C to C", "C to Lightning"],
          display_order=1),
    _attr("is_original", "boolean", False, "Original", display_order=2),
]


# ---------------------------------------------------------------------------
# Mapping: (subcategory_name, product_type_name) -> attribute list
# ---------------------------------------------------------------------------

def _build_attribute_map() -> dict:
    """
    Return a dict mapping (subcategory, product_type) to its list of
    attribute definition dicts.

    This is the single source of truth that ties every product type to
    the correct set of dynamic form fields.
    """
    m = {}

    # ---- Helper to assign the same attrs to many product types ----
    def _assign(sub, pt_name, attrs):
        m[(sub, pt_name)] = attrs

    # ----------------------------------------------------------------
    # Phones
    # ----------------------------------------------------------------
    for pt in ["Used Phone"]:
        _assign("Used Phones", pt, PHONE_ATTRS)
    for pt in ["Box Pack Phone"]:
        _assign("Box Pack Phones", pt, PHONE_ATTRS)
    for pt in ["Keypad Phone"]:
        _assign("Keypad Phones", pt, PHONE_ATTRS)

    # ----------------------------------------------------------------
    # Glass Protectors - iPhone Glass
    # ----------------------------------------------------------------
    iphone_glass_types = [
        "OG Glass", "Youksh Privacy Glass", "Youksh Clear Glass",
        "Flayer Glass", "Kuzoom Privacy Glass", "Kuzoom Clear Glass",
        "Coblu Privacy Glass", "Coblu Clear Glass", "Blue Shark Glass",
        "Soqoo Glass", "Borderless Glass", "Milake Privacy Glass",
    ]
    for pt in iphone_glass_types:
        _assign("iPhone Glass", pt, GLASS_PROTECTOR_ATTRS)

    # Glass Protectors - Android Glass
    _assign("Android Glass", "OG Glass", GLASS_PROTECTOR_ATTRS)
    _assign("Android Glass", "9D Glass", GLASS_9D_ATTRS)

    # ----------------------------------------------------------------
    # Branded Accessories: Ronin
    # ----------------------------------------------------------------
    _assign("Ronin", "Power Bank", POWER_BANK_ATTRS)
    _assign("Ronin", "Ear Buds", EAR_BUDS_NECKBAND_ATTRS)
    _assign("Ronin", "Neckband", EAR_BUDS_NECKBAND_ATTRS)
    _assign("Ronin", "Charger", CHARGER_ATTRS)
    _assign("Ronin", "20W Adapter", CHARGER_ATTRS)
    _assign("Ronin", "Speaker", SPEAKER_ATTRS)
    _assign("Ronin", "Sound Bar", SPEAKER_ATTRS)
    _assign("Ronin", "2 in 1 Cable", CABLE_ATTRS)
    _assign("Ronin", "3 in 1 Cable", CABLE_ATTRS)
    _assign("Ronin", "Car Charger", CAR_CHARGER_ATTRS)
    _assign("Ronin", "Gaming Handfree", HANDFREE_ATTRS)
    _assign("Ronin", "Wireless Headphone", HEADPHONE_ATTRS)
    _assign("Ronin", "Cable", CABLE_ATTRS)
    _assign("Ronin", "Smart Watch", SMART_WATCH_ATTRS)

    # ----------------------------------------------------------------
    # Branded Accessories: Space
    # ----------------------------------------------------------------
    _assign("Space", "Power Bank", POWER_BANK_ATTRS)
    _assign("Space", "3 in 1 Wireless Power Bank", POWER_BANK_ATTRS)
    _assign("Space", "Wireless Power Bank", POWER_BANK_ATTRS)
    _assign("Space", "Neckband", EAR_BUDS_NECKBAND_ATTRS)
    _assign("Space", "Charger", CHARGER_ATTRS)
    _assign("Space", "Sound Bar", SPEAKER_ATTRS)
    _assign("Space", "Ear Buds", EAR_BUDS_NECKBAND_ATTRS)
    _assign("Space", "3 Amp Charger", CHARGER_ATTRS)
    _assign("Space", "Aux Cable", CABLE_ATTRS)
    _assign("Space", "USB Cable", CABLE_ATTRS)
    _assign("Space", "Handfree", HANDFREE_ATTRS)
    _assign("Space", "Car Charger", CAR_CHARGER_ATTRS)
    _assign("Space", "3 in 1 Cable", CABLE_ATTRS)
    _assign("Space", "Headphone", HEADPHONE_ATTRS)
    _assign("Space", "Smart Watch", SMART_WATCH_ATTRS)

    # ----------------------------------------------------------------
    # Branded Accessories: Login
    # ----------------------------------------------------------------
    _assign("Login", "12W Charger", CHARGER_ATTRS)
    _assign("Login", "20W Charger", CHARGER_ATTRS)
    _assign("Login", "18W Charger", CHARGER_ATTRS)
    _assign("Login", "Silica Gel Cable", CABLE_ATTRS)
    _assign("Login", "35W Type-C Cable", CABLE_ATTRS)
    _assign("Login", "22.5W Cable", CABLE_ATTRS)
    _assign("Login", "C to C Cable", CABLE_ATTRS)
    _assign("Login", "C to Lightning Cable", CABLE_ATTRS)
    _assign("Login", "Handfree", HANDFREE_ATTRS)
    _assign("Login", "Handfree iPhone", HANDFREE_ATTRS)
    _assign("Login", "Car Charger", CAR_CHARGER_ATTRS)
    _assign("Login", "Speaker", SPEAKER_ATTRS)
    _assign("Login", "Headphone", HEADPHONE_ATTRS)
    _assign("Login", "Gaming Headphone", HEADPHONE_ATTRS)
    _assign("Login", "Sound Bar", SPEAKER_ATTRS)
    _assign("Login", "Power Bank", POWER_BANK_ATTRS)
    _assign("Login", "65W Power Bank", POWER_BANK_ATTRS)
    _assign("Login", "Wireless Power Bank", POWER_BANK_ATTRS)
    _assign("Login", "Smart Watch", SMART_WATCH_ATTRS)

    # ----------------------------------------------------------------
    # Branded Accessories: Audionic
    # ----------------------------------------------------------------
    _assign("Audionic", "Power Bank", POWER_BANK_ATTRS)
    _assign("Audionic", "Ear Buds", EAR_BUDS_NECKBAND_ATTRS)
    _assign("Audionic", "Handfree", HANDFREE_ATTRS)
    _assign("Audionic", "Car Charger", CAR_CHARGER_ATTRS)
    _assign("Audionic", "Charging Cable", CABLE_ATTRS)
    _assign("Audionic", "Wireless Speaker", SPEAKER_ATTRS)

    # ----------------------------------------------------------------
    # Branded Accessories: Cherry
    # ----------------------------------------------------------------
    _assign("Cherry", "Handfree", HANDFREE_ATTRS)
    _assign("Cherry", "Charging Cable", CABLE_ATTRS)

    # ----------------------------------------------------------------
    # Branded Accessories: Faster
    # ----------------------------------------------------------------
    _assign("Faster", "Power Bank", POWER_BANK_ATTRS)
    _assign("Faster", "Wireless Power Bank", POWER_BANK_ATTRS)
    _assign("Faster", "Handfree", HANDFREE_ATTRS)
    _assign("Faster", "Car Charger", CAR_CHARGER_ATTRS)
    _assign("Faster", "C-type Charger", CHARGER_ATTRS)
    _assign("Faster", "B-type Charger", CHARGER_ATTRS)
    _assign("Faster", "3 in 1 Cable", CABLE_ATTRS)
    _assign("Faster", "2 in 1 Cable", CABLE_ATTRS)
    _assign("Faster", "2 Meter Cable", CABLE_ATTRS)
    _assign("Faster", "Jumbo Speaker", SPEAKER_ATTRS)
    _assign("Faster", "Sound Bar", SPEAKER_ATTRS)
    _assign("Faster", "Wireless Headphone", HEADPHONE_ATTRS)
    _assign("Faster", "Bike Mobile Charger", BIKE_MOBILE_CHARGER_ATTRS)
    _assign("Faster", "C to C Cable", CABLE_ATTRS)
    _assign("Faster", "Lightning to Lightning Cable", CABLE_ATTRS)

    # ----------------------------------------------------------------
    # Branded Accessories: Orimo
    # ----------------------------------------------------------------
    _assign("Orimo", "Handfree", HANDFREE_ATTRS)
    _assign("Orimo", "Lightning Cable", CABLE_ATTRS)
    _assign("Orimo", "2 Meter Cable", CABLE_ATTRS)
    _assign("Orimo", "C to C Cable", CABLE_ATTRS)
    _assign("Orimo", "Speaker", SPEAKER_ATTRS)
    _assign("Orimo", "Neckband", EAR_BUDS_NECKBAND_ATTRS)

    # ----------------------------------------------------------------
    # Branded Accessories: Taar
    # ----------------------------------------------------------------
    _assign("Taar", "C to Lightning Cable", CABLE_ATTRS)
    _assign("Taar", "USB Cable", CABLE_ATTRS)
    _assign("Taar", "12W Charger", CHARGER_ATTRS)
    _assign("Taar", "18W Charger", CHARGER_ATTRS)

    # ----------------------------------------------------------------
    # Camera Lens
    # ----------------------------------------------------------------
    _assign("iPhone Lens", "Blue Shark iPhone Lens", CAMERA_LENS_ATTRS)
    _assign("Android Lens", "Blue Shark Android Lens", CAMERA_LENS_ATTRS)

    # ----------------------------------------------------------------
    # General Accessories
    # ----------------------------------------------------------------
    ga = "General Accessories"

    # Adapters
    _assign(ga, "3 Pin Charging Adapter", ADAPTER_ATTRS)
    _assign(ga, "2 Pin Charging Adapter", ADAPTER_ATTRS)
    _assign(ga, "Samsung 45W Adapter", ADAPTER_ATTRS)
    _assign(ga, "Original IC Adapter", ADAPTER_ATTRS)
    _assign(ga, "Huawei Adapter", ADAPTER_ATTRS)
    _assign(ga, "Oppo Adapter", ADAPTER_ATTRS)
    _assign(ga, "Samsung Blue Port Adapter", ADAPTER_ATTRS)
    _assign(ga, "USB to Lightning Adapter", ADAPTER_ATTRS)

    # Local cables
    _assign(ga, "iPhone Copy Cable", LOCAL_CHARGING_CABLE_ATTRS)
    _assign(ga, "Local Charging Cable", LOCAL_CHARGING_CABLE_ATTRS)

    # Converters
    _assign(ga, "Converter", CONVERTER_ATTRS)
    _assign(ga, "C-type to VGA Converter", CONVERTER_ATTRS)
    _assign(ga, "C-type to HDMI Converter", CONVERTER_ATTRS)
    _assign(ga, "VGA to HDMI Converter", CONVERTER_ATTRS)
    _assign(ga, "Display Port to VGA Converter", CONVERTER_ATTRS)

    # Local cables (Type-C variants)
    _assign(ga, "Type-C to Type-C Cable Local", CABLE_ATTRS)
    _assign(ga, "Type-C to Lightning Cable Local", CABLE_ATTRS)
    _assign(ga, "Charging Cable", CABLE_ATTRS)

    # Wireless MagSafe Charger
    _assign(ga, "Wireless MagSafe Charger", WIRELESS_MAGSAFE_CHARGER_ATTRS)

    # Wireless Power Bank
    _assign(ga, "Wireless Power Bank", POWER_BANK_ATTRS)

    # Stylus Pen
    _assign(ga, "Stylus Pen", STYLUS_PEN_ATTRS)

    # Sheets
    _assign(ga, "Jelly Sheet", SHEET_ATTRS)
    _assign(ga, "Membrane Sheet", SHEET_ATTRS)

    # Handfree
    _assign(ga, "Jionee Handfree", HANDFREE_ATTRS)
    _assign(ga, "AUX Handfree", HANDFREE_ATTRS)

    # Car chargers
    _assign(ga, "Anchar Car Charger", CAR_CHARGER_ATTRS)
    _assign(ga, "iPhone 13 Car Charger", CAR_CHARGER_ATTRS)
    _assign(ga, "Local Car Charger", CAR_CHARGER_ATTRS)
    _assign(ga, "FM Player Car Charger", FM_PLAYER_CAR_CHARGER_ATTRS)

    # Extension
    _assign(ga, "Extension", EXTENSION_ATTRS)

    # Cooling Fan
    _assign(ga, "Cooling Fan", COOLING_FAN_ATTRS)

    # Holders / Stands
    _assign(ga, "Car Mobile Holder", STAND_HOLDER_ATTRS)
    _assign(ga, "Selfie Stick", STAND_HOLDER_ATTRS)
    _assign(ga, "Neepho Mobile Stand", STAND_HOLDER_ATTRS)
    _assign(ga, "360 Degree Mobile Holder", STAND_HOLDER_ATTRS)
    _assign(ga, "Selfie Stand Holder", STAND_HOLDER_ATTRS)
    _assign(ga, "Local Mobile Stand", STAND_HOLDER_ATTRS)

    # Headphone
    _assign(ga, "Headphone", HEADPHONE_ATTRS)

    # Keyboard / Mouse
    _assign(ga, "Keyboard", KEYBOARD_MOUSE_ATTRS)
    _assign(ga, "Mouse", KEYBOARD_MOUSE_ATTRS)

    # Mouse Pads
    _assign(ga, "Mouse Pad", MOUSE_PAD_ATTRS)
    _assign(ga, "RGB Mouse Pad", MOUSE_PAD_ATTRS)

    # Speakers / Sound Bars
    _assign(ga, "Speaker", SPEAKER_ATTRS)
    _assign(ga, "Sound Bar", SPEAKER_ATTRS)

    # Mikes
    _assign(ga, "Wired Mike", MIKE_ATTRS)
    _assign(ga, "Boya Wireless Mike", MIKE_ATTRS)
    _assign(ga, "Sx8 Wireless Mike", MIKE_ATTRS)

    # Ring Light
    _assign(ga, "Ring Light", RING_LIGHT_ATTRS)

    # Infrastructure cables
    _assign(ga, "HDMI Cable", INFRA_CABLE_ATTRS)
    _assign(ga, "LAN Cable", INFRA_CABLE_ATTRS)
    _assign(ga, "VGA Cable", INFRA_CABLE_ATTRS)
    _assign(ga, "Printer Cable", INFRA_CABLE_ATTRS)

    # USB Hubs / Port Extenders
    _assign(ga, "USB Port Extender", USB_HUB_ATTRS)
    _assign(ga, "USB 3.0 Hub", USB_HUB_ATTRS)
    _assign(ga, "C-type USB Hub", USB_HUB_ATTRS)

    # Covers under General Accessories
    _assign(ga, "Swarovski Phone Cover", COVER_CASE_ATTRS)
    _assign(ga, "Ladies Phone Cover", COVER_CASE_ATTRS)
    _assign(ga, "Soft TPU Cover", COVER_CASE_ATTRS)
    _assign(ga, "MagSafe TPU Cover", COVER_CASE_ATTRS)
    _assign(ga, "Hard TPU Cover", COVER_CASE_ATTRS)
    _assign(ga, "Color MagSafe Cover", COVER_CASE_ATTRS)
    _assign(ga, "AirPods Cover", COVER_CASE_ATTRS)

    # Smart Watch Strap / Chargers
    _assign(ga, "Smart Watch Strap", SMART_WATCH_STRAP_CHARGER_ATTRS)
    _assign(ga, "C-type Smart Watch Charger", SMART_WATCH_STRAP_CHARGER_ATTRS)
    _assign(ga, "USB Smart Watch Charger", SMART_WATCH_STRAP_CHARGER_ATTRS)

    # Phone Card Holder
    _assign(ga, "Phone Card Holder", PHONE_CARD_HOLDER_ATTRS)

    # Tablet (under General Accessories)
    _assign(ga, "Tablet", TABLET_ATTRS)

    # ----------------------------------------------------------------
    # Phone Cases
    # ----------------------------------------------------------------
    # TPU Bumper Case
    _assign("TPU Bumper Case", "iPhone TPU Bumper", COVER_CASE_ATTRS)
    _assign("TPU Bumper Case", "Android TPU Bumper", COVER_CASE_ATTRS)

    # Original Branded Case
    _assign("Original Branded Case", "iPhone Original Case",
            ORIGINAL_CASE_ATTRS)
    _assign("Original Branded Case", "Android Original Case",
            ORIGINAL_CASE_ATTRS)

    # Local Branded Case
    _assign("Local Branded Case", "Local Branded Case",
            LOCAL_BRANDED_CASE_ATTRS)
    _assign("Local Branded Case", "Polo Logo Case", LOCAL_BRANDED_CASE_ATTRS)

    # ----------------------------------------------------------------
    # Tablet Accessories
    # ----------------------------------------------------------------
    # iPad Accessories
    _assign("iPad Accessories", "iPad Back Cover", TABLET_COVER_ATTRS)
    _assign("iPad Accessories", "iPad Glass Protector", TABLET_GLASS_ATTRS)

    # Samsung Tablet Accessories
    _assign("Samsung Tablet Accessories", "Samsung Tablet Cover",
            TABLET_COVER_ATTRS)
    _assign("Samsung Tablet Accessories", "Samsung Tablet Glass",
            TABLET_GLASS_ATTRS)

    # General Tablet Accessories
    _assign("General Tablet Accessories", "Universal Glass Protector",
            TABLET_GLASS_ATTRS)
    _assign("General Tablet Accessories", "Memory Card", MEMORY_USB_ATTRS)
    _assign("General Tablet Accessories", "USB Drive", MEMORY_USB_ATTRS)
    _assign("General Tablet Accessories", "Laptop Power Cable",
            POWER_CABLE_ATTRS)
    _assign("General Tablet Accessories", "Computer Power Cable",
            POWER_CABLE_ATTRS)
    _assign("General Tablet Accessories", "Laptop Cooling Pad",
            LAPTOP_COOLING_PAD_ATTRS)

    return m


# ---------------------------------------------------------------------------
# Seed attribute definitions
# ---------------------------------------------------------------------------

def seed_attribute_definitions(client, product_type_ids: dict):
    """Seed attribute_definitions for every product type."""
    attr_map = _build_attribute_map()
    count = 0

    for (sub_name, pt_name), attrs in attr_map.items():
        pt_id = product_type_ids.get((sub_name, pt_name))
        if pt_id is None:
            print(f"  WARNING: No product_type_id for ({sub_name!r}, "
                  f"{pt_name!r}) -- skipping attributes")
            continue

        for idx, attr in enumerate(attrs, start=1):
            row = {
                "product_type_id": pt_id,
                "name": attr["name"],
                "field_type": attr["field_type"],
                "is_required": attr["is_required"],
                "label": attr["label"],
                "display_order": attr.get("display_order", idx),
            }
            if "options" in attr:
                row["options"] = attr["options"]

            _upsert_row(
                client,
                "attribute_definitions",
                row,
                on_conflict="product_type_id,name",
            )
            count += 1

    return count


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def seed_all(client):
    """
    Populate all seed data tables in the correct order.

    Parameters
    ----------
    client : supabase.Client
        An authenticated Supabase client instance.
    """
    print("Seeding categories ...")
    category_ids = seed_categories(client)
    print(f"  -> {len(category_ids)} categories upserted.")

    print("Seeding subcategories ...")
    subcategory_ids = seed_subcategories(client, category_ids)
    print(f"  -> {len(subcategory_ids)} subcategories upserted.")

    print("Seeding product types ...")
    product_type_ids = seed_product_types(client, subcategory_ids)
    print(f"  -> {len(product_type_ids)} product types upserted.")

    print("Seeding attribute definitions ...")
    attr_count = seed_attribute_definitions(client, product_type_ids)
    print(f"  -> {attr_count} attribute definitions upserted.")

    print("Seeding complete.")


# ---------------------------------------------------------------------------
# Standalone runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from dotenv import load_dotenv
    from supabase import create_client

    # Load .env from the project root (two levels up from this file)
    env_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", ".env"
    )
    load_dotenv(dotenv_path=env_path)

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")

    if not url or not key:
        print("ERROR: SUPABASE_URL and SUPABASE_KEY must be set in .env")
        sys.exit(1)

    supabase_client = create_client(url, key)
    seed_all(supabase_client)
