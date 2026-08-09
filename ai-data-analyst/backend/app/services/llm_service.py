"""
services/llm_service.py — Dual Gemini/Groq LLM Cognitive Router
================================================================

PURPOSE:
  This module acts as the "brain" of the agent in Phase 2.
  It supports both Google Gemini and Groq (Llama 3) dynamically based on the
  environment configuration (.env). It takes natural-language queries, selects
  tools, executes them, and returns business-ready responses.
"""

from __future__ import annotations

import os
import sys
import logging
import json
from typing import Any, Callable, Dict, List, Optional, Tuple
import pandas as pd

from google import genai
from google.genai import types
from google.genai.errors import APIError, ClientError

try:
    from groq import Groq
except ImportError:
    Groq = None

# Add parent directory to path to resolve imports
from pathlib import Path
_root = Path(__file__).resolve().parents[2]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from app.core.config import settings
from app.tools.pandas_tools import (
    ToolResult,
    calculate_sum,
    calculate_mean,
    calculate_min,
    calculate_max,
    calculate_count,
    group_by,
    top_n,
    filter_rows,
    time_series_aggregate,
    compare_periods,
    calculate_percentage_change,
    value_counts,
)
from app.tools.statistics_tools import (
    detect_outliers,
    calculate_correlation,
    describe_column,
    correlation_matrix,
)
from app.tools.visualization_tools import (
    plot_bar_chart,
    plot_line_chart,
    plot_pie_chart,
    plot_scatter_chart,
)
from app.tools.research_tools import web_research

logger = logging.getLogger(__name__)

# ── Module-Level Active Dataset Reference ────────────────────────────────────
_ACTIVE_DF: pd.DataFrame | None = None


# ── Custom Exceptions for CLI Fallback ────────────────────────────────────────

class LLMServiceError(Exception):
    """Base exception for LLM service issues."""
    pass


class LLMQuotaExceededError(LLMServiceError):
    """Raised when Gemini/Groq API quota or rate limit is hit."""
    pass


class LLMConnectionError(LLMServiceError):
    """Raised when offline or unable to connect to the APIs."""
    pass


# ── LLM-Callable Tool Wrapper Declarations ────────────────────────────────────

def get_total_sum(column: str) -> dict:
    """Calculate the sum total of all values in a numeric column."""
    global _ACTIVE_DF
    if _ACTIVE_DF is None:
        return {"success": False, "error": "No dataset loaded."}
    res = calculate_sum(_ACTIVE_DF, column)
    return _serialize_result(res)


def get_average_mean(column: str) -> dict:
    """Calculate the average (arithmetic mean) of a numeric column."""
    global _ACTIVE_DF
    if _ACTIVE_DF is None:
        return {"success": False, "error": "No dataset loaded."}
    res = calculate_mean(_ACTIVE_DF, column)
    return _serialize_result(res)


def get_minimum_value(column: str) -> dict:
    """Find the minimum (lowest) value in a column."""
    global _ACTIVE_DF
    if _ACTIVE_DF is None:
        return {"success": False, "error": "No dataset loaded."}
    res = calculate_min(_ACTIVE_DF, column)
    return _serialize_result(res)


def get_maximum_value(column: str) -> dict:
    """Find the maximum (highest) value in a column."""
    global _ACTIVE_DF
    if _ACTIVE_DF is None:
        return {"success": False, "error": "No dataset loaded."}
    res = calculate_max(_ACTIVE_DF, column)
    return _serialize_result(res)


def get_row_count(column: Optional[str] = None) -> dict:
    """Get the total number of records (rows) in the dataset or non-null values in a column."""
    global _ACTIVE_DF
    if _ACTIVE_DF is None:
        return {"success": False, "error": "No dataset loaded."}
    res = calculate_count(_ACTIVE_DF, column)
    return _serialize_result(res)


