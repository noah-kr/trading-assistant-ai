"""
Alpaca Portfolio Logic - Fetches user positions.
"""

import os
from uuid import UUID
from alpaca.broker import BrokerClient

from db import get_alpaca_account_for_user


def _get_broker() -> BrokerClient:
    return BrokerClient(
        api_key=os.getenv("APCA_BROKER_KEY_ID"),
        secret_key=os.getenv("APCA_BROKER_SECRET_KEY"),
        sandbox=True,
    )


def get_portfolio_data(user_id: int) -> dict:
    """
    Returns all current positions of a user, plus account cash & equity.
    """
    account_id_str = get_alpaca_account_for_user(user_id)[0]
    account_id = UUID(account_id_str) if isinstance(account_id_str, str) else account_id_str
    client = _get_broker()

    # Fetch account-level info (cash, equity, buying power)
    cash = 0.0
    equity = 0.0
    buying_power = 0.0
    try:
        acct = client.get_trade_account_by_id(account_id)
        cash = float(acct.cash or 0)
        equity = float(acct.equity or 0)
        buying_power = float(acct.buying_power or 0)
    except Exception:
        pass

    try:
        positions = client.get_all_positions_for_account(account_id)
    except Exception as e:
        return {
            "error": f"Failed to fetch positions: {e}",
            "positions": [],
            "cash": cash,
            "equity": equity,
            "buying_power": buying_power,
        }

    result = []
    for p in positions:
        result.append({
            "symbol": p.symbol,
            "qty": float(p.qty),
            "avg_entry_price": float(p.avg_entry_price),
            "market_value": float(p.market_value),
            "current_price": float(p.current_price),
            "unrealized_pl": float(p.unrealized_pl),
            "unrealized_plpc": float(p.unrealized_plpc),
        })

    return {
        "status": "OK",
        "positions_count": len(result),
        "positions": result,
        "cash": cash,
        "equity": equity,
        "buying_power": buying_power,
    }
