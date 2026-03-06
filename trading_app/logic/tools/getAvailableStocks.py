"""Tool: Get available NASDAQ 100 stocks."""

from langchain.tools import tool
from logic.api.alpaca.alpaca_get_all_assets import get_nasdaq100_assets


@tool("get_available_stocks", description="Fetches NASDAQ 100 data and displays all available Stocks to buy")
def get_available_stocks():
    """
    Retrieves all currently available/purchasable stocks as a list of ticker symbols with stock names.
    """
    try:
        rows = get_nasdaq100_assets(
            include_symbol=True,
            include_name=True,
            include_last_sale=False,
            include_net_change=False,
            include_percent_change=False,
            include_delta_indicator=False,
        )
        return rows
    except Exception as e:
        return {"error": f"Internal NASDAQ100 function failed: {str(e)}"}
