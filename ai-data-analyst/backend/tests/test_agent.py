"""
tests/test_agent.py — Unit Tests for LangGraph self-correcting agent
=====================================================================

PURPOSE:
  Verifies LangGraph compilation, routing pathways, validation conditions,
  and self-correction cycles (retrying on mock failures).
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
import pytest

from app.core.config import settings
from app.services.agent_service import AgentService, AgentState
from app.tools.pandas_tools import ToolResult


class TestAgentWorkflow(unittest.TestCase):

    def setUp(self):
        self.original_provider = settings.llm_provider
        self.original_model = settings.llm_model
        settings.llm_provider = "gemini"
        settings.llm_model = "gemini-2.0-flash"

        self.sample_df = pd.DataFrame({
            "category": ["Office Supplies", "Furniture", "Electronics"],
            "sales": [150.0, 350.0, 1000.0],
            "profit": [30.0, 70.0, 250.0]
        })

    def tearDown(self):
        settings.llm_provider = self.original_provider
        settings.llm_model = self.original_model

    def test_graph_compilation(self):
        """Verify that the LangGraph compiles without errors."""
        agent = AgentService(self.sample_df, "test.csv")
        assert agent.graph is not None

    def test_routing_decision(self):
        """Test decide_after_routing triggers execute node only when a tool is found."""
        agent = AgentService(self.sample_df, "test.csv")
        
        state_direct: AgentState = {
            "query": "hello",
            "file_name": "test.csv",
            "tool_name": None,
            "tool_args": None,
            "tool_result": None,
            "raw_result": None,
            "explanation": "Hello!",
            "errors": [],
            "retry_count": 0,
            "direct_response": True
        }
        assert agent.decide_after_routing(state_direct) == "direct"

        state_execute: AgentState = {
            "query": "total sales",
            "file_name": "test.csv",
            "tool_name": "get_total_sum",
            "tool_args": {"column": "sales"},
            "tool_result": None,
            "raw_result": None,
            "explanation": None,
            "errors": [],
            "retry_count": 0,
            "direct_response": False
        }
        assert agent.decide_after_routing(state_execute) == "execute"

    def test_validation_decision_success(self):
        """Test decide_after_validation routes to explain when execution succeeded."""
        agent = AgentService(self.sample_df, "test.csv")
        mock_result = ToolResult(
            success=True,
            tool_name="get_total_sum",
            result=1500.0,
            description="Total sales is 1500"
        )
        state: AgentState = {
            "query": "total sales",
            "file_name": "test.csv",
            "tool_name": "get_total_sum",
            "tool_args": {"column": "sales"},
            "tool_result": {"success": True, "result": 1500.0},
            "raw_result": mock_result,
            "explanation": None,
            "errors": [],
            "retry_count": 0,
            "direct_response": False
        }
        assert agent.decide_after_validation(state) == "explain"

    def test_validation_decision_retry(self):
        """Test decide_after_validation triggers self-correction loop when execution fails."""
        agent = AgentService(self.sample_df, "test.csv")
        mock_result = ToolResult(
            success=False,
            tool_name="get_total_sum",
            result=None,
            description="Column 'revenue' not found",
            error="Column not found"
        )
        
        # Attempt 1: should loop back to route
        state_1: AgentState = {
            "query": "total revenue",
            "file_name": "test.csv",
            "tool_name": "get_total_sum",
            "tool_args": {"column": "revenue"},
            "tool_result": None,
            "raw_result": mock_result,
            "explanation": None,
            "errors": ["Column not found"],
            "retry_count": 1,
            "direct_response": False
        }
        assert agent.decide_after_validation(state_1) == "route"

        # Attempt 3 (limit reached): should force explain
        state_3: AgentState = {
            "query": "total revenue",
            "file_name": "test.csv",
            "tool_name": "get_total_sum",
            "tool_args": {"column": "revenue"},
            "tool_result": None,
            "raw_result": mock_result,
            "explanation": None,
            "errors": ["Column not found", "Column not found", "Column not found"],
            "retry_count": 3,
            "direct_response": False
        }
        assert agent.decide_after_validation(state_3) == "explain"

    @patch("google.genai.Client")
    def test_agent_self_correction_workflow(self, mock_client_cls):
        """Verify the full agent workflow recovers from a tool error and corrects its parameters."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        # 1. First route returns an invalid tool argument (e.g. column 'revenue' instead of 'sales')
        mock_call_1 = MagicMock()
        mock_call_1.name = "get_total_sum"
        mock_call_1.args = {"column": "revenue"}
        
        mock_resp_route_1 = MagicMock()
        mock_resp_route_1.function_calls = [mock_call_1]
        mock_resp_route_1.candidates = [MagicMock()]

        # 2. Second route (after validator adds error) corrects its argument to 'sales'
        mock_call_2 = MagicMock()
        mock_call_2.name = "get_total_sum"
        mock_call_2.args = {"column": "sales"}
        
        mock_resp_route_2 = MagicMock()
        mock_resp_route_2.function_calls = [mock_call_2]
        mock_resp_route_2.candidates = [MagicMock()]

        # 3. Third response is the final text explanation summary
        mock_resp_explain = MagicMock()
        mock_resp_explain.text = "The total sales is 1,500.00."

        # Bind side effects for mock calls:
        # Route 1 -> Explain (fails and goes to Route 2) -> Route 2 -> Explain (succeeds and compiles)
        # Note: the workflow calls self.client.models.generate_content inside route_node, then explain_node.
        # Flow triggers:
        # - route_node (returns revenue) -> execute_node (fails) -> validator (retry_count=1) ->
        # - route_node (returns sales) -> execute_node (succeeds) -> validator (succeeds) ->
        # - explain_node (returns explanation)
        mock_client.models.generate_content.side_effect = [
            mock_resp_route_1, # first route attempt
            mock_resp_route_2, # second route attempt
            mock_resp_explain  # final explanation call
        ]

        agent = AgentService(self.sample_df, "test.csv")
        explanation, tool_res, errors = agent.run("What is total revenue?")

        # Assertions
        assert explanation == "The total sales is 1,500.00."
        assert len(errors) == 1
        assert "Column 'revenue' not found" in errors[0]
        assert tool_res is not None
        assert tool_res.success is True
        assert tool_res.result == 1500.0
