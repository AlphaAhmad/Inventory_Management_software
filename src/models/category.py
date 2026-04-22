from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Category:
    id: str = ""
    name: str = ""
    display_order: int = 0


@dataclass
class Subcategory:
    id: str = ""
    category_id: str = ""
    name: str = ""
    display_order: int = 0


@dataclass
class ProductType:
    id: str = ""
    subcategory_id: str = ""
    name: str = ""
    display_order: int = 0
