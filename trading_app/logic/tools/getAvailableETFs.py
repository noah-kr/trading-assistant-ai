"""Tool: Get available ETFs."""

from langchain.tools import tool
from logic.api.alpaca.alpaca_etf_data import POPULAR_ETFS


@tool("get_available_etfs", description="Fetches all available ETFs that can be bought and sold")
def get_available_etfs(category: str = None):
    """
    Returns all available ETFs for trading, optionally filtered by category.

    Args:
        category (str, optional): Filter ETFs by category (e.g., "Tech", "Bonds", "Large Cap")
    """
    try:
        etfs = POPULAR_ETFS.copy()
        if category:
            etfs = [e for e in etfs if e["category"].lower() == category.lower()]
        return etfs
    except Exception as e:
        return {"error": f"Failed to get ETFs: {str(e)}"}
