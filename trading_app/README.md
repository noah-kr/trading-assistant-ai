# Trading Assistant

An AI-powered trading assistant web application built with Python (Flask) for the Web and Cloud Computing course at NOVA SBE. The application allows users to manage a simulated investment portfolio through a conversational AI interface, with support for stocks, ETFs, and cryptocurrencies.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Tech Stack](#tech-stack)
4. [Project Structure](#project-structure)
5. [Detailed File Descriptions](#detailed-file-descriptions)
6. [External APIs](#external-apis)
7. [Setup & Installation](#setup--installation)
8. [How to Get API Keys](#how-to-get-api-keys)
9. [Running the Application](#running-the-application)
10. [Features](#features)
11. [Authentication & Security](#authentication--security)
12. [Database Schema](#database-schema)
13. [Multi-Agent AI Architecture](#multi-agent-ai-architecture)

---

## Overview

This application provides a full-stack trading assistant where users can:

- **Chat** with an AI assistant that understands financial markets and can execute trades on the user's behalf
- **View their portfolio** with real-time positions, cash balance, equity, and an allocation chart
- **Browse market data** including NASDAQ 100 stocks, popular ETFs, and cryptocurrencies
- **Deposit funds** into their sandbox brokerage account via simulated ACH transfers
- **Place and cancel orders** for stocks, ETFs, and crypto through natural language commands

All trading happens in Alpaca's **sandbox environment** (paper trading), so no real money is involved. Each user automatically receives a sandbox brokerage account upon registration.

---

## Architecture

The application follows a classic **three-tier architecture**:

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend                                │
│   HTML/CSS/JavaScript (Jinja2 templates, Chart.js, Fetch API)   │
└──────────────────────────────┬──────────────────────────────────┘
                               │ JSON (REST API)
┌──────────────────────────────▼──────────────────────────────────┐
│                      Flask Backend                              │
│   app.py (routes & auth)  ←→  logic/ (agents, tools, APIs)      │
│                               │                                 │
│   db.py (SQLite)              │                                 │
└──────────────────────────────┬──────────────────────────────────┘
                               │ HTTPS
┌──────────────────────────────▼──────────────────────────────────┐
│                     External APIs                               │
│   Alpaca Broker API  │  Alpaca Data API  │  Alpha Vantage       │
│   Google Gemini / OpenAI (LLM)           │  NewsAPI             │
└─────────────────────────────────────────────────────────────────┘
```

**Request flow for a chat message:**
1. User types a message in the browser → JavaScript sends a `POST /api/chat` request with JSON body
2. Flask receives the request, authenticates the user via session, and forwards the message to the **master agent**
3. The master agent (LangGraph-based) decides which sub-agent to delegate to (e.g., trading, news, data lookup)
4. The sub-agent may call **tools** that interact with external APIs (Alpaca for trading, NewsAPI for news, etc.)
5. The response flows back through the agent chain → Flask saves it to the database → returns JSON to the frontend
6. JavaScript renders the response in the chat window

---

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Web Framework** | Flask 3.x | HTTP server, routing, session management, template rendering |
| **Database** | SQLite | Storing users, password hashes, Alpaca account IDs, chat history |
| **Frontend** | HTML, CSS, JavaScript | Single-page app with tab navigation, forms, and data display |
| **Charts** | Chart.js 4.x | Portfolio allocation (doughnut chart), stock price history (line charts) |
| **LLM Framework** | LangChain + LangGraph | Orchestrating multi-agent AI conversations with tool calling |
| **Agent Framework** | deepagents | Creating hierarchical agent structures (master → sub-agents) |
| **LLM Providers** | Google Gemini / OpenAI | Natural language understanding and generation |
| **Brokerage** | Alpaca Broker API (sandbox) | Account creation, order placement, positions, funding |
| **Market Data** | Alpaca Data API, Alpha Vantage, NASDAQ API | Stock quotes, crypto prices, historical data |
| **News** | NewsAPI | Financial news articles for sentiment analysis |

---

## Project Structure

```
trading_app/
│
├── app.py                          # Flask application entry point
├── db.py                           # Database layer (SQLite)
├── requirements.txt                # Python package dependencies
├── .env                            # Environment variables (API keys) — not committed
├── .env.example                    # Template showing required environment variables
├── .gitignore                      # Files excluded from version control
├── README.md                       # This file
│
├── templates/                      # Jinja2 HTML templates
│   ├── login.html                  # Login page
│   ├── register.html               # Registration page
│   └── home.html                   # Main application page (chat, portfolio, market)
│
├── static/                         # Static frontend assets
│   ├── style.css                   # Stylesheet (dark/light theme, responsive layout)
│   └── script.js                   # Client-side JavaScript (all UI logic)
│
└── logic/                          # Backend business logic
    ├── __init__.py
    │
    ├── agents/                     # LLM-powered AI agents
    │   ├── __init__.py
    │   ├── llm.py                  # Shared LLM model instance (Gemini or OpenAI)
    │   ├── master_agent.py         # Orchestrator agent that delegates to sub-agents
    │   ├── query_agent.py          # Classifies and normalises user questions
    │   ├── news_decision_agent.py  # Fetches and analyses financial news
    │   ├── numbers_agent.py        # Collects structured market data (prices, positions)
    │   ├── trading_buy_agent.py    # Handles buy orders for stocks, ETFs, and crypto
    │   ├── trading_sell_agent.py   # Handles sell orders for stocks, ETFs, and crypto
    │   └── draw_chart_agent.py     # Generates chart display commands for the frontend
    │
    ├── tools/                      # LangChain tools (callable by agents)
    │   ├── __init__.py
    │   ├── buyStock.py             # Places buy orders for stocks
    │   ├── buyETF.py               # Places buy orders for ETFs
    │   ├── buyCrypto.py            # Places buy orders for cryptocurrencies
    │   ├── sellStock.py            # Places sell orders for stocks
    │   ├── sellETF.py              # Places sell orders for ETFs
    │   ├── sellCrypto.py           # Places sell orders for cryptocurrencies
    │   ├── getAvailableStocks.py   # Retrieves the NASDAQ 100 stock list
    │   ├── getAvailableETFs.py     # Retrieves the available ETFs list
    │   ├── getAvailableCryptos.py  # Retrieves the available cryptocurrencies list
    │   ├── getLiveStockData.py     # Fetches live NASDAQ 100 data for a specific stock
    │   ├── getCryptoPrice.py       # Fetches real-time cryptocurrency prices
    │   ├── getETFPrice.py          # Fetches real-time ETF prices
    │   ├── getUsersStocks.py       # Retrieves the user's current portfolio positions
    │   ├── getNews.py              # Searches for financial news articles
    │   └── getPendingOrders.py     # Retrieves and cancels pending orders
    │
    └── api/                        # External API wrappers
        ├── __init__.py
        ├── alpha_vantage.py        # Alpha Vantage historical stock data wrapper
        └── alpaca/                 # Alpaca API modules
            ├── __init__.py
            ├── alpaca_account.py       # Sandbox account provisioning
            ├── alpaca_portfolio.py     # Portfolio data fetching
            ├── alpaca_trade.py         # Order placement and management
            ├── alpaca_funding.py       # ACH deposit transfers
            ├── alpaca_get_all_assets.py # NASDAQ 100 data from NASDAQ API
            ├── alpaca_crypto_data.py   # Crypto data and supported pairs list
            └── alpaca_etf_data.py      # Popular ETFs static list
```

---

## Detailed File Descriptions

### Root Files

#### `app.py` — Flask Application Entry Point
This is the main file that starts the web server. It defines all HTTP routes organised into sections:

- **Page routes**: Serve the HTML pages (`/login`, `/register`, `/home`). The `/` root path redirects to `/home` if logged in, otherwise `/login`.
- **Auth routes** (`/api/auth/*`): Handle user registration, login, logout, and identity queries. Registration also auto-provisions an Alpaca sandbox brokerage account for the new user. Login checks for missing Alpaca accounts and creates them on-the-fly for legacy users.
- **Chat route** (`/api/chat`): Receives a user message as JSON, forwards it to the master AI agent, saves the conversation to the database, and returns the agent's response. Supports a "Force Mode" flag that tells the AI to act immediately without asking follow-up questions.
- **Chat history route** (`/api/chat/history`): Returns the full conversation history for the logged-in user so the frontend can restore past messages on page load.
- **Portfolio route** (`/api/portfolio`): Proxies to the Alpaca portfolio module to return the user's positions, cash, equity, and buying power.
- **Market data routes** (`/api/market/*`): Provide stock history from Alpha Vantage, crypto quotes from Alpaca, NASDAQ 100 listings, ETF lists, and crypto lists.
- **Trade routes** (`/api/trade/*`): Return pending orders and allow cancellation of specific orders.
- **Funding route** (`/api/funding/deposit`): Processes fund deposits through ACH transfers to the user's sandbox account.

All API routes return JSON. Authentication-protected routes use a `@login_required` decorator that checks for `session["user_id"]`.

#### `db.py` — Database Layer
Manages the SQLite database. Provides:

- `init_db()`: Creates the `users` and `chat_history` tables on startup.
- `get_db()` / `close_db()`: Flask request-scoped database connection management using Flask's `g` context object. Each HTTP request gets its own connection which is auto-closed afterwards.
- `get_alpaca_account_for_user(user_id)`: Looks up the user's Alpaca account and relationship IDs. If no account exists, it automatically provisions one by calling the Alpaca account creation module. This ensures every user always has a working brokerage account.
- `get_username(user_id)`: Retrieves a username by ID (used for ACH relationship naming).
- `save_alpaca_account(user_id, account_id, relationship_id)`: Persists newly created Alpaca account credentials.

#### `requirements.txt` — Python Dependencies
Lists all required Python packages with minimum version constraints. Key dependencies:
- `flask` — Web framework
- `langchain`, `langgraph`, `deepagents` — AI agent orchestration
- `langchain-google-genai`, `langchain-openai` — LLM provider bindings
- `alpaca-py` — Alpaca Broker SDK for trading operations
- `httpx`, `requests` — HTTP clients for direct API calls
- `newsapi-python` — NewsAPI SDK
- `pydantic` — Data validation for order models

#### `.env.example` — Environment Variable Template
Shows all required API keys with placeholder values. Users copy this to `.env` and fill in real keys. The `.env` file is excluded from version control by `.gitignore`. (Left it in for now, so everyone can test it without having to set up every API)

#### `.gitignore` — Version Control Exclusions
Prevents sensitive and generated files from being committed: `.env` (API keys), `database.db` (user data), `__pycache__/` (compiled Python), `.DS_Store` (macOS metadata).

---

### Templates (`templates/`)

#### `login.html` — Login Page
A standalone page with a centered card containing username/password fields. On form submission, JavaScript sends a `POST /api/auth/login` request. On success, redirects to `/home`. Displays error messages inline if authentication fails. Includes a link to the registration page. Supports dark/light theme via a `<script>` block that reads the user's theme preference from `localStorage` before the page renders, preventing a flash of the wrong theme.

#### `register.html` — Registration Page
Similar to the login page but with an additional "Confirm Password" field. Client-side validation ensures passwords match before sending the request. On successful registration, the user is automatically logged in and redirected to `/home`. The backend creates both the user account and an Alpaca sandbox brokerage account.

#### `home.html` — Main Application Page
The core of the application. It contains three tabs managed by JavaScript:

1. **Chat Tab**: A scrollable message area showing the conversation between the user and the AI assistant. Includes a text input form with a "Send" button and a "Force Mode" checkbox. A hidden modal overlay is used to display stock charts when the AI decides to show one.

2. **Portfolio Tab**: Contains four panels laid out in a responsive CSS grid:
   - *Your Portfolio*: Summary cards (Cash, Positions, Market Value, P&L, Equity, Buying Power) and a data table listing each position with symbol, quantity, market value, average entry price, current price, and unrealised profit/loss. A "Refresh" button reloads the data.
   - *Portfolio Allocation*: A doughnut chart (Chart.js) showing the relative size of each position.
   - *Pending Orders*: A table of open orders with a "Cancel" button on each row.
   - *Deposit Funds*: A form to deposit a specified USD amount, with a status message shown after submission.

3. **Market Tab**: Contains four panels:
   - *Stock Lookup*: A search form where the user enters a ticker symbol and selects a timeframe and period. Results are displayed as a Chart.js line chart with close, high, and low prices.
   - *NASDAQ 100*: A scrollable list of all NASDAQ 100 stocks with current prices and percentage changes. Loaded on demand when the user clicks a button.
   - *Popular ETFs*: A scrollable list of popular ETFs with their categories.
   - *Cryptocurrencies*: A scrollable list of supported crypto pairs.

The navigation bar at the top shows the app name, tab buttons, the logged-in username, a theme toggle button (dark/light mode), and a logout button.

---

### Static Assets (`static/`)

#### `style.css` — Stylesheet
Defines the complete visual appearance of the application using CSS custom properties (variables) for theming. Organised into sections:

- **Theme variables**: Two sets of colour definitions — dark (default, defined on `:root`) and light (on `[data-theme="light"]`). Covers backgrounds, text colours, borders, accent colours, chart colours, and status colours (green for positive, red for negative).
- **Auth pages**: Centered card layout with gradient background for login/register.
- **Buttons**: Primary (blue), danger (red), and small variants with hover/active states.
- **Navbar**: Horizontal bar with flexbox, tab buttons with bottom-border active indicator, theme toggle button.
- **Tab system**: `display: none` / `display: block` toggling via `.tab-content.active`.
- **Chat**: Flexbox column layout. User messages are right-aligned with blue background; assistant messages are left-aligned with card background. A typing indicator animation uses CSS `@keyframes` with dot animation.
- **Panels**: CSS Grid layout (`grid-template-columns: repeat(auto-fit, minmax(380px, 1fr))`) for responsive panel arrangement. Each panel has card styling. Supports `overflow-x: auto` for tables that might overflow.
- **Tables**: Clean table styling with uppercase headers, hover effects, and `white-space: nowrap` to prevent cell content overflow.
- **Scrollable lists**: Fixed-height containers with vertical scroll for long lists (NASDAQ 100, ETFs, cryptos).
- **Forms**: Inline form layout for deposit and stock lookup, with input styling matching the theme.
- **Portfolio summary cards**: Flex-wrap cards showing key metrics.
- **Chart modal**: Full-screen overlay for stock charts triggered from chat.
- **Responsive**: Media query at 768px switches panel grid to single column and adjusts spacing.
- **Scrollbar**: Custom thin scrollbar styling for WebKit browsers.

#### `script.js` — Client-Side JavaScript
Contains all frontend interactivity. Organised into sections:

- **Tab navigation**: Listens for click events on nav tabs, toggles `.active` class, and triggers data loading when switching to Portfolio or Market tabs.
- **Logout handler**: Sends `POST /api/auth/logout` and redirects to the login page.
- **Theme toggle**: Reads/writes the theme preference to `localStorage` and updates the `data-theme` attribute on the `<html>` element. Swaps the toggle button icon between a moon (☽) and sun (☀).
- **`chartColors()` helper**: Reads current CSS variable values for chart grid, text, and legend colours so that Chart.js instances automatically match the theme.
- **Chat**: Loads chat history on page load via `GET /api/chat/history`. On form submit, sends `POST /api/chat` with the message and Force Mode flag, shows a typing indicator, then renders the response. Parses responses for chart commands (JSON with `"type": "SHOW_STOCK_CHART"`) and opens the chart modal when detected.
- **Chart modal**: Fetches stock data from `/api/market/stock/<symbol>` and renders a Chart.js line chart in a modal overlay. Destroys the chart instance on close to prevent memory leaks.
- **Portfolio loading**: Fetches positions from `/api/portfolio`, calculates totals, renders summary cards and the positions table, and creates/updates the doughnut chart. Also fetches pending orders from `/api/trade/orders` and renders them with cancel buttons.
- **Order cancellation**: Sends `DELETE /api/trade/orders/<id>` and refreshes the portfolio on success.
- **Deposit form**: Sends `POST /api/funding/deposit` with the amount, displays success/error messages, and triggers a portfolio refresh after a short delay.
- **Market data**: Lazy-loads ETF and crypto lists when the Market tab is first opened. NASDAQ 100 loads on button click. Stock lookup form fetches historical data and renders a line chart with close, high, and low datasets.
- **`generateColors(n)` helper**: Returns an array of distinct colours for chart segments, cycling through 15 predefined colours.

---

### Logic Layer (`logic/`)

The `logic/` directory contains all business logic, separated from the Flask routing layer. It is organised into three sub-packages:

#### Agents (`logic/agents/`)

##### `llm.py` — Shared LLM Instance
Creates a single LLM instance that all agents share. Supports two providers:
- If `OPENAI_API_KEY` is set in the environment, it creates a `ChatOpenAI` instance (default model: `gpt-4o-mini`).
- Otherwise, if `GOOGLE_API_KEY` is set, it creates a `ChatGoogleGenerativeAI` instance (default model: `gemini-2.5-flash-lite`).
- The `MODEL` environment variable can override the model name for either provider.
- If neither key is set, the application raises a `RuntimeError` at import time.

This centralised approach ensures all agents use the same model and configuration.

##### `master_agent.py` — Orchestrator
The master agent is built using `deepagents.create_deep_agent()` with a system prompt that defines its role as a stock, ETF, and cryptocurrency advisor. It does not have any tools of its own; instead, it delegates to six sub-agents based on the user's intent:
- Questions about news → `news_subagent`
- Questions needing classification → `query_subagent`
- Data lookups and portfolio queries → `numbers_subagent`
- Buy orders → `trading_buy_subagent`
- Sell orders → `trading_sell_subagent`
- Chart requests → `draw_chart_subagent`

It uses `InMemorySaver` as a checkpointer to maintain conversation context within a session (thread ID is per user). The system prompt contains detailed instructions for distinguishing between portfolio queries (which should return text) and chart requests (which should return JSON).

##### `query_agent.py` — Query Classifier
Determines whether a user's question is relevant to stocks/ETFs/crypto or off-topic. If relevant, it normalises the query by extracting company names, ticker symbols, and user intent. If not relevant, it returns `NOT_RELEVANT` with a brief explanation. This helps the master agent decide whether to proceed or politely decline.

##### `news_decision_agent.py` — News Analyst
Has access to the `get_news` tool (which calls NewsAPI). Its system prompt instructs it to research a company, gather recent news, and provide a clear BUY/SELL/HOLD recommendation based on sentiment analysis of the articles.

##### `numbers_agent.py` — Data Collector
The most tool-rich agent. Has access to seven tools: `get_stock_data`, `get_available_stocks`, `get_users_stocks`, `get_crypto_price`, `get_etf_price`, `get_available_cryptos`, `get_available_etfs`. Its job is to gather numerical data and return it in a structured format. It handles portfolio queries ("show me my stocks") by using `get_users_stocks`.

##### `trading_buy_agent.py` — Buy Executor
Equipped with `buy_stock`, `buy_etf`, `buy_crypto`, `get_available_etfs`, and `get_available_cryptos` tools. Parses the user's intent to determine the asset type, symbol, and quantity, then executes the appropriate buy order. For crypto, supports both quantity-based and dollar-amount (notional) orders.

##### `trading_sell_agent.py` — Sell Executor
Equipped with `sell_stock`, `sell_etf`, `sell_crypto`, `get_users_stocks`, `get_pending_orders`, and `cancel_all_orders_for_symbol` tools. Before selling, it can verify the user actually owns the asset. If a sale fails due to a "wash trade" error (conflicting open order), it can automatically cancel the conflicting orders and retry.

##### `draw_chart_agent.py` — Chart Generator
Has no tools. Its sole purpose is to determine whether the user's request warrants a stock/crypto/ETF price chart. If so, it outputs a JSON object like `{"type": "SHOW_STOCK_CHART", "symbol": "AAPL", "period": "1W", "timeframe": "1Hour"}` which the frontend JavaScript detects and uses to render a Chart.js chart in a modal.

---

#### Tools (`logic/tools/`)

Each file in the `tools/` directory defines a LangChain `@tool`-decorated function that an agent can call. All trading tools receive the `user_id` from the LangGraph `RunnableConfig` to scope actions to the correct user.

| Tool File | Tool Name | Description |
|-----------|-----------|-------------|
| `buyStock.py` | `buy_stock` | Places a market buy order for a stock via Alpaca |
| `buyETF.py` | `buy_etf` | Places a market buy order for an ETF via Alpaca |
| `buyCrypto.py` | `buy_crypto` | Places a market buy order for crypto (supports qty or notional) |
| `sellStock.py` | `sell_stock` | Places a market sell order for a stock |
| `sellETF.py` | `sell_etf` | Places a market sell order for an ETF |
| `sellCrypto.py` | `sell_crypto` | Places a market sell order for crypto |
| `getAvailableStocks.py` | `get_available_stocks` | Returns the NASDAQ 100 stock list (symbol + name) |
| `getAvailableETFs.py` | `get_available_etfs` | Returns the list of popular ETFs (optionally filtered by category) |
| `getAvailableCryptos.py` | `get_available_cryptos` | Returns the list of supported cryptocurrency pairs |
| `getLiveStockData.py` | `get_stock_data` | Fetches current NASDAQ 100 data for a specific ticker |
| `getCryptoPrice.py` | `get_crypto_price` | Fetches real-time crypto quote from Alpaca Data API |
| `getETFPrice.py` | `get_etf_price` | Fetches real-time ETF quote from Alpaca Data API |
| `getUsersStocks.py` | `get_users_stocks` | Returns the user's current portfolio positions with P&L |
| `getNews.py` | `get_news` | Searches NewsAPI for articles about a given topic |
| `getPendingOrders.py` | `get_pending_orders` / `cancel_all_orders_for_symbol` | Lists/cancels pending orders |

---

#### API Wrappers (`logic/api/`)

##### `alpha_vantage.py` — Historical Stock Data
Wraps the Alpha Vantage REST API. Fetches daily, weekly, or monthly time series for any stock symbol. Accepts a period parameter (`1m` through `5y`) to control how much data to return. Returns a list of data points with date, open, high, low, close, and volume.

##### `alpaca/alpaca_account.py` — Account Provisioning
Creates new sandbox brokerage accounts via the Alpaca Broker SDK. For each new user, it:
1. Creates an account with placeholder identity data (name derived from username, sandbox-only address and SSN).
2. Creates an ACH bank relationship using sandbox bank details, enabling the user to deposit funds.
3. Returns the `account_id` and `relationship_id` which are stored in the database.

##### `alpaca/alpaca_portfolio.py` — Portfolio Data
Fetches account-level data (cash, equity, buying power) and all positions for a user via the Alpaca Broker SDK. Returns a structured dict used by both the `/api/portfolio` endpoint and the `get_users_stocks` tool.

##### `alpaca/alpaca_trade.py` — Order Management
Core trading logic. Provides:
- `place_order_internal(body)`: Places a market or limit order. Includes automatic wash-trade resolution — if an order fails because an opposite order already exists, it cancels the conflicting orders and retries.
- `get_open_orders_for_user(user_id)`: Returns all non-final orders (pending, accepted, partially filled).
- `cancel_order_for_user(user_id, order_id)`: Cancels a specific order.

Uses a `PlaceOrderBody` Pydantic model for input validation.

##### `alpaca/alpaca_funding.py` — Fund Deposits
Handles ACH transfers using direct REST API calls (not the SDK). The flow:
1. `_ensure_ach_relationship()` checks the database, then Alpaca, for an existing ACH relationship. If none exists, creates one with sandbox bank details.
2. `deposit_for_user()` creates an INCOMING ACH transfer for the specified amount. Returns the transfer ID and status (typically `QUEUED`).

##### `alpaca/alpaca_get_all_assets.py` — NASDAQ 100 Data
Fetches the current NASDAQ 100 stock list from the NASDAQ API. Supports selecting which fields to include (symbol, name, last sale price, net change, percent change). Used by both the market data endpoint and the `get_available_stocks` / `get_stock_data` tools.

##### `alpaca/alpaca_crypto_data.py` — Cryptocurrency Data
Contains a static list of 20 supported crypto trading pairs (BTC/USD, ETH/USD, SOL/USD, etc.) and a function to fetch real-time quotes from the Alpaca Data API.

##### `alpaca/alpaca_etf_data.py` — ETF Data
Contains a static list of 25 popular ETFs across categories (Large Cap, Small Cap, International, Bonds, Commodities, Sector, Thematic, Dividend, Real Estate). Used by the market data endpoint and the `get_available_etfs` tool.

---

## External APIs

The application integrates with the following external services:

| API | Purpose | Authentication | Free Tier |
|-----|---------|---------------|-----------|
| **Alpaca Broker API** | Account creation, trading, positions, funding | API key + secret (HTTP Basic Auth) | Free sandbox |
| **Alpaca Data API** | Real-time crypto and ETF quotes | API key + secret (HTTP headers) | Included with Alpaca account |
| **Alpha Vantage** | Historical stock price data (daily/weekly/monthly) | API key (query parameter) | 25 requests/day |
| **NewsAPI** | Financial news articles | API key | 100 requests/day |
| **Google Gemini** | LLM for AI chat assistant | API key | Free tier available |
| **OpenAI** | Alternative LLM provider | API key | Pay-per-use |

---

## Setup & Installation

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)

### 1. Install dependencies
```bash
cd trading_app
pip install -r requirements.txt
```

### 2. Configure environment variables
```bash
cp .env.example .env
```
Open `.env` in a text editor and fill in your API keys (see next section).

### 3. Run the application
```bash
python app.py
```
The server starts on http://localhost:5001.

---

## How to Get API Keys

### Google Gemini API Key (free)
1. Visit https://aistudio.google.com/apikey
2. Click **"Create API Key"**
3. Copy the key → set `GOOGLE_API_KEY` in `.env`

### OpenAI API Key (alternative, paid)
1. Visit https://platform.openai.com/api-keys
2. Click **"Create new secret key"**
3. Copy the key → set `OPENAI_API_KEY` in `.env`
4. Set `MODEL=gpt-4o-mini` in `.env`

> Only one LLM provider key is needed. If both are set, OpenAI takes priority.

### Alpaca Broker API (free sandbox)
1. Sign up at https://app.alpaca.markets/signup
2. In the dashboard, generate **Broker API** keys → set `APCA_BROKER_KEY_ID` and `APCA_BROKER_SECRET_KEY`
3. Generate **Paper Trading API** keys → set `APCA_API_KEY_ID` and `APCA_API_SECRET_KEY`

> Use the Sandbox/Paper environment, not live trading.

### Alpha Vantage (free)
1. Visit https://www.alphavantage.co/support/#api-key
2. Get a free key → set `ALPHA_VANTAGE_KEY`

### NewsAPI (free)
1. Register at https://newsapi.org/register
2. Get your key → set `NEWS_KEY`

### Complete `.env` Example
```
FLASK_SECRET_KEY=your-random-secret-string

OPENAI_API_KEY=sk-...
MODEL=gpt-4o-mini
GOOGLE_API_KEY=AIzaSy...

APCA_BROKER_KEY_ID=PK...
APCA_BROKER_SECRET_KEY=...
APCA_API_KEY_ID=PK...
APCA_API_SECRET_KEY=...

ALPHA_VANTAGE_KEY=...
NEWS_KEY=...
```

---

## Running the Application

```bash
python app.py
```

1. Open http://localhost:5001 in your browser
2. Register a new account (an Alpaca sandbox brokerage account is created automatically)
3. Start chatting with the AI, browse market data, or deposit funds

---

## Features

### Chat Interface
- Conversational AI that understands financial queries
- Can execute trades through natural language ("buy 2 shares of Apple")
- Analyses news sentiment for stocks and provides BUY/SELL/HOLD recommendations
- Shows stock price charts in a modal when requested ("show me AAPL chart")
- **Force Mode**: When enabled, the AI acts immediately without asking clarifying questions
- Chat history is persisted in the database and restored on page reload

### Portfolio Management
- Real-time portfolio view with summary cards (cash, equity, P&L, buying power)
- Positions table with per-stock profit/loss
- Interactive doughnut chart showing allocation by position
- Pending orders table with one-click cancellation
- Fund deposit via simulated ACH transfer

### Market Data
- **Stock Lookup**: Search any stock by ticker, view historical price charts with configurable timeframe and period
- **NASDAQ 100**: Live list of all NASDAQ 100 stocks with current prices and daily change
- **Popular ETFs**: Curated list of 25 ETFs across major categories
- **Cryptocurrencies**: List of 20 supported crypto trading pairs

### Theme
- Dark mode (default) and light mode
- Toggle with the moon/sun button in the navbar
- Preference saved in `localStorage` and persists across sessions
- Applied before page render to prevent flash of wrong theme

---

## Authentication & Security

- **Password hashing**: User passwords are hashed with SHA-256 before storage. The database never contains plaintext passwords.
- **Session-based auth**: Flask's server-side sessions store the user's `id`. A `@login_required` decorator protects all sensitive routes.
- **API key isolation**: Alpaca broker credentials and all API keys are stored in server-side environment variables (`.env`) and never exposed to the browser.
- **Per-user scoping**: Every trading and portfolio operation uses the user's specific `alpaca_account_id` looked up from the session. Users cannot access other users' data.

---

## Database Schema

### `users` table
| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER (PK, auto-increment) | Unique user identifier |
| `username` | TEXT (unique, not null) | Login username |
| `password_hash` | TEXT (not null) | SHA-256 hash of the password |
| `alpaca_account_id` | TEXT (nullable) | Linked Alpaca brokerage account UUID |
| `alpaca_relationship_id` | TEXT (nullable) | Linked ACH bank relationship UUID |
| `created_at` | TIMESTAMP | Account creation time |

### `chat_history` table
| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER (PK, auto-increment) | Message identifier |
| `user_id` | INTEGER (FK → users.id) | Which user this message belongs to |
| `role` | TEXT (not null) | Either `"user"` or `"assistant"` |
| `content` | TEXT (not null) | The message text |
| `created_at` | TIMESTAMP | When the message was sent |

---

## Multi-Agent AI Architecture

The chat system uses a hierarchical multi-agent architecture powered by LangChain and LangGraph:

```
User Message
    │
    ▼
Master Agent (orchestrator, no tools)
    │
    ├── Query Agent        → Classifies relevance, normalises questions
    ├── News Agent         → Fetches and analyses news (uses NewsAPI tool)
    ├── Numbers Agent      → Retrieves prices, positions, market data (7 tools)
    ├── Trading Buy Agent  → Executes buy orders (stocks, ETFs, crypto)
    ├── Trading Sell Agent  → Executes sell orders, handles wash trades
    └── Chart Agent        → Generates chart commands for the frontend
```

Each sub-agent is a self-contained `CompiledSubAgent` with its own system prompt and set of tools. The master agent decides which sub-agent to invoke based on the user's request. The LangGraph checkpointer maintains conversation context so the agents can refer to previous messages within the same session.
