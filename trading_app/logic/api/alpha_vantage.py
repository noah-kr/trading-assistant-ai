"""
Alpha Vantage API wrapper - Fetches historical stock data.
"""

import os
import requests


ALPHA_VANTAGE_BASE = "https://www.alphavantage.co/query"


def get_stock_history_data(symbol: str, timeframe: str = "daily", period: str = "1y"):
    """
    Fetch historical stock price data from Alpha Vantage.

    Args:
        symbol:    Ticker symbol (e.g. "AAPL")
        timeframe: "daily", "weekly", or "monthly"
        period:    How far back - "1m", "3m", "6m", "1y", "5y", "max" (controls outputsize)

    Returns:
        dict with "symbol", "timeframe", "data" (list of {date, open, high, low, close, volume})
    """
    api_key = os.getenv("ALPHA_VANTAGE_KEY", "")
    if not api_key:
        return {"error": "ALPHA_VANTAGE_KEY not set in environment."}

    # Map timeframe to API function
    func_map = {
        "daily":   "TIME_SERIES_DAILY",
        "weekly":  "TIME_SERIES_WEEKLY",
        "monthly": "TIME_SERIES_MONTHLY",
    }
    function = func_map.get(timeframe, "TIME_SERIES_DAILY")

    # Determine output size
    compact_periods = {"1m", "3m"}
    outputsize = "compact" if period in compact_periods else "full"

    params = {
        "function": function,
        "symbol": symbol.upper(),
        "apikey": api_key,
        "outputsize": outputsize,
    }

    try:
        resp = requests.get(ALPHA_VANTAGE_BASE, params=params, timeout=15)
        resp.raise_for_status()
        raw = resp.json()

        # Alpha Vantage wraps data under different keys depending on function
        ts_key_map = {
            "TIME_SERIES_DAILY":   "Time Series (Daily)",
            "TIME_SERIES_WEEKLY":  "Weekly Time Series",
            "TIME_SERIES_MONTHLY": "Monthly Time Series",
        }
        ts_key = ts_key_map.get(function, "Time Series (Daily)")
        time_series = raw.get(ts_key)

        if not time_series:
            # Check for error / rate limit messages
            note = raw.get("Note") or raw.get("Information") or raw.get("Error Message")
            if note:
                return {"error": note}
            return {"error": f"No data returned for {symbol}. Response keys: {list(raw.keys())}"}

        # Convert to ordered list
        data_points = []
        for date_str, values in sorted(time_series.items(), reverse=True):
            data_points.append({
                "date": date_str,
                "open": float(values["1. open"]),
                "high": float(values["2. high"]),
                "low": float(values["3. low"]),
                "close": float(values["4. close"]),
                "volume": int(values["5. volume"]),
            })

        # Trim based on period
        limit = _period_to_limit(period, timeframe)
        if limit and limit < len(data_points):
            data_points = data_points[:limit]

        return {
            "symbol": symbol.upper(),
            "timeframe": timeframe,
            "period": period,
            "data": data_points,
        }

    except requests.RequestException as e:
        return {"error": f"Alpha Vantage request failed: {str(e)}"}


def _period_to_limit(period: str, timeframe: str) -> int | None:
    """Convert period string to number of data points."""
    if timeframe == "daily":
        mapping = {"1m": 22, "3m": 66, "6m": 132, "1y": 252, "5y": 1260}
    elif timeframe == "weekly":
        mapping = {"1m": 4, "3m": 13, "6m": 26, "1y": 52, "5y": 260}
    elif timeframe == "monthly":
        mapping = {"1m": 1, "3m": 3, "6m": 6, "1y": 12, "5y": 60}
    else:
        return None
    return mapping.get(period)