def group_by_analysis(group_column: str, value_column: str, agg_func: str = "sum") -> dict:
    """Group the dataset by a categorical column and aggregate a numeric column."""
    global _ACTIVE_DF
    if _ACTIVE_DF is None:
        return {"success": False, "error": "No dataset loaded."}
    res = group_by(_ACTIVE_DF, group_column, value_column, agg_func)
    return _serialize_result(res)


def top_n_analysis(group_column: str, value_column: str, n: int = 5, agg_func: str = "sum") -> dict:
    """Find the top N performing categories or groups ranked by an aggregated value."""
    global _ACTIVE_DF
    if _ACTIVE_DF is None:
        return {"success": False, "error": "No dataset loaded."}
    res = top_n(_ACTIVE_DF, group_column, value_column, n, agg_func)
    return _serialize_result(res)


def filter_data(column: str, operator: str, value: str) -> dict:
    """Filter the rows of the dataset based on a column condition."""
    global _ACTIVE_DF
    if _ACTIVE_DF is None:
        return {"success": False, "error": "No dataset loaded."}

    parsed_value: Any = value
    try:
        if "." in value:
            parsed_value = float(value)
        else:
            parsed_value = int(value)
    except ValueError:
        pass

    res = filter_rows(_ACTIVE_DF, column, operator, parsed_value)
    return _serialize_result(res)


def time_series_analysis(value_column: str, frequency: str = "ME", agg_func: str = "sum") -> dict:
    """Aggregate a numeric column over time periods (e.g. monthly sales)."""
    global _ACTIVE_DF
    if _ACTIVE_DF is None:
        return {"success": False, "error": "No dataset loaded."}

    date_col = _auto_detect_date_col(_ACTIVE_DF)
    if not date_col:
        return {"success": False, "error": "Could not identify a date column in the dataset."}

    res = time_series_aggregate(_ACTIVE_DF, date_col, value_column, frequency, agg_func)
    return _serialize_result(res)


def compare_periods_analysis(value_column: str, period1: str, period2: str, frequency: str = "ME") -> dict:
    """Compare total aggregated value between two specific time periods."""
    global _ACTIVE_DF
    if _ACTIVE_DF is None:
        return {"success": False, "error": "No dataset loaded."}

    date_col = _auto_detect_date_col(_ACTIVE_DF)
    if not date_col:
        return {"success": False, "error": "Could not identify a date column in the dataset."}

    res = compare_periods(_ACTIVE_DF, date_col, value_column, period1, period2, frequency)
    return _serialize_result(res)


def calculate_percentage_change_analysis(value_column: str, frequency: str = "ME") -> dict:
    """Calculate period-over-period percentage changes."""
    global _ACTIVE_DF
    if _ACTIVE_DF is None:
        return {"success": False, "error": "No dataset loaded."}

    date_col = _auto_detect_date_col(_ACTIVE_DF)
    if not date_col:
        return {"success": False, "error": "Could not identify a date column in the dataset."}

    res = calculate_percentage_change(_ACTIVE_DF, date_col, value_column, frequency)
    return _serialize_result(res)


def detect_outliers_analysis(column: str) -> dict:
    """Detect statistical outliers in a numeric column using the IQR method."""
    global _ACTIVE_DF
    if _ACTIVE_DF is None:
        return {"success": False, "error": "No dataset loaded."}
    res = detect_outliers(_ACTIVE_DF, column)
    return _serialize_result(res)


def calculate_correlation_analysis(column1: str, column2: str) -> dict:
    """Calculate the Pearson correlation coefficient between two numeric columns."""
    global _ACTIVE_DF
    if _ACTIVE_DF is None:
        return {"success": False, "error": "No dataset loaded."}
    res = calculate_correlation(_ACTIVE_DF, column1, column2)
    return _serialize_result(res)


def describe_column_analysis(column: str) -> dict:
    """Retrieve comprehensive descriptive statistics for a column."""
    global _ACTIVE_DF
    if _ACTIVE_DF is None:
        return {"success": False, "error": "No dataset loaded."}
    res = describe_column(_ACTIVE_DF, column)
    return _serialize_result(res)


