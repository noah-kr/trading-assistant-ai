"""
Alpaca Funding - Deposit money into a user's Alpaca Broker sandbox account.

Uses the Alpaca Broker REST API directly:
  1. Ensures an ACH relationship exists (auto-creates one in sandbox).
  2. Creates an INCOMING ACH transfer for the requested amount.
"""

import os
import requests
from db import get_alpaca_account_for_user, save_alpaca_account
import sqlite3

_BASE = "https://broker-api.sandbox.alpaca.markets/v1"


def _auth():
    """Return (key, secret) tuple for requests basic-auth."""
    return (
        os.getenv("APCA_BROKER_KEY_ID", ""),
        os.getenv("APCA_BROKER_SECRET_KEY", ""),
    )


def _ensure_ach_relationship(account_id: str, owner_name: str) -> str:
    """
    Return the ACH relationship ID for the account.
    If one already exists (stored in DB or on Alpaca), reuse it.
    Otherwise create a new one with dummy sandbox bank details.
    """
    # 1. Check if we already have it in the DB
    from db import DATABASE_PATH
    db = sqlite3.connect(DATABASE_PATH)
    db.row_factory = sqlite3.Row
    row = db.execute(
        "SELECT alpaca_relationship_id FROM users WHERE alpaca_account_id = ?",
        (account_id,),
    ).fetchone()
    db.close()

    if row and row["alpaca_relationship_id"]:
        return row["alpaca_relationship_id"]

    # 2. Check Alpaca for existing relationships
    resp = requests.get(
        f"{_BASE}/accounts/{account_id}/ach_relationships",
        auth=_auth(),
    )
    if resp.status_code == 200:
        rels = resp.json()
        approved = [r for r in rels if r.get("status") == "APPROVED"]
        if approved:
            rel_id = approved[0]["id"]
            # Persist it
            db = sqlite3.connect(DATABASE_PATH)
            db.execute(
                "UPDATE users SET alpaca_relationship_id = ? WHERE alpaca_account_id = ?",
                (rel_id, account_id),
            )
            db.commit()
            db.close()
            return rel_id

    # 3. Create a new ACH relationship (sandbox auto-approves)
    resp = requests.post(
        f"{_BASE}/accounts/{account_id}/ach_relationships",
        json={
            "account_owner_name": owner_name or "Account Holder",
            "bank_account_type": "CHECKING",
            "bank_account_number": "32165498720",
            "bank_routing_number": "121000358",
        },
        auth=_auth(),
    )
    resp.raise_for_status()
    rel_id = resp.json()["id"]

    # Persist
    db = sqlite3.connect(DATABASE_PATH)
    db.execute(
        "UPDATE users SET alpaca_relationship_id = ? WHERE alpaca_account_id = ?",
        (rel_id, account_id),
    )
    db.commit()
    db.close()
    return rel_id


def deposit_for_user(user_id: int, amount: float) -> dict:
    """
    Deposit funds into the user's Alpaca sandbox account.
    Returns a dict with success info or an error message.
    """
    # Get user's Alpaca account
    try:
        account_id, _ = get_alpaca_account_for_user(user_id)
    except ValueError as e:
        return {"error": str(e)}

    # Get username for ACH relationship owner name
    from db import get_username
    try:
        owner_name = get_username(user_id)
    except ValueError:
        owner_name = "Account Holder"

    # Ensure ACH relationship exists
    try:
        rel_id = _ensure_ach_relationship(account_id, owner_name)
    except Exception as e:
        return {"error": f"Could not set up bank link: {e}"}

    # Create the deposit transfer
    try:
        resp = requests.post(
            f"{_BASE}/accounts/{account_id}/transfers",
            json={
                "transfer_type": "ach",
                "relationship_id": rel_id,
                "amount": str(amount),
                "direction": "INCOMING",
            },
            auth=_auth(),
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "success": True,
            "transfer_id": data.get("id"),
            "amount": float(data.get("amount", amount)),
            "status": data.get("status", "QUEUED"),
        }
    except requests.HTTPError as e:
        body = ""
        try:
            body = e.response.json().get("message", e.response.text)
        except Exception:
            body = str(e)
        return {"error": f"Deposit failed: {body}"}
    except Exception as e:
        return {"error": f"Deposit failed: {e}"}
