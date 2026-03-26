from src.database.repository import Repository
from src.models.transaction import Transaction
from src.models.product import Product
from src.services.inventory_service import InventoryService


class TransactionService:
    def __init__(self):
        # Share the same Repository instance as InventoryService
        svc = InventoryService()
        self.repo = svc.repo

    def record_purchase(
        self,
        product_id: str,
        quantity: int,
        unit_price: float,
        customer_info: str = "",
        notes: str = "",
    ) -> Transaction:
        product = self.repo.get_product_by_id(product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")

        transaction = Transaction(
            product_id=product_id,
            type="purchase",
            quantity=quantity,
            unit_price=unit_price,
            total_price=quantity * unit_price,
            customer_info=customer_info,
            notes=notes,
        )
        created = self.repo.create_transaction(transaction)

        product.quantity += quantity
        if product.status == "sold":
            product.status = "in_stock"
        self.repo.update_product(product)

        return created

    def record_sale(
        self,
        product_id: str,
        quantity: int,
        unit_price: float,
        original_price: float = 0.0,
        customer_info: str = "",
        notes: str = "",
    ) -> Transaction:
        product = self.repo.get_product_by_id(product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")
        if product.quantity < quantity:
            raise ValueError(
                f"Not enough stock. Available: {product.quantity}, Requested: {quantity}"
            )

        transaction = Transaction(
            product_id=product_id,
            type="sale",
            quantity=quantity,
            unit_price=unit_price,
            total_price=quantity * unit_price,
            original_price=original_price,
            customer_info=customer_info,
            notes=notes,
        )
        created = self.repo.create_transaction(transaction)

        product.quantity -= quantity
        if product.quantity == 0:
            product.status = "sold"
        self.repo.update_product(product)

        return created

    def get_all_transactions(self) -> list[Transaction]:
        return self.repo.get_all_transactions()

    def get_recent_transactions(self, limit: int = 10) -> list[Transaction]:
        return self.repo.get_recent_transactions(limit)

    def get_product_name_map(self) -> dict[str, str]:
        return self.repo.get_product_name_map()

    def get_transactions_for_product(self, product_id: str) -> list[Transaction]:
        return self.repo.get_transactions(product_id=product_id)

    def get_purchases(self) -> list[Transaction]:
        return self.repo.get_transactions(trans_type="purchase")

    def get_sales(self) -> list[Transaction]:
        return self.repo.get_transactions(trans_type="sale")

    # ── Return / Claim / Resolve ─────────────────────

    def record_return(
        self,
        product_id: str,
        refund_amount: float,
        customer_info: str = "",
        return_reason: str = "",
    ) -> Transaction:
        product = self.repo.get_product_by_id(product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")
        if product.status != "sold":
            raise ValueError("Only sold products can be returned")

        last_sale = self.repo.get_last_sale_for_product(product_id)

        transaction = Transaction(
            product_id=product_id,
            type="return",
            quantity=1,
            unit_price=refund_amount,
            total_price=refund_amount,
            original_price=last_sale.unit_price if last_sale else 0,
            customer_info=customer_info,
            notes=return_reason,
            related_transaction_id=last_sale.id if last_sale else "",
        )
        created = self.repo.create_transaction(transaction)

        product.quantity += 1
        product.status = "in_stock"
        
        # Apply condition updates if not a phone (phones are handled below)
        phone_details = self.repo.get_phone_details(product_id)
        if not phone_details:
            if new_condition:
                product.attributes["condition"] = new_condition
            if new_phone_type == "used":
                # Maybe append used to title or attributes
                if product.attributes.get("condition") != new_condition:
                    product.attributes["condition"] = new_condition
                    
        self.repo.update_product(product)

        return created

    def record_claim(
        self,
        product_id: str,
        claim_reason: str,
        customer_info: str = "",
    ) -> Transaction:
        product = self.repo.get_product_by_id(product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")
        if product.status != "sold":
            raise ValueError("Only sold products can be claimed")

        last_sale = self.repo.get_last_sale_for_product(product_id)

        transaction = Transaction(
            product_id=product_id,
            type="claim",
            quantity=1,
            unit_price=0,
            total_price=0,
            customer_info=customer_info,
            notes=claim_reason,
            related_transaction_id=last_sale.id if last_sale else "",
        )
        created = self.repo.create_transaction(transaction)

        product.status = "claimed"
        self.repo.update_product(product)

        # Update phone_details if this is a phone
        phone_details = self.repo.get_phone_details(product_id)
        if phone_details:
            phone_details.is_claimed = True
            phone_details.claim_reason = claim_reason
            self.repo.update_phone_details(phone_details)

        return created

    def resolve_claim(
        self,
        product_id: str,
        accepted: bool,
        notes: str = "",
    ) -> Transaction:
        product = self.repo.get_product_by_id(product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")
        if product.status != "claimed":
            raise ValueError("Only claimed products can be resolved")

        claim_txn = self.repo.get_active_claim_for_product(product_id)
        resolution = "accepted" if accepted else "rejected"

        transaction = Transaction(
            product_id=product_id,
            type="claim_resolved",
            quantity=1,
            unit_price=0,
            total_price=0,
            notes=f"Claim {resolution}. {notes}".strip(),
            related_transaction_id=claim_txn.id if claim_txn else "",
        )
        created = self.repo.create_transaction(transaction)

        if accepted:
            product.quantity = 1
            product.status = "in_stock"
        else:
            product.status = "sold"
            product.quantity = 0
        self.repo.update_product(product)

        # Clear phone claim fields if applicable
        phone_details = self.repo.get_phone_details(product_id)
        if phone_details:
            phone_details.is_claimed = False
            phone_details.claim_reason = ""
            self.repo.update_phone_details(phone_details)

        return created

    def get_last_sale_for_product(self, product_id: str) -> Transaction | None:
        return self.repo.get_last_sale_for_product(product_id)
