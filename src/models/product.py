from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class Product:
    id: str = ""
    product_type_id: str = ""
    name: str = ""
    brand: str = ""
    model: str = ""
    purchase_price: float = 0.0
    sale_price: float = 0.0
    quantity: int = 0
    status: str = "in_stock"  # "in_stock", "sold", "claimed"
    attributes: dict = field(default_factory=dict)
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""


@dataclass
class PhoneDetails:
    id: str = ""
    product_id: str = ""
    imei1: str = ""
    imei2: str = ""
    phone_type: str = ""  # "used", "box_pack", "keypad"
    has_box: bool = False
    has_charger: bool = False
    keypad_type: str = ""  # "keys_only", "keypad_touchscreen"
    is_claimed: bool = False
    claim_reason: str = ""
    condition: str = ""  # "excellent", "good", "fair", "poor"
    storage_gb: int = 0
    ram_gb: int = 0
    color: str = ""
    region_variant: str = ""
