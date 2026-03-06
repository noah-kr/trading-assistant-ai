"""Tool: Get user's portfolio positions from Alpaca."""

from langchain.tools import tool
from langchain_core.runnables import RunnableConfig
from logic.api.alpaca.alpaca_portfolio import get_portfolio_data


@tool(
    "get_users_stocks",
    description="Fetches all stocks owned by the user and returns a list of detailed position objects, including profit and loss.",
)
def get_users_stocks(config: RunnableConfig) -> list[dict]:
    """
    Returns all of the user's stocks as a list of objects.
    """
    user_id = config["configurable"]["user_id"]
    portfolio = get_portfolio_data(user_id)

    positions = portfolio.get("positions", [])

    cleaned_positions = []
    for p in positions:
        cleaned_positions.append({
            "symbol": p["symbol"],
            "qty": float(p["qty"]),
            "avg_entry_price": float(p["avg_entry_price"]),
            "market_value": float(p["market_value"]),
            "current_price": float(p["current_price"]),
            "unrealized_pl": float(p["unrealized_pl"]),
            "unrealized_plpc": float(p["unrealized_plpc"]),
        })

    return cleaned_positions
