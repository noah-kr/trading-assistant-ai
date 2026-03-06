"""Tool: Get and cancel pending orders."""

from langchain.tools import tool
from langchain_core.runnables import RunnableConfig

from logic.api.alpaca.alpaca_trade import get_broker
from db import get_alpaca_account_for_user


@tool("get_pending_orders", description="Fetches all pending/open orders for the user")
def get_pending_orders(config: RunnableConfig) -> list[dict]:
    """
    Returns all pending/open orders for the user.
    """
    account_id = get_alpaca_account_for_user(config["configurable"]["user_id"])[0]
    client = get_broker()

    try:
        orders = client.get_orders_for_account(account_id=account_id)
    except Exception as e:
        return [{"error": str(e)}]

    result = []
    for o in orders:
        status = str(o.status).lower() if o.status else ""
        if status in ("new", "pending_new", "accepted", "pending_cancel", "partially_filled"):
            result.append({
                "id": str(o.id),
                "symbol": o.symbol,
                "qty": float(o.qty) if o.qty else 0,
                "side": str(o.side).replace("OrderSide.", "").lower() if o.side else "",
                "status": status,
            })

    return result


@tool("cancel_all_orders_for_symbol", description="Cancels all pending orders for a specific symbol")
def cancel_all_orders_for_symbol(symbol: str, *, config: RunnableConfig) -> str:
    """
    Cancels all pending orders for a specific symbol.

    Args:
        symbol (str): The stock/ETF/crypto symbol to cancel orders for
    """
    account_id = get_alpaca_account_for_user(config["configurable"]["user_id"])[0]
    client = get_broker()
    symbol = symbol.upper()

    try:
        orders = client.get_orders_for_account(account_id=account_id)
        cancelled = 0

        for o in orders:
            if o.symbol == symbol:
                status = str(o.status).lower() if o.status else ""
                if status in ("new", "pending_new", "accepted", "pending_cancel", "partially_filled"):
                    try:
                        client.cancel_order_for_account_by_id(account_id=account_id, order_id=str(o.id))
                        cancelled += 1
                    except Exception:
                        pass

        if cancelled > 0:
            return f"{cancelled} open order(s) for {symbol} were cancelled."
        else:
            return f"No open orders found for {symbol}."

    except Exception as e:
        return f"Error: {str(e)}"
