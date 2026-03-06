"""
Alpaca Trade Logic - Handles order placement and management.
"""

import os
from uuid import UUID
from pydantic import BaseModel

from alpaca.broker.client import BrokerClient
from alpaca.broker.requests import OrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType

from db import get_alpaca_account_for_user


def get_broker() -> BrokerClient:
    return BrokerClient(
        api_key=os.getenv("APCA_BROKER_KEY_ID"),
        secret_key=os.getenv("APCA_BROKER_SECRET_KEY"),
        sandbox=True,
    )


class PlaceOrderBody(BaseModel):
    account_id: str  # UUID as string for SQLite compatibility
    username: str
    symbol: str
    qty: float
    side: str  # "buy" or "sell"
    time_in_force: str | None = "day"
    order_type: str | None = "market"


def place_order_internal(body: PlaceOrderBody) -> dict:
    """
    Places a simple order for the user's sub-account.
    Returns a dict with the result.
    """
    client = get_broker()

    side_str = body.side.lower()
    if side_str not in ("buy", "sell"):
        return {"error": "side must be 'buy' or 'sell'"}

    side = OrderSide.BUY if side_str == "buy" else OrderSide.SELL

    tif_str = (body.time_in_force or "day").upper()
    try:
        tif = TimeInForce[tif_str]
    except KeyError:
        return {"error": f"invalid time_in_force: {body.time_in_force}"}

    order_type_str = (body.order_type or "market").upper()
    if order_type_str not in ("MARKET", "LIMIT"):
        return {"error": "only 'market' or 'limit' are supported"}

    order_type = OrderType[order_type_str]

    account_id = UUID(body.account_id) if isinstance(body.account_id, str) else body.account_id

    order_req = OrderRequest(
        account_id=account_id,
        username=body.username,
        symbol=body.symbol,
        qty=body.qty,
        side=side,
        type=order_type,
        time_in_force=tif,
    )

    try:
        order = client.submit_order_for_account(account_id, order_req)
    except Exception as e:
        error_str = str(e)

        if "wash trade" in error_str.lower():
            try:
                open_orders = client.get_orders_for_account(account_id=account_id)
                cancelled_count = 0
                for open_order in open_orders:
                    if open_order.symbol == body.symbol:
                        try:
                            client.cancel_order_for_account_by_id(account_id=account_id, order_id=open_order.id)
                            cancelled_count += 1
                        except Exception:
                            pass

                if cancelled_count > 0:
                    try:
                        order = client.submit_order_for_account(account_id, order_req)
                        return {
                            "status": "OK",
                            "order_id": str(order.id),
                            "symbol": order.symbol,
                            "qty": str(order.qty),
                            "side": str(order.side),
                            "type": str(order.type),
                            "time_in_force": str(order.time_in_force),
                            "status_alpaca": str(order.status),
                            "note": f"{cancelled_count} conflicting order(s) were cancelled",
                        }
                    except Exception as retry_error:
                        return {"error": f"Wash Trade: {cancelled_count} cancelled, but retry failed: {str(retry_error)}"}
                else:
                    return {"error": f"Wash Trade for {body.symbol}: Opposite order already open."}
            except Exception as cancel_error:
                return {"error": f"Wash Trade for {body.symbol}: cancel error: {str(cancel_error)}"}

        return {"error": error_str}

    return {
        "status": "OK",
        "order_id": str(order.id),
        "symbol": order.symbol,
        "qty": str(order.qty),
        "side": str(order.side),
        "type": str(order.type),
        "time_in_force": str(order.time_in_force),
        "status_alpaca": str(order.status),
    }


def get_open_orders_for_user(user_id: int) -> dict:
    """Returns all pending orders for a user."""
    account_id = get_alpaca_account_for_user(user_id)[0]
    client = get_broker()

    try:
        orders = client.get_orders_for_account(account_id=UUID(account_id))
    except Exception as e:
        return {"error": str(e)}

    result = []
    final_statuses = ("filled", "canceled", "cancelled", "expired", "rejected", "replaced", "done_for_day")

    for o in orders:
        raw_status = str(o.status).lower() if o.status else ""
        status = raw_status.replace("orderstatus.", "")

        if status not in final_statuses:
            result.append({
                "id": str(o.id),
                "symbol": o.symbol,
                "qty": float(o.qty) if o.qty else 0,
                "filled_qty": float(o.filled_qty) if o.filled_qty else 0,
                "side": str(o.side).replace("OrderSide.", "").lower() if o.side else "",
                "type": str(o.type).replace("OrderType.", "").lower() if o.type else "",
                "status": status,
                "created_at": o.created_at.isoformat() if o.created_at else None,
            })

    return {"status": "OK", "orders_count": len(result), "orders": result}


def cancel_order_for_user(user_id: int, order_id: str) -> dict:
    """Cancel a specific order for a user."""
    account_id = get_alpaca_account_for_user(user_id)[0]
    client = get_broker()

    try:
        client.cancel_order_for_account_by_id(account_id=UUID(account_id), order_id=order_id)
        return {"status": "OK", "message": f"Order {order_id} was cancelled"}
    except Exception as e:
        return {"error": f"Cancellation failed: {str(e)}"}
