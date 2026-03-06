"""Tool: Sell Stock via Alpaca Broker API."""

from langchain.tools import tool
from langchain_core.runnables import RunnableConfig

from logic.api.alpaca.alpaca_trade import place_order_internal, PlaceOrderBody
from db import get_alpaca_account_for_user, get_username


@tool("sell_stock", return_direct=True)
def sell_stock(symbol: str, qty: float, *, config: RunnableConfig) -> str:
    """
    Places a SELL order for a stock.

    Args:
        symbol (str): Stock ticker, e.g., "AAPL"
        qty (float): Quantity
    """
    try:
        user_id = config["configurable"]["user_id"]
        account_id = get_alpaca_account_for_user(user_id)[0]
        username = get_username(user_id)

        payload = PlaceOrderBody(
            account_id=account_id,
            username=username,
            symbol=symbol.upper(),
            qty=qty,
            side="sell",
            time_in_force="day",
            order_type="market",
        )

        result = place_order_internal(payload)

        if isinstance(result, dict) and result.get("status") == "OK":
            order_status = str(result.get("status_alpaca", "")).lower()
            note = result.get("note", "")
            order_id = result.get("order_id")

            if order_status in ("filled", "orderstatus.filled"):
                return f"Successfully sold {qty} shares of {symbol.upper()}. Order executed immediately. Order-ID: {order_id}. {note}"
            elif order_status in ("new", "orderstatus.new", "pending_new", "orderstatus.pending_new", "accepted", "orderstatus.accepted"):
                return (
                    f"Sell order for {qty} shares of {symbol.upper()} placed (Order-ID: {order_id}). "
                    f"Status: {order_status}. NOTE: The US stock market may be closed. "
                    f"The order will execute when the market opens. {note}"
                )
            else:
                return f"Order for {qty} shares of {symbol.upper()} placed. Status: {order_status}. Order-ID: {order_id}. {note}"

        return str(result)
    except Exception as e:
        return f"Error selling {symbol}: {str(e)}"
