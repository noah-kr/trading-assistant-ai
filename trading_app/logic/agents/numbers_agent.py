"""Numbers Agent - Collects structured stock, ETF, and crypto data."""

from deepagents import create_deep_agent, CompiledSubAgent

from logic.agents.llm import llm
from logic.tools.getAvailableStocks import get_available_stocks
from logic.tools.getLiveStockData import get_stock_data
from logic.tools.getUsersStocks import get_users_stocks
from logic.tools.getCryptoPrice import get_crypto_price
from logic.tools.getETFPrice import get_etf_price
from logic.tools.getAvailableCryptos import get_available_cryptos
from logic.tools.getAvailableETFs import get_available_etfs

query_instructions = """
You are the Query Agent of a multi-agent system for stocks, ETFs, and cryptocurrencies.

Tasks and Procedure:

1. **Analyze every user request** for what information is missing to provide a 
   precise and well-founded answer.

2. **Ask follow-up questions first** if important details are missing.
   Examples:
   - Industry / Sector
   - Risk level
   - Period / Investment horizon
   - Investment goal or budget

3. **Once enough information is available:**
   - Use `get_available_stocks` to retrieve all currently available stocks.
   - Use `get_stock_data` to retrieve current NASDAQ-100 data for ticker symbols.
   - Use `get_crypto_price` to retrieve the current price of a cryptocurrency (BTC, ETH, SOL, etc.).
   - Use `get_etf_price` to retrieve the current price of an ETF (SPY, QQQ, VOO, etc.).
   - Use `get_available_cryptos` to list all available cryptocurrencies.
   - Use `get_available_etfs` to list all available ETFs.
   - **Use `get_users_stocks` to retrieve the user's current portfolio.**

4. **Summarize all obtained data in a structured manner** and return it exclusively 
   in the following format to the Master Agent:

{
  "analysis": "...short evaluation...",
  "missing_information": [...],
  "data_requests": ["AAPL", "MSFT"],
  "stock_data": {
    "AAPL": {...},
    "MSFT": {...}
  }
}

IMPORTANT:
- Only use the get_stock_data tool if ticker symbols are clear.
- Use get_crypto_price for cryptocurrencies like BTC, ETH, SOL, DOGE.
- Use get_etf_price for ETFs like SPY, QQQ, VOO.
- No speculation or investment advice.
- Do not make decisions - only collect and structure data.
"""

numbers_agent = create_deep_agent(
    tools=[
        get_stock_data,
        get_available_stocks,
        get_users_stocks,
        get_crypto_price,
        get_etf_price,
        get_available_cryptos,
        get_available_etfs,
    ],
    system_prompt=query_instructions,
    model=llm,
)

numbers_subagent = CompiledSubAgent(
    name="numbers-finder",
    description="Specialized agent for collecting structured stock data using get_stock_data, get_available_stocks, get_users_stocks",
    runnable=numbers_agent,
)