def get_correlation_matrix() -> dict:
    """Generate the full Pearson correlation matrix for all numeric columns in the dataset."""
    global _ACTIVE_DF
    if _ACTIVE_DF is None:
        return {"success": False, "error": "No dataset loaded."}
    res = correlation_matrix(_ACTIVE_DF)
    return _serialize_result(res)


def generate_bar_chart(x_column: str, y_column: str, title: str, filename: str) -> dict:
    """Generate a premium bar chart of category (x_column) vs values (y_column) and save it as a PNG image."""
    global _ACTIVE_DF
    if _ACTIVE_DF is None:
        return {"success": False, "error": "No dataset loaded."}
    res = plot_bar_chart(_ACTIVE_DF, x_column, y_column, title, filename)
    return _serialize_result(res)


def generate_line_chart(x_column: str, y_column: str, title: str, filename: str) -> dict:
    """Generate a premium line chart of time/values (x_column) vs values (y_column) and save it as a PNG image."""
    global _ACTIVE_DF
    if _ACTIVE_DF is None:
        return {"success": False, "error": "No dataset loaded."}
    res = plot_line_chart(_ACTIVE_DF, x_column, y_column, title, filename)
    return _serialize_result(res)


def generate_pie_chart(names_column: str, values_column: str, title: str, filename: str) -> dict:
    """Generate a premium pie (or donut) chart of categories (names_column) and weights (values_column) as a PNG."""
    global _ACTIVE_DF
    if _ACTIVE_DF is None:
        return {"success": False, "error": "No dataset loaded."}
    res = plot_pie_chart(_ACTIVE_DF, names_column, values_column, title, filename)
    return _serialize_result(res)


def generate_scatter_chart(x_column: str, y_column: str, title: str, filename: str) -> dict:
    """Generate a premium scatter plot correlating x_column and y_column and save it as a PNG."""
    global _ACTIVE_DF
    if _ACTIVE_DF is None:
        return {"success": False, "error": "No dataset loaded."}
    res = plot_scatter_chart(_ACTIVE_DF, x_column, y_column, title, filename)
    return _serialize_result(res)


def web_research_tool(query: str) -> dict:
    """Search the web for additional contextual insights or market trends related to the query."""
    res = web_research(query)
    return _serialize_result(res)


# ── Helper Utilities ─────────────────────────────────────────────────────────

def _auto_detect_date_col(df: pd.DataFrame) -> str | None:
    for col in df.columns:
        if "date" in col.lower() or "time" in col.lower() or "ordered" in col.lower():
            return col
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            return col
    return None


def _serialize_result(result: ToolResult) -> dict:
    data = result.result
    if isinstance(data, pd.DataFrame):
        serialized_data = {
            "total_rows_matching": len(data),
            "columns": list(data.columns),
            "sample_records": data.head(15).to_dict(orient="records")
        }
    elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        serialized_data = data[:15]
    else:
        serialized_data = data

    return {
        "success": result.success,
        "tool_name": result.tool_name,
        "description": result.description,
        "result": serialized_data,
        "error": result.error,
    }


# ── LLM Service Class ─────────────────────────────────────────────────────────

