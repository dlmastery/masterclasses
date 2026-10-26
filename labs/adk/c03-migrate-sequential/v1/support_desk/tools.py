"""Order lookup tool, the same in 1.x and 2.x (from the Chapter 1 refund lab)."""
from typing import Annotated

from pydantic import Field

ORDERS = {
    "A-1001": {"total_usd": 89.0, "days_since_delivery": 12, "category": "electronics"},
    "A-1002": {"total_usd": 1450.0, "days_since_delivery": 41, "category": "furniture"},
}


def lookup_order(order_id: Annotated[str, Field(description="Order ID, e.g. A-1001")]) -> dict:
    """Look up an order. Always call this before answering a refund question."""
    order = ORDERS.get(order_id.strip().upper())
    if order is None:
        return {"status": "error", "error_message": f"No order with ID {order_id}."}
    return {"status": "success", "order": order}
