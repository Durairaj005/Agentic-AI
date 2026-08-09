import unittest
from unittest.mock import patch, MagicMock
from app.tools.research_tools import web_research
from app.core.config import settings

class TestResearchTools(unittest.TestCase):
    
    @patch("app.core.config.settings.tavily_api_key", None)
    def test_web_research_mock_fallback(self):
        """Test that web_research returns mock data when API key is missing."""
        result = web_research("What is the competitor landscape of retail?")
        self.assertTrue(result.success)
        self.assertEqual(result.tool_name, "web_research")
        self.assertIn("MOCKED", result.description)
        self.assertIsNotNone(result.result)
        self.assertIn("results", result.result)
        self.assertIn("answer", result.result)

    @patch("app.core.config.settings.tavily_api_key", "test-api-key")
    @patch("urllib.request.urlopen")
    def test_web_research_api_success(self, mock_urlopen):
        """Test that web_research successfully calls Tavily API and parses JSON response."""
        # Mock Response object
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"results": [{"title": "Live Market Data", "url": "https://live.com", "content": "Live search content"}], "answer": "Live answer"}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = web_research("Who won the 2026 World Cup?")
        
        self.assertTrue(result.success)
        self.assertEqual(result.tool_name, "web_research")
        self.assertIsNotNone(result.result)
        self.assertEqual(result.result["answer"], "Live answer")
        self.assertEqual(len(result.result["results"]), 1)
        self.assertEqual(result.result["results"][0]["title"], "Live Market Data")

    @patch("app.core.config.settings.tavily_api_key", "test-api-key")
    @patch("urllib.request.urlopen")
    def test_web_research_api_failure(self, mock_urlopen):
        """Test that web_research handles network/HTTP errors gracefully."""
        from urllib.error import URLError
        mock_urlopen.side_effect = URLError("DNS resolution failure")

        result = web_research("Who won the 2026 World Cup?")
        
        self.assertFalse(result.success)
        self.assertIn("DNS resolution failure", result.error)
        self.assertIsNone(result.result)