class LLMService:
    """Cognitive routing service supporting Gemini and Groq clients dynamically."""

    def __init__(self, df: pd.DataFrame, file_name: str = "dataset"):
        self.df = df
        self.file_name = file_name
        self.provider = settings.llm_provider.lower()
        self.model = settings.llm_model
        
        # Tools definitions
        self.tools = [
            get_total_sum,
            get_average_mean,
            get_minimum_value,
            get_maximum_value,
            get_row_count,
            group_by_analysis,
            top_n_analysis,
            filter_data,
            time_series_analysis,
            compare_periods_analysis,
            calculate_percentage_change_analysis,
            detect_outliers_analysis,
            describe_column_analysis,
            get_correlation_matrix,
            generate_bar_chart,
            generate_line_chart,
            generate_pie_chart,
            generate_scatter_chart,
            web_research_tool,
        ]
        
        self._init_client()

    def _init_client(self) -> None:
        api_key = settings.require_llm_key()
        if self.provider == "gemini":
            self.client = genai.Client(api_key=api_key)
        elif self.provider == "groq":
            if Groq is None:
                raise LLMServiceError("Groq library not installed. Run pip install groq.")
            self.client = Groq(api_key=api_key)
        else:
            raise LLMServiceError(f"Unsupported LLM provider: {self.provider}")

    def _get_system_instructions(self) -> str:
        columns_desc = []
        for col in self.df.columns:
            dtype = str(self.df[col].dtype)
            sample_values = self.df[col].dropna().head(3).tolist()
            sample_str = ", ".join(repr(x) for x in sample_values)
            columns_desc.append(f"- **{col}** (type: {dtype}, examples: [{sample_str}])")

        col_str = "\n".join(columns_desc)

        return f"""You are a helpful AI Data Analyst Agent for the dataset '{self.file_name}' ({len(self.df):,} rows).
Here is the dataset schema:
{col_str}

Use the tools provided to query the dataset and answer the user's question.
If the question requires external research (such as explaining macro market trends, competitor information, or real-world events not present in the CSV dataset), use the `web_research_tool` to perform online research.
Keep your explanations professional, clear, and business-focused.
"""

    def _get_groq_tool_schemas(self) -> list[dict]:
        """Defines JSON schema declarations for Groq tool-calling."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_total_sum",
                    "description": "Calculate the sum total of all values in a numeric column.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "column": {"type": "string", "description": "The name of the column to sum (e.g. 'sales', 'profit', 'quantity')"}
                        },
                        "required": ["column"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_average_mean",
                    "description": "Calculate the average (arithmetic mean) of a numeric column.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "column": {"type": "string", "description": "The name of the column to average (e.g. 'sales', 'profit', 'quantity')"}
                        },
                        "required": ["column"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_minimum_value",
                    "description": "Find the minimum (lowest) value in a column.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "column": {"type": "string", "description": "The name of the column (e.g. 'sales', 'profit', 'quantity', 'order_date')"}
                        },
                        "required": ["column"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_maximum_value",
                    "description": "Find the maximum (highest) value in a column.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "column": {"type": "string", "description": "The name of the column (e.g. 'sales', 'profit', 'quantity', 'order_date')"}
                        },
                        "required": ["column"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_row_count",
                    "description": "Get the total number of records (rows) in the dataset or non-null values in a column.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "column": {"type": "string", "description": "Optional column name to count non-null values."}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "group_by_analysis",
                    "description": "Group the dataset by a categorical column and aggregate a numeric column.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "group_column": {"type": "string", "description": "The categorical column to group by (e.g. 'region', 'category', 'segment')"},
                            "value_column": {"type": "string", "description": "The numeric column to aggregate (e.g. 'sales', 'profit', 'quantity')"},
                            "agg_func": {"type": "string", "description": "Aggregation function: 'sum', 'mean', 'count', 'min', 'max'", "default": "sum"}
                        },
                        "required": ["group_column", "value_column"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "top_n_analysis",
                    "description": "Find the top N performing categories or groups ranked by an aggregated value.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "group_column": {"type": "string", "description": "The column to group by (e.g. 'product_name', 'customer_name', 'region')"},
                            "value_column": {"type": "string", "description": "The numeric column to rank by (e.g. 'sales', 'profit')"},
                            "n": {"type": "integer", "description": "The number of top records to return. Default is 5.", "default": 5},
                            "agg_func": {"type": "string", "description": "Aggregation function ('sum', 'mean', 'count')", "default": "sum"}
                        },
                        "required": ["group_column", "value_column"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "filter_data",
                    "description": "Filter the rows of the dataset based on a column condition.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "column": {"type": "string", "description": "The column to filter by."},
                            "operator": {"type": "string", "description": "Comparison operator: '==', '!=', '>', '>=', '<', '<=', or 'contains'."},
                            "value": {"type": "string", "description": "The value to compare against."}
                        },
                        "required": ["column", "operator", "value"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "time_series_analysis",
                    "description": "Aggregate a numeric column over time periods (e.g. monthly sales).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "value_column": {"type": "string", "description": "The numeric column to aggregate over time."},
                            "frequency": {"type": "string", "description": "Time interval: 'ME' (Monthly), 'QE' (Quarterly), 'YE' (Yearly).", "default": "ME"},
                            "agg_func": {"type": "string", "description": "Aggregation function ('sum', 'mean', 'count')", "default": "sum"}
                        },
                        "required": ["value_column"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "compare_periods_analysis",
                    "description": "Compare total aggregated value between two specific time periods.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "value_column": {"type": "string", "description": "The numeric column to compare."},
                            "period1": {"type": "string", "description": "First period (e.g., '2023-02')"},
                            "period2": {"type": "string", "description": "Second period (e.g., '2023-03')"},
                            "frequency": {"type": "string", "description": "Frequency ('ME' for Monthly).", "default": "ME"}
                        },
                        "required": ["value_column", "period1", "period2"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "calculate_percentage_change_analysis",
                    "description": "Calculate period-over-period percentage changes.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "value_column": {"type": "string", "description": "The numeric column to calculate changes for."},
                            "frequency": {"type": "string", "description": "Interval frequency ('ME' or 'QE').", "default": "ME"}
                        },
                        "required": ["value_column"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "detect_outliers_analysis",
                    "description": "Detect statistical outliers in a numeric column using the IQR method.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "column": {"type": "string", "description": "The numeric column to scan for anomalies/outliers."}
                        },
                        "required": ["column"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "calculate_correlation_analysis",
                    "description": "Calculate the Pearson correlation coefficient between two numeric columns.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "column1": {"type": "string", "description": "First numeric column."},
                            "column2": {"type": "string", "description": "Second numeric column."}
                        },
                        "required": ["column1", "column2"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "describe_column_analysis",
                    "description": "Retrieve comprehensive descriptive statistics for a column.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "column": {"type": "string", "description": "The name of the column to describe."}
                        },
                        "required": ["column"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_correlation_matrix",
                    "description": "Generate the full Pearson correlation matrix for all numeric columns in the dataset.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_bar_chart",
                    "description": "Generate a premium bar chart of category (x_column) vs values (y_column) and save it as a PNG image.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "x_column": {"type": "string", "description": "The column to plot on the X-axis (e.g. region, category)."},
                            "y_column": {"type": "string", "description": "The numeric column to plot on the Y-axis (e.g. sales, profit)."},
                            "title": {"type": "string", "description": "The title of the chart."},
                            "filename": {"type": "string", "description": "The output filename (without extension, e.g. 'sales_bar_chart')."}
                        },
                        "required": ["x_column", "y_column", "title", "filename"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_line_chart",
                    "description": "Generate a premium line chart of time/values (x_column) vs values (y_column) and save it as a PNG image.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "x_column": {"type": "string", "description": "The column to plot on the X-axis (e.g. date, month)."},
                            "y_column": {"type": "string", "description": "The numeric column to plot on the Y-axis (e.g. sales, profit)."},
                            "title": {"type": "string", "description": "The title of the chart."},
                            "filename": {"type": "string", "description": "The output filename (without extension, e.g. 'sales_line_chart')."}
                        },
                        "required": ["x_column", "y_column", "title", "filename"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_pie_chart",
                    "description": "Generate a premium pie (or donut) chart of categories (names_column) and weights (values_column) as a PNG.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "names_column": {"type": "string", "description": "The column containing category names."},
                            "values_column": {"type": "string", "description": "The numeric column containing weight values."},
                            "title": {"type": "string", "description": "The title of the chart."},
                            "filename": {"type": "string", "description": "The output filename (without extension, e.g. 'sales_pie_chart')."}
                        },
                        "required": ["names_column", "values_column", "title", "filename"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_scatter_chart",
                    "description": "Generate a premium scatter plot correlating x_column and y_column and save it as a PNG.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "x_column": {"type": "string", "description": "The numeric X column."},
                            "y_column": {"type": "string", "description": "The numeric Y column."},
                            "title": {"type": "string", "description": "The title of the chart."},
                            "filename": {"type": "string", "description": "The output filename (without extension, e.g. 'sales_scatter_chart')."}
                        },
                        "required": ["x_column", "y_column", "title", "filename"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "web_research_tool",
                    "description": "Search the web for additional contextual insights or market trends related to the query.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "The search query to execute (e.g. 'why did product sales drop in march 2026')."}
                        },
                        "required": ["query"]
                    }
                }
            }
        ]

    def ask(self, query: str) -> Tuple[Optional[str], Optional[ToolResult]]:
        """Sends query to selected provider, routes function call, and returns answers."""
        global _ACTIVE_DF
        _ACTIVE_DF = self.df

        if self.provider == "gemini":
            return self._ask_gemini(query)
        elif self.provider == "groq":
            return self._ask_groq(query)
        else:
            raise LLMServiceError(f"Unsupported provider: {self.provider}")

    def _ask_gemini(self, query: str) -> Tuple[Optional[str], Optional[ToolResult]]:
        config = types.GenerateContentConfig(
            tools=self.tools,
            system_instruction=self._get_system_instructions(),
            temperature=0.0,
        )
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=query,
                config=config,
            )

            if response.function_calls:
                call = response.function_calls[0]
                tool_name = call.name
                arguments = call.args

                logger.info(f"Gemini routing to: {tool_name} with: {arguments}")
                func_map = {f.__name__: f for f in self.tools}
                wrapper_func = func_map.get(tool_name)

                if not wrapper_func:
                    return f"Error: Tool '{tool_name}' not found.", None

                tool_output = wrapper_func(**arguments)
                raw_result = self._execute_real_tool(tool_name, arguments)

                follow_up_content = [
                    types.Content(role="user", parts=[types.Part.from_text(text=query)]),
                    response.candidates[0].content,
                    types.Content(role="tool", parts=[
                        types.Part.from_function_response(
                            name=tool_name,
                            response={"result": tool_output}
                        )
                    ])
                ]

                final_response = self.client.models.generate_content(
                    model=self.model,
                    contents=follow_up_content,
                    config=config,
                )
                return final_response.text, raw_result

            return response.text, None

        except APIError as e:
            if e.code == 429:
                raise LLMQuotaExceededError("Gemini API Quota limits exceeded.") from e
            raise LLMServiceError(f"Gemini API Error: {e.message}") from e
        except ClientError as e:
            if "quota" in str(e).lower() or "429" in str(e):
                raise LLMQuotaExceededError("Gemini API Quota limits exceeded.") from e
            raise LLMServiceError(f"Gemini Client Error: {e}") from e
        except Exception as e:
            err_str = str(e).lower()
            if "getaddrinfo" in err_str or "connection" in err_str or "offline" in err_str:
                raise LLMConnectionError("DNS or network connection error to Gemini API.") from e
            raise LLMServiceError(f"Unexpected Gemini Service Exception: {e}") from e

    def _ask_groq(self, query: str) -> Tuple[Optional[str], Optional[ToolResult]]:
        try:
            system_instruction = self._get_system_instructions()
            messages = [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": query}
            ]

            # Initial call with tool declarations
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self._get_groq_tool_schemas(),
                tool_choice="auto",
                temperature=0.0
            )

            message = response.choices[0].message
            if message.tool_calls:
                # Groq requested a function call
                messages.append(message)
                
                tool_call = message.tool_calls[0]
                tool_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)

                logger.info(f"Groq routing to: {tool_name} with: {arguments}")
                func_map = {f.__name__: f for f in self.tools}
                wrapper_func = func_map.get(tool_name)

                if not wrapper_func:
                    return f"Error: Tool '{tool_name}' not found.", None

                # Execute local wrapper & build output
                tool_output = wrapper_func(**arguments)
                raw_result = self._execute_real_tool(tool_name, arguments)

                # Send tool response block back to Groq
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": json.dumps(tool_output)
                })

                # Follow-up completion for final business explanation
                final_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.0
                )
                return final_response.choices[0].message.content, raw_result

            return message.content, None

        except Exception as e:
            err_str = str(e).lower()
            if "429" in err_str or "rate_limit" in err_str:
                raise LLMQuotaExceededError("Groq API rate limit or quota exceeded.") from e
            if "getaddrinfo" in err_str or "connection" in err_str or "offline" in err_str:
                raise LLMConnectionError("DNS or network connection error to Groq API.") from e
            raise LLMServiceError(f"Unexpected Groq Service Exception: {e}") from e

    def _execute_real_tool(self, wrapper_name: str, args: dict) -> ToolResult:
        try:
            if wrapper_name == "get_total_sum":
                return calculate_sum(self.df, args["column"])
            elif wrapper_name == "get_average_mean":
                return calculate_mean(self.df, args["column"])
            elif wrapper_name == "get_minimum_value":
                return calculate_min(self.df, args["column"])
            elif wrapper_name == "get_maximum_value":
                return calculate_max(self.df, args["column"])
            elif wrapper_name == "get_row_count":
                return calculate_count(self.df, args.get("column"))
            elif wrapper_name == "group_by_analysis":
                return group_by(self.df, args["group_column"], args["value_column"], args.get("agg_func", "sum"))
            elif wrapper_name == "top_n_analysis":
                return top_n(self.df, args["group_column"], args["value_column"], args.get("n", 5), args.get("agg_func", "sum"))
            elif wrapper_name == "filter_data":
                val = args["value"]
                try:
                    val = float(val) if "." in str(val) else int(val)
                except ValueError:
                    pass
                return filter_rows(self.df, args["column"], args["operator"], val)
            elif wrapper_name == "time_series_analysis":
                date_col = _auto_detect_date_col(self.df)
                return time_series_aggregate(self.df, date_col, args["value_column"], args.get("frequency", "ME"), args.get("agg_func", "sum"))
            elif wrapper_name == "compare_periods_analysis":
                date_col = _auto_detect_date_col(self.df)
                return compare_periods(self.df, date_col, args["value_column"], args["period1"], args["period2"], args.get("frequency", "ME"))
            elif wrapper_name == "calculate_percentage_change_analysis":
                date_col = _auto_detect_date_col(self.df)
                return calculate_percentage_change(self.df, date_col, args["value_column"], args.get("frequency", "ME"))
            elif wrapper_name == "detect_outliers_analysis":
                return detect_outliers(self.df, args["column"])
            elif wrapper_name == "calculate_correlation_analysis":
                return calculate_correlation(self.df, args["column1"], args["column2"])
            elif wrapper_name == "describe_column_analysis":
                return describe_column(self.df, args["column"])
            elif wrapper_name == "get_correlation_matrix":
                return correlation_matrix(self.df)
            elif wrapper_name == "generate_bar_chart":
                return plot_bar_chart(self.df, args["x_column"], args["y_column"], args["title"], args["filename"])
            elif wrapper_name == "generate_line_chart":
                return plot_line_chart(self.df, args["x_column"], args["y_column"], args["title"], args["filename"])
            elif wrapper_name == "generate_pie_chart":
                return plot_pie_chart(self.df, args["names_column"], args["values_column"], args["title"], args["filename"])
            elif wrapper_name == "generate_scatter_chart":
                return plot_scatter_chart(self.df, args["x_column"], args["y_column"], args["title"], args["filename"])
            elif wrapper_name == "web_research_tool":
                return web_research(args["query"])
        except Exception as e:
            return ToolResult(
                success=False,
                tool_name=wrapper_name,
                result=None,
                description=f"Error executing real tool: {e}",
                error=str(e),
            )
        return ToolResult(
            success=False,
            tool_name=wrapper_name,
            result=None,
            description="Unknown tool execution name.",
            error=f"Could not map tool name '{wrapper_name}'",
        )
