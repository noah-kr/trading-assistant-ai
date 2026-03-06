"""Tool: Get current ETF price from Alpaca."""

import os
import httpx
from langchain.tools import tool


@tool("get_etf_price", description="Gets the current price of an ETF")
def get_etf_price(symbol: str):
    """
    Returns the current price for an ETF.

    Args:
        symbol (str): ETF symbol (e.g., "SPY", "QQQ", "VOO")
    """
    symbol = symbol.upper()

    url = os.getenv("ALPACA_DATA_URL", "https://data.alpaca.markets")
    endpoint = f"{url}/v2/stocks/{symbol}/quotes/latest"

    headers = {
        "APCA-API-KEY-ID": os.getenv("APCA_API_KEY_ID"),
        "APCA-API-SECRET-KEY": os.getenv("APCA_API_SECRET_KEY"),
    }

    try:
        with httpx.Client(timeout=10) as client:
            response = client.get(endpoint, headers=headers)

            if response.status_code != 200:
                return {"error": f"API error: {response.status_code}"}

            data = response.json()
            quote = data.get("quote", {})

            if not quote:
                return {"error": f"No quote found for {symbol}"}

            ask = quote.get("ap", 0)
            bid = quote.get("bp", 0)
            mid = (ask + bid) / 2 if ask and bid else ask or bid

            return {
                "symbol": symbol,
                "ask_price": ask,
                "bid_price": bid,
                "mid_price": round(mid, 2),
                "timestamp": quote.get("t"),
            }

    except Exception as e:
        return {"error": f"Failed to get ETF price: {str(e)}"}
