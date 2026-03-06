"""Tool: Sell Cryptocurrency via Alpaca Broker API."""

import os
from langchain.tools import tool
from langchain_core.runnables import RunnableConfig

from alpaca.broker.client import BrokerClient
from alpaca.broker.requests import OrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType

from db import get_alpaca_account_for_user, get_username


def _get_broker() -> BrokerClient:
    return BrokerClient(
        api_key=os.getenv("APCA_BROKER_KEY_ID"),
        secret_key=os.getenv("APCA_BROKER_SECRET_KEY"),
        sandbox=True,
    )


@tool("sell_crypto", return_direct=True)
def sell_crypto(symbol: str, qty: float = None, notional: float = None, *, config: RunnableConfig) -> str:
    """
    Places a SELL order for a cryptocurrency.

    Args:
        symbol (str): Crypto symbol (e.g., "BTC", "ETH", "BTC/USD")
        qty (float, optional): Quantity to sell (in crypto units)
        notional (float, optional): Dollar amount to sell (alternative to qty)
    """
    user_id = config["configurable"]["user_id"]
    symbol = symbol.upper().replace("/USD", "").replace("USD", "")
    crypto_symbol = f"{symbol}/USD"

    account_id = get_alpaca_account_for_user(user_id)[0]
    username = get_username(user_id)
    client = _get_broker()

    order_params = {
        "account_id": account_id,
        "username": username,
        "symbol": crypto_symbol,
        "side": OrderSide.SELL,
        "type": OrderType.MARKET,
        "time_in_force": TimeInForce.GTC,
    }

    if notional and not qty:
        order_params["notional"] = notional
    elif qty:
        order_params["qty"] = qty
    else:
        return "Error: Must provide either qty or notional amount"

    try:
        order_req = OrderRequest(**order_params)
        order = client.submit_order_for_account(account_id, order_req)

        order_status = str(order.status).lower()
        order_id = str(order.id)
        amount_str = f"{qty} {symbol}" if qty else f"${notional} of {symbol}"

        return f"Sell order for {amount_str} placed. Status: {order_status}. Order-ID: {order_id}."

    except Exception as e:
        return f"Error selling {symbol}: {str(e)}"
