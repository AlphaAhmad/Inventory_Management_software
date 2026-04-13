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

    def get_all_transactions(
        self,
        trans_type: str | None = None,
        limit: int | None = 500,
    ) -> list[Transaction]:
        return self.repo.get_all_transactions(trans_type=trans_type, limit=limit)

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
        new_phone_type: str = None,
        new_condition: str = None,
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
        # Update cost basis to the refund amount (shop's effective re-acquisition cost)
        product.purchase_price = refund_amount

        # Apply condition updates
        phone_details = self.repo.get_phone_details(product_id)
        if phone_details:
            if new_phone_type:
                phone_details.phone_type = new_phone_type
            if new_condition:
                phone_details.condition = new_condition
            self.repo.update_phone_details(phone_details)
        else:
            if new_condition:
                if "attributes" not in product.__dict__ or product.attributes is None:
                    product.attributes = {}
                product.attributes["condition"] = new_condition
            if new_phone_type == "used":
                if "attributes" not in product.__dict__ or product.attributes is None:
                    product.attributes = {}
                product.attributes["phone_type"] = "used"
                
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

    # ── Revert ───────────────────────────────────────

    def revert_transaction(self, transaction_id: str) -> dict:
        """Undo a transaction as if it never happened.
        Only the MOST RECENT transaction for a product can be reverted so
        we don't break the state chain. Returns a dict describing what was
        undone (for the confirmation message)."""
        txn = self.repo.get_transaction_by_id(transaction_id)
        if not txn:
            raise ValueError("Transaction not found.")

        product = self.repo.get_product_by_id(txn.product_id)
        if not product:
            raise ValueError(
                "The product this transaction belongs to no longer exists "
                "in inventory. The transaction cannot be reverted."
            )

        # Guard: only the latest transaction for this product may be reverted.
        latest = self.repo.get_latest_transaction_for_product(txn.product_id)
        if latest and latest.id != txn.id:
            raise ValueError(
                "Only the most recent transaction for a product can be reverted. "
                "Revert newer transactions on this product first."
            )

        phone_details = self.repo.get_phone_details(txn.product_id)
        summary = {"type": txn.type, "product_id": txn.product_id}

        if txn.type == "sale":
            # Undo: put stock back, revert sold status if fully sold
            product.quantity += txn.quantity
            if product.status == "sold":
                product.status = "in_stock"
            self.repo.update_product(product)

        elif txn.type == "purchase":
            # Undo: take stock back out
            new_qty = product.quantity - txn.quantity
            if new_qty < 0:
                raise ValueError(
                    f"Cannot revert purchase: current stock ({product.quantity}) "
                    f"is less than the purchased quantity ({txn.quantity})."
                )
            product.quantity = new_qty
            if product.quantity == 0 and product.status == "in_stock":
                product.status = "sold"
            self.repo.update_product(product)

        elif txn.type == "return":
            # Undo: take the unit back out, restore sold status
            if product.quantity < 1:
                raise ValueError("Cannot revert return: product has no stock to remove.")
            product.quantity -= 1
            if product.quantity == 0:
                product.status = "sold"
            # Best-effort: reset purchase_price to the value prior to the return.
            # On return we had set purchase_price = refund_amount; there's no
            # historical record of the previous value, so we leave it alone and
            # surface a note in the summary.
            summary["purchase_price_note"] = (
                "Note: Product's purchase_price was overwritten when the return "
                "was recorded. The revert cannot restore the previous cost basis. "
                "Edit the product manually if you need to correct it."
            )
            self.repo.update_product(product)

        elif txn.type == "claim":
            # Undo: back to sold, clear claim fields
            product.status = "sold"
            self.repo.update_product(product)
            if phone_details and phone_details.is_claimed:
                phone_details.is_claimed = False
                phone_details.claim_reason = ""
                self.repo.update_phone_details(phone_details)

        elif txn.type == "claim_resolved":
            # Undo: back to claimed state. Infer accepted/rejected from the
            # notes we wrote ("Claim accepted." / "Claim rejected.").
            was_accepted = txn.notes.lower().startswith("claim accepted")
            if was_accepted:
                # We had set qty=1 / status=in_stock; undo that.
                if product.quantity > 0:
                    product.quantity -= 1
            # Status goes back to claimed regardless of previous outcome
            product.status = "claimed"
            self.repo.update_product(product)
            # Restore the claim flag; recover the original reason from the
            # linked claim transaction if available.
            if phone_details is not None:
                phone_details.is_claimed = True
                if txn.related_transaction_id:
                    claim_txn = self.repo.get_transaction_by_id(txn.related_transaction_id)
                    if claim_txn and claim_txn.notes:
                        phone_details.claim_reason = claim_txn.notes
                self.repo.update_phone_details(phone_details)
        else:
            raise ValueError(f"Unknown transaction type: {txn.type}")

        # Remove the transaction record itself
        self.repo.delete_transaction(txn.id)
        summary["deleted"] = True
        return summary
