"""
tests/test_llm_service.py — Unit Tests for Gemini LLM Service
==============================================================

PURPOSE:
  Verifies that the LLMService correctly handles dataset descriptions,
  tool schemas, tool executions, and graceful fallback errors (429/offline).
  Mocks the new `google-genai` SDK to run offline without hitting real quotas.
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np
import pytest

from app.core.config import settings
from app.services.llm_service import (
    LLMService,
    LLMServiceError,
    LLMQuotaExceededError,
    LLMConnectionError,
    get_total_sum,
    get_average_mean,
    _ACTIVE_DF,
)
from app.tools.pandas_tools import ToolResult
from google.genai.errors import APIError


class TestLLMService(unittest.TestCase):

    def setUp(self):
        # Override settings for tests to use gemini deterministically
        self.original_provider = settings.llm_provider
        self.original_model = settings.llm_model
        settings.llm_provider = "gemini"
        settings.llm_model = "gemini-2.0-flash"
        
        # Create a tiny test dataset
        self.sample_df = pd.DataFrame({
            "category": ["Office Supplies", "Furniture", "Electronics"],
            "sales": [150.0, 350.0, 1000.0],
            "profit": [30.0, 70.0, 250.0],
            "quantity": [3, 2, 5],
            "order_date": pd.to_datetime(["2023-01-15", "2023-02-18", "2023-03-22"])
        })

    def tearDown(self):
        # Restore settings
        settings.llm_provider = self.original_provider
        settings.llm_model = self.original_model

    def test_system_instructions_generation(self):
        """Verify that the system instructions correctly describe the dataset schema."""
        service = LLMService(self.sample_df, "test_sales.csv")
        instructions = service._get_system_instructions()
        
        assert "test_sales.csv" in instructions
        assert "sales" in instructions
        assert "category" in instructions
        assert "order_date" in instructions
        assert "3 rows" in instructions

    @patch("google.genai.Client")
    def test_serialize_result_dataframe(self, mock_client_cls):
        """Verify that _serialize_result safely serializes DataFrames into lists of dicts."""
        service = LLMService(self.sample_df, "test.csv")
        res = ToolResult(
            success=True,
            tool_name="filter_rows",
            result=self.sample_df.copy(),
            description="Filtered rows successfully"
        )
        
        serialized = service._execute_real_tool("get_row_count", {})
        assert serialized.success is True
        assert serialized.result == 3

    @patch("google.genai.Client")
    def test_ask_direct_response(self, mock_client_cls):
        """Verify LLMService.ask returns text directly if the LLM doesn't call a function."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        
        # Mock Gemini direct response
        mock_response = MagicMock()
        mock_response.function_calls = None
        mock_response.text = "Hello! I am ready to analyze your sales data."
        mock_client.models.generate_content.return_value = mock_response
        
        service = LLMService(self.sample_df, "test.csv")
        text, tool_res = service.ask("Hello there")
        
        assert text == "Hello! I am ready to analyze your sales data."
        assert tool_res is None

    @patch("google.genai.Client")
    def test_ask_with_function_calling(self, mock_client_cls):
        """Verify LLMService.ask intercepts a function call, executes it, and gets follow-up answer."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        
        # First call return value (mocking Gemini tool call request)
        mock_call = MagicMock()
        mock_call.name = "get_total_sum"
        mock_call.args = {"column": "sales"}
        
        mock_resp_1 = MagicMock()
        mock_resp_1.function_calls = [mock_call]
        mock_resp_1.candidates = [MagicMock()]
        
        # Second call return value (final text synthesis after tool execution)
        mock_resp_2 = MagicMock()
        mock_resp_2.text = "The total sales sum is 1,500.00."
        
        mock_client.models.generate_content.side_effect = [mock_resp_1, mock_resp_2]
        
        service = LLMService(self.sample_df, "test.csv")
        text, tool_res = service.ask("What is total sales?")
        
        # Should have invoked the real tool calculate_sum and returned full ToolResult
        assert text == "The total sales sum is 1,500.00."
        assert tool_res is not None
        assert tool_res.success is True
        assert tool_res.result == 1500.0
        
        # Verify mock_client made two calls to generate_content
        assert mock_client.models.generate_content.call_count == 2

    @patch("google.genai.Client")
    def test_quota_exceeded_error_handling(self, mock_client_cls):
        """Verify that a 429 APIError from the Gemini client is wrapped into LLMQuotaExceededError."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        
        # Create a mock APIError for rate limit (429 status code)
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_api_err = APIError(429, {"message": "Resource Exhausted"}, mock_response)
        
        mock_client.models.generate_content.side_effect = mock_api_err
        
        service = LLMService(self.sample_df, "test.csv")
        
        with pytest.raises(LLMQuotaExceededError):
            service.ask("total sales")

    @patch("google.genai.Client")
    def test_connection_error_handling(self, mock_client_cls):
        """Verify that network dns lookup exceptions are wrapped into LLMConnectionError."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        
        mock_client.models.generate_content.side_effect = Exception("getaddrinfo failed: offline")
        
        service = LLMService(self.sample_df, "test.csv")
        
        with pytest.raises(LLMConnectionError):
            service.ask("total sales")
