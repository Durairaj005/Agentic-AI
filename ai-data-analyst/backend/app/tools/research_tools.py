import urllib.request
import urllib.error
import json
import logging
from app.tools.pandas_tools import ToolResult
from app.core.config import settings

logger = logging.getLogger(__name__)

def web_research(query: str) -> ToolResult:
    """
    Search the web using the Tavily Search API.
    If the API key is not configured, returns a simulated mock response.
    """
    if not settings.tavily_api_key:
        logger.warning("TAVILY_API_KEY is not set. Returning a mock search response.")
        # Return mock results for demo/development purposes
        mock_data = {
            "query": query,
            "results": [
                {
                    "title": f"Market analysis matching query: {query}",
                    "url": "https://example.com/mock-report",
                    "content": "This is a simulated search result. In production, setting TAVILY_API_KEY will connect to live search index for current web information."
                }
            ],
            "answer": "This is a mock answer summarizing market findings for the development environment since no Tavily API Key is configured."
        }
        return ToolResult(
            success=True,
            tool_name="web_research",
            result=mock_data,
            description=f"Executed web research query: '{query}' (MOCKED)",
            error=None
        )

    url = "https://api.tavily.com/search"
    payload = {
        "api_key": settings.tavily_api_key,
        "query": query,
        "search_depth": "basic",
        "include_answer": True,
        "max_results": 5
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return ToolResult(
                success=True,
                tool_name="web_research",
                result=res_data,
                description=f"Successfully executed web research query: '{query}'",
                error=None
            )
    except urllib.error.URLError as e:
        logger.error(f"Tavily API call failed: {e}")
        return ToolResult(
            success=False,
            tool_name="web_research",
            result=None,
            description="Tavily web search request failed.",
            error=str(e)
        )
