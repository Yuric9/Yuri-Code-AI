"""Optional Tavily-backed research with durable source history."""
from __future__ import annotations

import os

from .database import log_research


def research(query: str, max_results: int | None = None) -> list[dict]:
    """Search the web when Tavily is configured; otherwise return an explicit unavailable state."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return [{"status": "unavailable", "reason": "TAVILY_API_KEY não configurada"}]
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=api_key)
        kwargs = {"search_depth": os.getenv("TAVILY_SEARCH_DEPTH", "advanced"), "include_answer": True}
        if max_results is not None:
            kwargs["max_results"] = max_results
        response = client.search(query, **kwargs)
    except Exception as exc:
        return [{"status": "error", "reason": str(exc)}]
    results = response.get("results", [])
    for item in results:
        url = item.get("url")
        text = item.get("content") or item.get("snippet") or ""
        log_research(query, url, text)
    return results
