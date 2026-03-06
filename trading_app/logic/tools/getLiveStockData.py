"""Tool: Get live NASDAQ-100 stock data."""

from langchain.tools import tool
from logic.api.alpaca.alpaca_get_all_assets import get_nasdaq100_assets


@tool("get_stock_data", description="Fetches NASDAQ 100 data for a given stock symbol.")
def get_stock_data(symbol: str):
    """
    Fetches current NASDAQ-100 data for a specific symbol.

    Args:
        symbol (str): Ticker symbol (e.g., 'AAPL', 'MSFT')
    """
    try:
        rows = get_nasdaq100_assets(
            include_symbol=True,
            include_name=True,
            include_last_sale=True,
            include_net_change=True,
            include_percent_change=True,
            include_delta_indicator=True,
        )

        symbol_upper = symbol.upper()
        match = next((row for row in rows if row["symbol"] == symbol_upper), None)

        if not match:
            return {"error": f"{symbol_upper} is not included in the NASDAQ 100."}

        return match

    except Exception as e:
        return {"error": f"Internal NASDAQ100 function failed: {str(e)}"}
