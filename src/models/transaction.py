from dataclasses import dataclass


@dataclass
class Transaction:
    id: str = ""
    product_id: str = ""
    type: str = ""  # "purchase", "sale", "return", "claim", "claim_resolved"
    quantity: int = 0
    unit_price: float = 0.0
    total_price: float = 0.0
    original_price: float = 0.0
    customer_info: str = ""
    notes: str = ""
    related_transaction_id: str = ""
    created_at: str = ""

    def __post_init__(self):
        # Supabase returns None for null UUID columns
        if self.related_transaction_id is None:
            self.related_transaction_id = ""
