"""Tool: Get financial news about a company or topic."""

import os
from newsapi import NewsApiClient
from langchain.tools import tool


@tool("get_news", description="Searches for news about the given company or topic")
def get_news(comp: str) -> dict:
    """
    Returns recent news articles about a given topic.
    """
    newsapi = NewsApiClient(api_key=os.getenv("NEWS_KEY"))

    data = newsapi.get_everything(
        q=comp,
        sort_by="relevancy",
        language="en",
    )

    return {
        "status": data.get("status"),
        "totalResults": data.get("totalResults"),
        "articles": [
            {
                "title": a.get("title"),
                "description": a.get("description"),
                "url": a.get("url"),
                "source": a.get("source", {}).get("name"),
            }
            for a in data.get("articles", [])
        ],
    }
