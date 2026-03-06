"""
Crypto Data - Supported cryptos list and quote fetching via Alpaca.
"""

import os
import httpx

SUPPORTED_CRYPTOS = [
    {"symbol": "BTC/USD",  "name": "Bitcoin",              "base": "BTC"},
    {"symbol": "ETH/USD",  "name": "Ethereum",             "base": "ETH"},
    {"symbol": "SOL/USD",  "name": "Solana",               "base": "SOL"},
    {"symbol": "DOGE/USD", "name": "Dogecoin",             "base": "DOGE"},
    {"symbol": "SHIB/USD", "name": "Shiba Inu",            "base": "SHIB"},
    {"symbol": "AVAX/USD", "name": "Avalanche",            "base": "AVAX"},
    {"symbol": "DOT/USD",  "name": "Polkadot",             "base": "DOT"},
    {"symbol": "LINK/USD", "name": "Chainlink",            "base": "LINK"},
    {"symbol": "UNI/USD",  "name": "Uniswap",              "base": "UNI"},
    {"symbol": "AAVE/USD", "name": "Aave",                 "base": "AAVE"},
    {"symbol": "LTC/USD",  "name": "Litecoin",             "base": "LTC"},
    {"symbol": "BCH/USD",  "name": "Bitcoin Cash",         "base": "BCH"},
    {"symbol": "XLM/USD",  "name": "Stellar",              "base": "XLM"},
    {"symbol": "ALGO/USD", "name": "Algorand",             "base": "ALGO"},
    {"symbol": "ATOM/USD", "name": "Cosmos",               "base": "ATOM"},
    {"symbol": "NEAR/USD", "name": "NEAR Protocol",        "base": "NEAR"},
    {"symbol": "APE/USD",  "name": "ApeCoin",              "base": "APE"},
    {"symbol": "MATIC/USD","name": "Polygon",              "base": "MATIC"},
    {"symbol": "XRP/USD",  "name": "Ripple",               "base": "XRP"},
    {"symbol": "ADA/USD",  "name": "Cardano",              "base": "ADA"},
]


def get_crypto_quote_data(symbol: str):
    """
    Fetch the latest quote for a crypto pair from Alpaca data API.
    symbol should be like 'BTC/USD'.
    """
    api_key = os.getenv("APCA_API_KEY_ID", "")
    api_secret = os.getenv("APCA_API_SECRET_KEY", "")

    # Alpaca crypto data endpoint (works for both paper and live)
    base_url = "https://data.alpaca.markets/v1beta3/crypto/us"
    url = f"{base_url}/latest/quotes"

    headers = {
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": api_secret,
    }
    params = {"symbols": symbol}

    try:
        resp = httpx.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        quotes = data.get("quotes", {})
        quote = quotes.get(symbol)
        if not quote:
            return {"error": f"No quote data for {symbol}"}

        return {
            "symbol": symbol,
            "ask_price": float(quote.get("ap", 0)),
            "ask_size": float(quote.get("as", 0)),
            "bid_price": float(quote.get("bp", 0)),
            "bid_size": float(quote.get("bs", 0)),
            "timestamp": quote.get("t", ""),
        }
    except Exception as e:
        return {"error": str(e)}
