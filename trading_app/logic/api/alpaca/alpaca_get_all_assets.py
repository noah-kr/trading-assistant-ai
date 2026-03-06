"""
NASDAQ 100 Assets - Fetches the NASDAQ 100 list from NASDAQ API.
"""

import requests


def parse_price(value):
    if value is None:
        return None
    if isinstance(value, str):
        value = value.replace("$", "").replace(",", "").replace("%", "").replace("+", "").strip()
    try:
        return float(value)
    except ValueError:
        return None


def load_nasdaq100():
    """Load NASDAQ 100 directly from NASDAQ API."""
    url = "https://api.nasdaq.com/api/quote/list-type/nasdaq100"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.nasdaq.com",
        "Referer": "https://www.nasdaq.com/",
    }

    try:
        res = requests.get(url, headers=headers)
        data = res.json()

        inner = data.get("data")
        if not inner:
            raise Exception("Missing 'data'")

        table = inner.get("data")
        if not table:
            raise Exception("Missing inner 'data' block")

        rows = table.get("rows")
        if not rows:
            raise Exception("Missing 'rows'")

        return rows

    except Exception as e:
        raise RuntimeError(f"Failed to load NASDAQ 100: {e}")


def get_nasdaq100_assets(
    include_symbol=True,
    include_name=False,
    include_last_sale=False,
    include_net_change=False,
    include_percent_change=False,
    include_delta_indicator=False,
):
    """
    Returns NASDAQ-100 stocks with dynamically selected fields.
    """
    rows = load_nasdaq100()
    filtered = []

    for row in rows:
        entry = {}
        if include_symbol:
            entry["symbol"] = row["symbol"]
        if include_name:
            entry["name"] = row["companyName"]
        if include_last_sale:
            entry["last_sale"] = parse_price(row.get("lastSalePrice"))
        if include_net_change:
            entry["net_change"] = parse_price(row.get("netChange"))
        if include_percent_change:
            entry["percent_change"] = parse_price(row.get("percentageChange"))
        if include_delta_indicator:
            entry["deltaIndicator"] = row.get("deltaIndicator")
        filtered.append(entry)

    return filtered
