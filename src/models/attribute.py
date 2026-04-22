from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AttributeDefinition:
    id: str = ""
    product_type_id: str = ""
    name: str = ""
    label: str = ""
    field_type: str = "text"  # "text", "number", "boolean", "select"
    options: list = field(default_factory=list)  # For select fields
    is_required: bool = False
    display_order: int = 0
