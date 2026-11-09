# Trading Assistant – multi-agent AI for a simulated portfolio

A full-stack Flask web app in which users manage a paper-trading portfolio (stocks, ETFs, crypto) through a conversational AI assistant. It was built for the Web and Cloud Computing course at Nova SBE.

## At a glance

| | |
|---|---|
| **Goal** | Let users ask market questions, analyse their portfolio and place or cancel orders in natural language, safely, in a sandbox brokerage account. |
| **Data** | Live market data and account data from the Alpaca Broker and Data APIs (sandbox), Alpha Vantage price data, NewsAPI headlines, and per-user chat history in SQLite. |
| **Methods** | Hierarchical multi-agent system (LangChain / LangGraph): a master agent routes each request to specialised sub-agents for query classification, news analysis, numbers and market data, buying, selling and chart generation, each with its own tools · session-based authentication · three-tier architecture (frontend, Flask API, logic and integration layer). |
| **Results** | A working prototype with chat-driven trading, a portfolio view with positions, cash, equity and an allocation chart, market browsing for the NASDAQ 100, popular ETFs and crypto, and simulated ACH deposits. No real money is involved. |
| **Tech stack** | Python · Flask · LangChain · LangGraph · OpenAI or Google Gemini · Alpaca API · Alpha Vantage · NewsAPI · SQLite · JavaScript / HTML / CSS |

Full documentation, including the architecture, the file-by-file descriptions, setup and the database schema, is in [`trading_app/README.md`](trading_app/README.md).

## Quick start

```bash
cd trading_app
pip install -r requirements.txt
cp .env.example .env   # add your own sandbox/API keys
python app.py
```

## My contribution
This was a team course project. I wrote the complete application myself: the Flask backend, the multi-agent AI layer, the API integrations, the frontend and the documentation. This repository contains my code with its original commit; the team's course repository is private.
