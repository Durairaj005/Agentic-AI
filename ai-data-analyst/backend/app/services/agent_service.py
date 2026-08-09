"""
services/agent_service.py — Self-Correcting LangGraph Agent
============================================================

PURPOSE:
  This module implements the LangGraph state machine workflow:
  Router Node -> Executor Node -> Validator Node -> Explain Node.
  If a tool call fails, the Validator routes back to the Router with error
  feedback for self-correction (retrying up to 3 times).
"""

from __future__ import annotations
from google import genai
from google.genai import types
from google.genai.errors import APIError, ClientError
import logging
import json
from typing import Any, Dict, List, Literal, Optional, TypedDict
import pandas as pd

from langgraph.graph import StateGraph, START, END

# Import central tools and configs
from app.services.llm_service import (
    LLMService,
    LLMServiceError,
    LLMQuotaExceededError,
    LLMConnectionError,
)
from app.tools.pandas_tools import ToolResult

logger = logging.getLogger(__name__)


# ── LangGraph Agent State Definition ──────────────────────────────────────────

class AgentState(TypedDict):
    """Represents the state of our analytical query execution loop."""
    query: str
    file_name: str
    tool_name: Optional[str]
    tool_args: Optional[dict]
    tool_result: Optional[dict]
    raw_result: Optional[ToolResult]
    explanation: Optional[str]
    errors: List[str]
    retry_count: int
    direct_response: bool


# ── Agent Service Class ───────────────────────────────────────────────────────

