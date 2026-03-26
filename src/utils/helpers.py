def format_price(price: float) -> str:
    if price == int(price):
        return f"Rs. {int(price):,}"
    return f"Rs. {price:,.2f}"


def format_quantity(qty: int) -> str:
    if qty == 0:
        return "Out of stock"
    return str(qty)
