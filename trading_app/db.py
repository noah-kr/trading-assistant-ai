"""
Database layer using SQLite.
"""

import sqlite3
import os
from flask import g

DATABASE_PATH = os.path.join(os.path.dirname(__file__), "database.db")


def get_db():
    """Get a database connection for the current request (Flask `g` context)."""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE_PATH)
        g.db.row_factory = sqlite3.Row  # allows dict-like access: row["column"]
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    """Close db connection at end of request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create all tables if they don't exist."""
    from flask import current_app
    current_app.teardown_appcontext(close_db)

    db = sqlite3.connect(DATABASE_PATH)
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            alpaca_account_id TEXT,
            alpaca_relationship_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    db.commit()
    db.close()


# ---------------------------------------------------------------------------
# Helper functions used by the AI agents/tools (replaces the old app.db)
# ---------------------------------------------------------------------------

def get_alpaca_account_for_user(user_id: int):
    """
    Returns (account_id, relationship_id) for a user.
    If the user has no Alpaca account yet, auto-creates one in the sandbox.
    """
    db = sqlite3.connect(DATABASE_PATH)
    db.row_factory = sqlite3.Row
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    db.close()

    if not user:
        raise ValueError(f"User {user_id} not found")

    if user["alpaca_account_id"]:
        return user["alpaca_account_id"], user["alpaca_relationship_id"]

    # Auto-provision: create an Alpaca account on-the-fly
    from logic.api.alpaca.alpaca_account import create_alpaca_account_for_user
    result = create_alpaca_account_for_user(user["username"])
    if "error" in result:
        raise ValueError(result["error"])

    save_alpaca_account(user_id, result["account_id"], result.get("relationship_id", ""))
    return result["account_id"], result.get("relationship_id", "")


def get_username(user_id: int) -> str:
    """Returns the username for a given user id."""
    db = sqlite3.connect(DATABASE_PATH)
    db.row_factory = sqlite3.Row
    user = db.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
    db.close()

    if not user:
        raise ValueError(f"User {user_id} not found")
    return user["username"]


def save_alpaca_account(user_id: int, account_id: str, relationship_id: str):
    """Saves the Alpaca account IDs for a user after Alpaca account creation."""
    db = sqlite3.connect(DATABASE_PATH)
    db.execute(
        "UPDATE users SET alpaca_account_id = ?, alpaca_relationship_id = ? WHERE id = ?",
        (account_id, relationship_id, user_id),
    )
    db.commit()
    db.close()