class AgentService:
    """Orchestrates the LangGraph execution loop for data analysis queries."""

    def __init__(self, df: pd.DataFrame, file_name: str = "dataset"):
        self.df = df
        self.file_name = file_name
        self.llm = LLMService(df, file_name)
        self.graph = self._compile_graph()

    def _compile_graph(self) -> StateGraph:
        """Constructs and compiles the self-correcting StateGraph workflow."""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("router", self.route_node)
        workflow.add_node("executor", self.execute_node)
        workflow.add_node("validator", self.validate_node)
        workflow.add_node("explain", self.explain_node)

        # Set entry point
        workflow.add_edge(START, "router")

        # Routing decisions from Router node
        workflow.add_conditional_edges(
            "router",
            self.decide_after_routing,
            {
                "execute": "executor",
                "direct": "explain"
            }
        )

        # Executor proceeds to validation
        workflow.add_edge("executor", "validator")

        # Validator conditional self-correcting routing
        workflow.add_conditional_edges(
            "validator",
            self.decide_after_validation,
            {
                "route": "router",
                "explain": "explain"
            }
        )

        # Explainer node finishes the run
        workflow.add_edge("explain", END)

        return workflow.compile()

    # ── Node Actions ──────────────────────────────────────────────────────────

    def route_node(self, state: AgentState) -> dict:
        """Determines the appropriate tool call using the LLM and previous error logs."""
        query = state["query"]
        retry_count = state["retry_count"]
        errors = state["errors"]

        logger.info(f"Agent routing node (Attempt {retry_count + 1})...")

        # Construct prompt, incorporating previous error feedback for self-correction
        system_instruction = self.llm._get_system_instructions()
        if errors:
            system_instruction += f"\n\n[WARNING: PREVIOUS ATTEMPT FAILED]\n" \
                                  f"Your previous attempt to call a tool failed with the following error:\n" \
                                  f"-> '{errors[-1]}'\n" \
                                  f"Please analyze this error, choose a different tool or modify the arguments (check column names/values), and try again. Do not repeat the same mistake."

        # Configure LLM Client call
        if self.llm.provider == "gemini":
            config = {
                "tools": self.llm.tools,
                "system_instruction": system_instruction,
                "temperature": 0.0,
            }
            try:
                response = self.llm.client.models.generate_content(
                    model=self.llm.model,
                    contents=query,
                    config=config,
                )

                if response.function_calls:
                    call = response.function_calls[0]
                    return {
                        "tool_name": call.name,
                        "tool_args": call.args,
                        "direct_response": False
                    }
                return {
                    "explanation": response.text,
                    "tool_name": None,
                    "tool_args": None,
                    "direct_response": True
                }
            except Exception as e:
                raise self._handle_llm_exception(e)
        
        elif self.llm.provider == "groq":
            try:
                messages = [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": query}
                ]
                response = self.llm.client.chat.completions.create(
                    model=self.llm.model,
                    messages=messages,
                    tools=self.llm._get_groq_tool_schemas(),
                    tool_choice="auto",
                    temperature=0.0
                )
                message = response.choices[0].message
                if message.tool_calls:
                    tool_call = message.tool_calls[0]
                    import json
                    return {
                        "tool_name": tool_call.function.name,
                        "tool_args": json.loads(tool_call.function.arguments),
                        "direct_response": False
                    }
                return {
                    "explanation": message.content,
                    "tool_name": None,
                    "tool_args": None,
                    "direct_response": True
                }
            except Exception as e:
                raise self._handle_llm_exception(e)
        
        return {"direct_response": True, "explanation": "Unsupported LLM Provider."}

    def execute_node(self, state: AgentState) -> dict:
        """Executes the selected analytical tool locally."""
        tool_name = state["tool_name"]
        tool_args = state["tool_args"]

        logger.info(f"Agent executing tool node: {tool_name} with args: {tool_args}")

        if not tool_name:
            return {"raw_result": None, "tool_result": None}

        # Invoke tool locally
        raw_result = self.llm._execute_real_tool(tool_name, tool_args)
        serialized_output = self.llm.tools[[f.__name__ for f in self.llm.tools].index(tool_name)](**tool_args)

        return {
            "raw_result": raw_result,
            "tool_result": serialized_output
        }

    def validate_node(self, state: AgentState) -> dict:
        """Inspects the execution outcome and logs any failures for self-correction."""
        raw_res = state["raw_result"]
        retry_count = state["retry_count"]
        errors = state["errors"]

        logger.info("Agent validation node checking execution outcome...")

        if raw_res is None:
            return {}

        if raw_res.success:
            logger.info("Tool validation: SUCCESS ✅")
            return {}

        # Log validation failure
        error_msg = raw_res.error or raw_res.description
        logger.warning(f"Tool validation: FAILED ❌ (Attempt {retry_count + 1}) - Error: {error_msg}")
        
        return {
            "errors": errors + [error_msg],
            "retry_count": retry_count + 1
        }

    def explain_node(self, state: AgentState) -> dict:
        """Generates the final natural language summary response."""
        query = state["query"]
        tool_name = state["tool_name"]
        tool_result = state["tool_result"]
        direct_response = state["direct_response"]
        errors = state["errors"]

        logger.info("Agent explanation node compiling response...")

        # If a direct response was already formulated or we had too many errors
        if direct_response:
            return {}

        if errors and not tool_result:
            return {
                "explanation": f"I tried to analyze your question, but encountered errors: {', '.join(errors)}. Please try rephrasing your request."
            }

        # Call Gemini/Groq follow-up to compile explanation
        system_instruction = self.llm._get_system_instructions()

        if self.llm.provider == "gemini":
            config = {
                "system_instruction": system_instruction,
                "temperature": 0.0,
            }
            # Reconstruct content blocks
            follow_up_content = [
                types.Content(role="user", parts=[types.Part.from_text(text=query)]),
                # Mock LLM tool call request
                types.Content(role="model", parts=[
                    types.Part.from_function_call(name=tool_name, args=state["tool_args"])
                ]),
                types.Content(role="tool", parts=[
                    types.Part.from_function_response(
                        name=tool_name,
                        response={"result": tool_result}
                    )
                ])
            ]
            try:
                response = self.llm.client.models.generate_content(
                    model=self.llm.model,
                    contents=follow_up_content,
                    config=config,
                )
                return {"explanation": response.text}
            except Exception as e:
                raise LLMServiceError(f"Gemini explanation error: {e}")

        elif self.llm.provider == "groq":
            try:
                messages = [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": query},
                    # Mock assistant tool request
                    {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [{
                            "id": "call_mock",
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "arguments": json.dumps(state["tool_args"])
                            }
                        }]
                    },
                    # Tool result response
                    {
                        "role": "tool",
                        "tool_call_id": "call_mock",
                        "name": tool_name,
                        "content": json.dumps(tool_result)
                    }
                ]
                response = self.llm.client.chat.completions.create(
                    model=self.llm.model,
                    messages=messages,
                    temperature=0.0
                )
                return {"explanation": response.choices[0].message.content}
            except Exception as e:
                raise LLMServiceError(f"Groq explanation error: {e}")

        return {"explanation": "Unsupported LLM Provider."}

    # ── Conditional Routing Decisions ─────────────────────────────────────────

    def decide_after_routing(self, state: AgentState) -> Literal["execute", "direct"]:
        """Decides whether to execute a tool or proceed directly to explanation."""
        if state["direct_response"]:
            return "direct"
        return "execute"

    def decide_after_validation(self, state: AgentState) -> Literal["route", "explain"]:
        """Controls the self-correcting cycle loops."""
        raw_res = state["raw_result"]
        retry_count = state["retry_count"]

        # Successful tool run proceeds to explainer
        if raw_res is None or raw_res.success:
            return "explain"

        # If we failed but have remaining retries, go back to route node
        if retry_count < 3:
            logger.info(f"Self-correction loop triggered! Retry count: {retry_count}/3")
            return "route"

        # Stop loop on maximum retries and describe errors
        logger.warning(f"Self-correction limit hit ({retry_count}/3). Finalizing explanation...")
        return "explain"

    # ── Execution Entry Point ─────────────────────────────────────────────────

    def run(self, query: str) -> tuple[Optional[str], Optional[ToolResult], list[str]]:
        """
        Runs the compiled LangGraph workflow against the user query.

        Returns:
            tuple: (final_text_response, raw_executed_tool_result_if_any, list_of_correcting_errors)
        """
        # Bind active DataFrame reference to support module-level wrappers
        from app.services import llm_service
        llm_service._ACTIVE_DF = self.df

        # Define initial state
        initial_state: AgentState = {
            "query": query,
            "file_name": self.file_name,
            "tool_name": None,
            "tool_args": None,
            "tool_result": None,
            "raw_result": None,
            "explanation": None,
            "errors": [],
            "retry_count": 0,
            "direct_response": False
        }

        # Run StateGraph
        try:
            final_state = self.graph.invoke(initial_state)
            return (
                final_state.get("explanation"),
                final_state.get("raw_result"),
                final_state.get("errors", [])
            )
        except Exception as e:
            # Let CLI catch rate limit wrapping from lower level
            raise e

    def _handle_llm_exception(self, e: Exception) -> Exception:
        """Translates external client or connection errors to standard service exceptions."""
        err_str = str(e).lower()
        if "429" in err_str or "rate_limit" in err_str:
            return LLMQuotaExceededError(f"API Quota limit exceeded: {e}")
        if "getaddrinfo" in err_str or "connection" in err_str or "offline" in err_str:
            return LLMConnectionError(f"API Connection error: {e}")
        return LLMServiceError(f"LLM API Error: {e}")
