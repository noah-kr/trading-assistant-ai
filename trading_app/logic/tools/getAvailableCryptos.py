"""Tool: Get available cryptocurrencies."""

from langchain.tools import tool
from logic.api.alpaca.alpaca_crypto_data import SUPPORTED_CRYPTOS


@tool("get_available_cryptos", description="Fetches all available cryptocurrencies that can be bought and sold")
def get_available_cryptos():
    """
    Returns all available cryptocurrencies for trading.
    """
    try:
        return SUPPORTED_CRYPTOS.copy()
    except Exception as e:
        return {"error": f"Failed to get cryptocurrencies: {str(e)}"}
