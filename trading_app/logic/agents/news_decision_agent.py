"""News Decision Agent - Fetches and analyzes financial news."""

from deepagents import create_deep_agent, CompiledSubAgent

from logic.agents.llm import llm
from logic.tools.getNews import get_news

research_instructions = """
You are an expert stock broker. Your job is to research a company and then clearly recommend one of the 
following actions at the very beginning of your answer:

Think about the most relevant news and think about each news consequence for the company stock.

You can use the internet search tool to gather recent news and market context.

## Example format:
BUY — Apple shows strong earnings growth and steady demand for its new products.

Use this format for every response.
"""

news_agent = create_deep_agent(
    tools=[get_news],
    system_prompt=research_instructions,
    model=llm,
)

news_subagent = CompiledSubAgent(
    name="web-searcher",
    description="Specialized agent for gathering news using the tools",
    runnable=news_agent,
)
