"""
Trading AI Assistant - Flask Application
==========================================
Main entry point. Sets up Flask, database, session auth, and all routes.
"""

import os
import hashlib
import logging
from functools import wraps

from flask import Flask, session, request, jsonify, render_template, redirect, url_for
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")

# ---------------------------------------------------------------------------
# Database initialization
# ---------------------------------------------------------------------------
from db import init_db, get_db

with app.app_context():
    init_db()

# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def login_required(f):
    """Decorator that redirects to /login if the user is not logged in."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated


def get_current_user_id() -> int:
    """Return the logged-in user's database id from the session."""
    return session.get("user_id")

# ---------------------------------------------------------------------------
# Page routes (HTML)
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login_page"))
    return redirect(url_for("home"))


@app.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")


@app.route("/register", methods=["GET"])
def register_page():
    return render_template("register.html")


@app.route("/home")
@login_required
def home():
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    return render_template("home.html", username=user["username"])


# ---------------------------------------------------------------------------
# Auth API routes (JSON)
# ---------------------------------------------------------------------------

@app.route("/api/auth/register", methods=["POST"])
def api_register():
    """Register a new user. Expects JSON {username, password}."""
    data = request.get_json()
    username = (data.get("username") or "").strip().lower()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if existing:
        return jsonify({"error": "Username already taken"}), 409

    pw_hash = hashlib.sha256(password.encode()).hexdigest()
    cur = db.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (username, pw_hash),
    )
    db.commit()
    user_id = cur.lastrowid

    # Auto-provision an Alpaca sandbox brokerage account
    try:
        from logic.api.alpaca.alpaca_account import create_alpaca_account_for_user
        from db import save_alpaca_account

        result = create_alpaca_account_for_user(username)
        if "account_id" in result:
            save_alpaca_account(user_id, result["account_id"], result.get("relationship_id", ""))
            logger.info("Alpaca account created for user '%s': %s", username, result["account_id"])
        else:
            logger.warning("Alpaca account creation failed for '%s': %s", username, result.get("error"))
    except Exception as e:
        logger.warning("Alpaca provisioning error for '%s': %s", username, e)

    # Auto-login after registration
    session["user_id"] = user_id
    return jsonify({"status": "ok", "user_id": user_id}), 201


@app.route("/api/auth/login", methods=["POST"])
def api_login():
    """Login. Expects JSON {username, password}."""
    data = request.get_json()
    username = (data.get("username") or "").strip().lower()
    password = data.get("password") or ""

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

    if not user:
        return jsonify({"error": "Invalid username or password"}), 401

    pw_hash = hashlib.sha256(password.encode()).hexdigest()
    if user["password_hash"] != pw_hash:
        return jsonify({"error": "Invalid username or password"}), 401

    session["user_id"] = user["id"]

    # Auto-provision Alpaca account if missing (for users created before this feature)
    if not user["alpaca_account_id"]:
        try:
            from logic.api.alpaca.alpaca_account import create_alpaca_account_for_user
            from db import save_alpaca_account

            result = create_alpaca_account_for_user(username)
            if "account_id" in result:
                save_alpaca_account(user["id"], result["account_id"], result.get("relationship_id", ""))
                logger.info("Alpaca account auto-provisioned for '%s': %s", username, result["account_id"])
        except Exception as e:
            logger.warning("Alpaca auto-provision on login failed for '%s': %s", username, e)

    return jsonify({"status": "ok", "user_id": user["id"]})


