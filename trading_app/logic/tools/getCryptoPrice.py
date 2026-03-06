"""Tool: Get current cryptocurrency price from Alpaca."""

import os
import httpx
from langchain.tools import tool


@tool("get_crypto_price", description="Gets the current price of a cryptocurrency")
def get_crypto_price(symbol: str):
    """
    Returns the current price for a cryptocurrency.

    Args:
        symbol (str): Crypto symbol (e.g., "BTC", "ETH", "BTC/USD", "BTCUSD")
    """
    symbol = symbol.upper().replace("-", "")
    if "/" not in symbol:
        if symbol.endswith("USD"):
            base = symbol[:-3]
        else:
            base = symbol
        formatted = f"{base}/USD"
    else:
        formatted = symbol

    url = os.getenv("ALPACA_CRYPTO_DATA_URL", "https://data.alpaca.markets")
    endpoint = f"{url}/v1beta3/crypto/us/latest/quotes"

    headers = {}
    api_key = os.getenv("APCA_API_KEY_ID")
    secret_key = os.getenv("APCA_API_SECRET_KEY")
    if api_key and secret_key:
        headers = {
            "APCA-API-KEY-ID": api_key,
            "APCA-API-SECRET-KEY": secret_key,
        }

    try:
        with httpx.Client(timeout=10) as client:
            response = client.get(endpoint, params={"symbols": formatted}, headers=headers)

            if response.status_code != 200:
                return {"error": f"API error: {response.status_code} - {response.text}"}

            data = response.json()
            quotes = data.get("quotes", {})

            if formatted not in quotes:
                return {"error": f"No quote found for {symbol}"}

            quote = quotes[formatted]
            ask = quote.get("ap", 0)
            bid = quote.get("bp", 0)
            mid = (ask + bid) / 2 if ask and bid else ask or bid

            return {
                "symbol": formatted,
                "ask_price": ask,
                "bid_price": bid,
                "mid_price": round(mid, 2),
                "timestamp": quote.get("t"),
            }

    except Exception as e:
        return {"error": f"Failed to get crypto price: {str(e)}"}