@app.route("/api/auth/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"status": "ok"})


@app.route("/api/auth/me")
def api_me():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    db = get_db()
    user = db.execute("SELECT id, username FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"id": user["id"], "username": user["username"]})

# ---------------------------------------------------------------------------
# Chat API route  (the main brain)
# ---------------------------------------------------------------------------

@app.route("/api/chat", methods=["POST"])
@login_required
def api_chat():
    """
    Receives a JSON body { "message": "...", "force_mode": false }
    and forwards it to the AI master agent.
    """
    data = request.get_json()
    user_msg = (data.get("message") or "").strip()
    force_mode = data.get("force_mode", False)

    if not user_msg:
        return jsonify({"error": "Message is required"}), 400

    user_id = get_current_user_id()

    # If force mode, prepend instructions
    if force_mode:
        user_msg = (
            "[FORCE MODE ACTIVE - DO NOT ASK FOLLOW-UP QUESTIONS]\n"
            f"{user_msg}\n\n"
            "IMPORTANT: You are in FORCE MODE. This means:\n"
            "- Do NOT ask follow-up questions\n"
            "- Make all necessary decisions independently\n"
            "- Choose appropriate parameters yourself\n"
            "- Act immediately and decisively\n"
            "- If information is missing: Make a reasonable assumption"
        )

    try:
        from logic.agents.master_agent import master_agent

        result = master_agent.invoke(
            {"messages": [{"role": "user", "content": user_msg}]},
            config={
                "configurable": {
                    "thread_id": f"user-{user_id}",
                    "user_id": user_id,
                }
            },
        )

        last_message = result["messages"][-1]
        answer = last_message.content

        # content can be a list of content blocks (e.g. from deepagents);
        # flatten to a single string for storage and display.
        if isinstance(answer, list):
            answer = "\n".join(
                block if isinstance(block, str) else block.get("text", "")
                for block in answer
            )

        # Save to chat history
        db = get_db()
        db.execute(
            "INSERT INTO chat_history (user_id, role, content) VALUES (?, ?, ?)",
            (user_id, "user", data.get("message", "")),
        )
        db.execute(
            "INSERT INTO chat_history (user_id, role, content) VALUES (?, ?, ?)",
            (user_id, "assistant", answer),
        )
        db.commit()

        return jsonify({"response": answer})

    except Exception as e:
        logger.error("Error in /api/chat: %s", e)
        err_str = str(e)
        # Friendly message for Gemini quota errors
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
            return jsonify({
                "error": "Gemini API rate limit reached. Please wait a minute and try again. "
                         "If this keeps happening, enable billing at https://ai.google.dev or "
                         "switch to a lighter model in your .env file."
            }), 429
        return jsonify({"error": err_str}), 500


# ---------------------------------------------------------------------------
# Chat history API
# ---------------------------------------------------------------------------

@app.route("/api/chat/history")
@login_required
def api_chat_history():
    user_id = get_current_user_id()
    db = get_db()
    rows = db.execute(
        "SELECT role, content, created_at FROM chat_history WHERE user_id = ? ORDER BY id ASC",
        (user_id,),
    ).fetchall()
    return jsonify([dict(r) for r in rows])


# ---------------------------------------------------------------------------
# Portfolio API (proxy to Alpaca)
# ---------------------------------------------------------------------------

@app.route("/api/portfolio")
@login_required
def api_portfolio():
    """Returns the user's current Alpaca positions."""
    try:
        from logic.api.alpaca.alpaca_portfolio import get_portfolio_data
        user_id = get_current_user_id()
        result = get_portfolio_data(user_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# Market data APIs
# ---------------------------------------------------------------------------

@app.route("/api/market/stock/<symbol>")
def api_stock_history(symbol):
    """Returns historical price data for a stock from Alpha Vantage."""
    timeframe = request.args.get("timeframe", "1Hour")
    period = request.args.get("period", "1W")

    try:
        from logic.api.alpha_vantage import get_stock_history_data
        result = get_stock_history_data(symbol, timeframe, period)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/market/crypto/<symbol>")
def api_crypto_quote(symbol):
    """Returns latest crypto quote."""
    try:
        from logic.api.alpaca.alpaca_crypto_data import get_crypto_quote_data
        result = get_crypto_quote_data(symbol)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/market/nasdaq100")
def api_nasdaq100():
    """Returns NASDAQ 100 stock list."""
    try:
        from logic.api.alpaca.alpaca_get_all_assets import get_nasdaq100_assets
        rows = get_nasdaq100_assets(
            include_symbol=True,
            include_name=True,
            include_last_sale=True,
            include_percent_change=True,
        )
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/market/etfs")
def api_etfs():
    """Returns available ETFs."""
    from logic.api.alpaca.alpaca_etf_data import POPULAR_ETFS
    return jsonify(POPULAR_ETFS)


@app.route("/api/market/cryptos")
def api_cryptos():
    """Returns available cryptos."""
    from logic.api.alpaca.alpaca_crypto_data import SUPPORTED_CRYPTOS
    return jsonify(SUPPORTED_CRYPTOS)


# ---------------------------------------------------------------------------
# Trade API (pending orders)
# ---------------------------------------------------------------------------

@app.route("/api/trade/orders")
@login_required
def api_open_orders():
    """Returns all pending orders for the user."""
    try:
        from logic.api.alpaca.alpaca_trade import get_open_orders_for_user
        user_id = get_current_user_id()
        result = get_open_orders_for_user(user_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/trade/orders/<order_id>", methods=["DELETE"])
@login_required
def api_cancel_order(order_id):
    """Cancels a pending order."""
    try:
        from logic.api.alpaca.alpaca_trade import cancel_order_for_user
        user_id = get_current_user_id()
        result = cancel_order_for_user(user_id, order_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# Funding API
# ---------------------------------------------------------------------------

@app.route("/api/funding/deposit", methods=["POST"])
@login_required
def api_deposit():
    """Deposit money into the user's Alpaca sandbox account."""
    data = request.get_json()
    amount = data.get("amount", 0)
    if amount <= 0:
        return jsonify({"error": "Amount must be positive"}), 400

    try:
        from logic.api.alpaca.alpaca_funding import deposit_for_user
        user_id = get_current_user_id()
        result = deposit_for_user(user_id, amount)
        if result.get("error"):
            return jsonify(result), 400
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, port=5001)
