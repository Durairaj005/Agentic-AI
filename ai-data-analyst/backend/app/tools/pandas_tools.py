"""
tools/pandas_tools.py — Deterministic Pandas Analysis Tools
============================================================

PURPOSE:
  These are the "hands" of the AI agent — the actual computation happens here.
  The LLM (Phase 2+) will decide WHICH tool to call and with WHAT arguments.
  Python/Pandas does the actual work.

DESIGN PRINCIPLE — "LLM reasons, Python computes":
  ✗ Wrong:  LLM calculates "March revenue is ₹4,23,000"
  ✓ Right:  LLM says "call calculate_sum(df, 'sales', filter_month='March')"
            → Python returns ₹4,23,000
            → LLM explains the result

WHY TYPED RETURN OBJECTS:
  Every tool returns a ToolResult dataclass, not a raw value.
  This lets the Validation Agent (Phase 3) check:
    • Did it succeed? (success=True/False)
    • What was the result?
    • What operation was performed?
  And lets the LLM understand the result without re-calculating.

PHASE ROADMAP:
  Phase 1: Functions called directly from CLI
  Phase 2: LLM calls these via tool-calling API
  Phase 3: LangGraph nodes wrap these functions
  Phase 5: FastAPI endpoints call these via analysis service
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

import numpy as np
import pandas as pd


# ── Result Wrapper ────────────────────────────────────────────────────────────

@dataclass
class ToolResult:
    """
    Standardised return type for every analysis tool.

    Every tool returns this so the agent/validation layer has a consistent
    interface regardless of which tool was called.
    """
    success: bool
    tool_name: str
    result: Any                           # the actual computed value
    description: str                      # human-readable description of result
    metadata: dict[str, Any] = field(default_factory=dict)  # extra context
    error: str | None = None             # error message if success=False

    def __repr__(self) -> str:
        if self.success:
            return f"ToolResult({self.tool_name}) → {self.description}"
        return f"ToolResult({self.tool_name}) ERROR: {self.error}"


# ── Validation Helper ─────────────────────────────────────────────────────────

def _validate_column(df: pd.DataFrame, column: str, tool_name: str) -> ToolResult | None:
    """
    Check that a column exists in the DataFrame.
    Returns a ToolResult error if not found, None if OK.
    This is used internally by every tool before processing.
    """
    if column not in df.columns:
        available = ", ".join(df.columns.tolist())
        return ToolResult(
            success=False,
            tool_name=tool_name,
            result=None,
            description=f"Column '{column}' not found.",
            error=f"Column '{column}' not found. Available columns: {available}",
        )
    return None


def _validate_numeric(df: pd.DataFrame, column: str, tool_name: str) -> ToolResult | None:
    """Check that a column is numeric. Returns error ToolResult or None."""
    if not pd.api.types.is_numeric_dtype(df[column]):
        return ToolResult(
            success=False,
            tool_name=tool_name,
            result=None,
            description=f"Column '{column}' is not numeric.",
            error=f"Column '{column}' has dtype '{df[column].dtype}', expected numeric.",
        )
    return None


# ── Basic Aggregation Tools ───────────────────────────────────────────────────

def calculate_sum(df: pd.DataFrame, column: str) -> ToolResult:
    """
    Calculate the total sum of a numeric column.

    Example:
        calculate_sum(df, 'sales')
        → ToolResult(result=45_823_200.0, description="Total sales: ₹45,823,200.00")
    """
    tool = "calculate_sum"
    err = _validate_column(df, column, tool) or _validate_numeric(df, column, tool)
    if err:
        return err

    total = float(df[column].sum())
    return ToolResult(
        success=True,
        tool_name=tool,
        result=total,
        description=f"Total {column}: {total:,.2f}",
        metadata={"column": column, "count": int(df[column].count())},
    )


def calculate_mean(df: pd.DataFrame, column: str) -> ToolResult:
    """Calculate the arithmetic mean of a numeric column."""
    tool = "calculate_mean"
    err = _validate_column(df, column, tool) or _validate_numeric(df, column, tool)
    if err:
        return err

    mean_val = float(df[column].mean())
    return ToolResult(
        success=True,
        tool_name=tool,
        result=mean_val,
        description=f"Average {column}: {mean_val:,.2f}",
        metadata={"column": column, "count": int(df[column].count())},
    )


def calculate_min(df: pd.DataFrame, column: str) -> ToolResult:
    """Find the minimum value in a numeric column."""
    tool = "calculate_min"
    err = _validate_column(df, column, tool) or _validate_numeric(df, column, tool)
    if err:
        return err

    min_val = float(df[column].min())
    idx = int(df[column].idxmin())
    return ToolResult(
        success=True,
        tool_name=tool,
        result=min_val,
        description=f"Minimum {column}: {min_val:,.2f} (row {idx})",
        metadata={"column": column, "row_index": idx},
    )


def calculate_max(df: pd.DataFrame, column: str) -> ToolResult:
    """Find the maximum value in a numeric column."""
    tool = "calculate_max"
    err = _validate_column(df, column, tool) or _validate_numeric(df, column, tool)
    if err:
        return err

    max_val = float(df[column].max())
    idx = int(df[column].idxmax())
    return ToolResult(
        success=True,
        tool_name=tool,
        result=max_val,
        description=f"Maximum {column}: {max_val:,.2f} (row {idx})",
        metadata={"column": column, "row_index": idx},
    )


def calculate_count(df: pd.DataFrame, column: str | None = None) -> ToolResult:
    """Count non-null rows (total rows if no column specified)."""
    tool = "calculate_count"
    if column:
        err = _validate_column(df, column, tool)
        if err:
            return err
        count = int(df[column].count())
        desc = f"Non-null count of {column}: {count:,}"
    else:
        count = len(df)
        desc = f"Total rows: {count:,}"

    return ToolResult(
        success=True,
        tool_name=tool,
        result=count,
        description=desc,
        metadata={"column": column},
    )


# ── Grouping & Aggregation ────────────────────────────────────────────────────

AggFunc = Literal["sum", "mean", "count", "min", "max", "median"]


def group_by(
    df: pd.DataFrame,
    group_col: str,
    value_col: str,
    agg_func: AggFunc = "sum",
    top_n: int | None = None,
    sort_descending: bool = True,
) -> ToolResult:
    """
    Group the DataFrame by one column and aggregate another.

    Args:
        df:              The source DataFrame.
        group_col:       Column to group by (e.g. 'region', 'category').
        value_col:       Column to aggregate (e.g. 'sales', 'profit').
        agg_func:        Aggregation function: 'sum'|'mean'|'count'|'min'|'max'|'median'.
        top_n:           If set, return only the top N groups.
        sort_descending: Sort largest values first.

    Example:
        group_by(df, 'region', 'profit', 'sum', top_n=5)
        → Which region generated the highest profit?
    """
    tool = "group_by"
    for col in [group_col, value_col]:
        err = _validate_column(df, col, tool)
        if err:
            return err

    # Perform aggregation
    grouped = df.groupby(group_col, dropna=False)[value_col].agg(agg_func)
    grouped = grouped.sort_values(ascending=not sort_descending)

    if top_n:
        grouped = grouped.head(top_n)

    result_df = grouped.reset_index()
    result_df.columns = [group_col, f"{agg_func}_{value_col}"]

    # Convert to list of dicts for JSON serialisability
    result_list = result_df.to_dict(orient="records")

    top_group = result_list[0] if result_list else {}
    top_name = top_group.get(group_col, "N/A")
    top_value = top_group.get(f"{agg_func}_{value_col}", 0)

    return ToolResult(
        success=True,
        tool_name=tool,
        result=result_list,
        description=(
            f"{agg_func.capitalize()} of {value_col} by {group_col}. "
            f"Top: {top_name} ({top_value:,.2f})"
        ),
        metadata={
            "group_col": group_col,
            "value_col": value_col,
            "agg_func": agg_func,
            "n_groups": len(result_list),
        },
    )


def top_n(
    df: pd.DataFrame,
    group_col: str,
    value_col: str,
    n: int = 5,
    agg_func: AggFunc = "sum",
) -> ToolResult:
    """Convenience wrapper: top N groups by value. Delegates to group_by."""
    return group_by(df, group_col, value_col, agg_func, top_n=n, sort_descending=True)


# ── Filtering ─────────────────────────────────────────────────────────────────

Operator = Literal["==", "!=", ">", ">=", "<", "<=", "contains", "startswith"]


def filter_rows(
    df: pd.DataFrame,
    column: str,
    operator: Operator,
    value: Any,
) -> ToolResult:
    """
    Filter rows based on a condition.

    Args:
        df:       Source DataFrame.
        column:   Column to filter on.
        operator: Comparison operator.
        value:    Value to compare against.

    Example:
        filter_rows(df, 'category', '==', 'Electronics')
        filter_rows(df, 'sales', '>', 100000)
        filter_rows(df, 'region', 'contains', 'North')
    """
    tool = "filter_rows"
    err = _validate_column(df, column, tool)
    if err:
        return err

    series = df[column]

    try:
        if operator == "==":
            mask = series == value
        elif operator == "!=":
            mask = series != value
        elif operator == ">":
            mask = series > value
        elif operator == ">=":
            mask = series >= value
        elif operator == "<":
            mask = series < value
        elif operator == "<=":
            mask = series <= value
        elif operator == "contains":
            mask = series.astype(str).str.contains(str(value), case=False, na=False)
        elif operator == "startswith":
            mask = series.astype(str).str.startswith(str(value), na=False)
        else:
            return ToolResult(
                success=False,
                tool_name=tool,
                result=None,
                description="",
                error=f"Unknown operator: '{operator}'",
            )
    except TypeError as e:
        return ToolResult(
            success=False,
            tool_name=tool,
            result=None,
            description="",
            error=f"Type error during filter: {e}",
        )

    filtered = df[mask]
    return ToolResult(
        success=True,
        tool_name=tool,
        result=filtered,           # returns DataFrame for chaining
        description=f"Filtered rows where {column} {operator} '{value}': {len(filtered):,} rows",
        metadata={
            "column": column,
            "operator": operator,
            "value": str(value),
            "rows_before": len(df),
            "rows_after": len(filtered),
        },
    )


# ── Sorting ───────────────────────────────────────────────────────────────────

def sort_data(
    df: pd.DataFrame,
    column: str,
    ascending: bool = False,
    head: int | None = 10,
) -> ToolResult:
    """
    Sort the DataFrame by a column and return the top rows.

    Args:
        df:        Source DataFrame.
        column:    Column to sort by.
        ascending: False = largest first (default).
        head:      Return only first N rows (None = all rows).
    """
    tool = "sort_data"
    err = _validate_column(df, column, tool)
    if err:
        return err

    sorted_df = df.sort_values(by=column, ascending=ascending)
    if head:
        sorted_df = sorted_df.head(head)

    direction = "ascending" if ascending else "descending"
    return ToolResult(
        success=True,
        tool_name=tool,
        result=sorted_df,
        description=f"Sorted by {column} ({direction}), showing top {len(sorted_df)} rows",
        metadata={"column": column, "ascending": ascending},
    )


# ── Time-Series Analysis ──────────────────────────────────────────────────────

def time_series_aggregate(
    df: pd.DataFrame,
    date_col: str,
    value_col: str,
    frequency: Literal["D", "W", "ME", "QE", "YE"] = "ME",
    agg_func: AggFunc = "sum",
) -> ToolResult:
    """
    Aggregate a value column over time periods.

    Args:
        df:        Source DataFrame.
        date_col:  Column containing dates.
        value_col: Numeric column to aggregate.
        frequency: 'D'=daily, 'W'=weekly, 'ME'=monthly, 'QE'=quarterly, 'YE'=yearly
        agg_func:  Aggregation function.

    Example:
        time_series_aggregate(df, 'order_date', 'sales', 'ME', 'sum')
        → Monthly total sales

    TEACHING NOTE:
        'ME' stands for "Month End" — it's the pandas 2.x replacement for 'M'.
        Using 'M' now raises a FutureWarning.
    """
    tool = "time_series_aggregate"
    for col in [date_col, value_col]:
        err = _validate_column(df, col, tool)
        if err:
            return err

    # Ensure date column is datetime
    try:
        dates = pd.to_datetime(df[date_col])
    except Exception as e:
        return ToolResult(
            success=False,
            tool_name=tool,
            result=None,
            description="",
            error=f"Could not parse '{date_col}' as datetime: {e}",
        )

    temp = df[[value_col]].copy()
    temp.index = dates

    resampled = temp[value_col].resample(frequency).agg(agg_func)
    resampled = resampled.reset_index()
    resampled.columns = ["period", value_col]
    resampled["period"] = resampled["period"].astype(str)

    result_list = resampled.to_dict(orient="records")

    freq_labels = {"D": "daily", "W": "weekly", "ME": "monthly", "QE": "quarterly", "YE": "yearly"}
    freq_label = freq_labels.get(frequency, frequency)

    return ToolResult(
        success=True,
        tool_name=tool,
        result=result_list,
        description=f"{agg_func.capitalize()} {value_col} by {freq_label} period ({len(result_list)} periods)",
        metadata={
            "date_col": date_col,
            "value_col": value_col,
            "frequency": frequency,
            "agg_func": agg_func,
            "n_periods": len(result_list),
        },
    )


def compare_periods(
    df: pd.DataFrame,
    date_col: str,
    value_col: str,
    period1: str,
    period2: str,
    agg_func: AggFunc = "sum",
) -> ToolResult:
    """
    Compare a metric between two time periods and calculate percentage change.

    Args:
        df:        Source DataFrame.
        date_col:  Date column name.
        value_col: Numeric column to compare.
        period1:   First period label, e.g. "2023-02" (base period).
        period2:   Second period label, e.g. "2023-03" (comparison period).
        agg_func:  How to aggregate within each period.

    Example:
        compare_periods(df, 'order_date', 'sales', '2023-02', '2023-03')
        → "Sales decreased 32.9% from February to March"

    TEACHING NOTE:
        This is one of the most important tools for the question
        "Why did sales decrease in March?" because it provides
        the raw fact that the LLM then explains.
    """
    tool = "compare_periods"
    for col in [date_col, value_col]:
        err = _validate_column(df, col, tool)
        if err:
            return err

    try:
        dates = pd.to_datetime(df[date_col])
    except Exception as e:
        return ToolResult(
            success=False, tool_name=tool, result=None, description="",
            error=f"Cannot parse date column: {e}",
        )

    temp = df[[value_col]].copy()
    temp["_period"] = dates.dt.to_period("M").astype(str)

    def _aggregate(period_str: str) -> float | None:
        subset = temp[temp["_period"] == period_str][value_col]
        if subset.empty:
            return None
        funcs = {"sum": "sum", "mean": "mean", "count": "count",
                 "min": "min", "max": "max", "median": "median"}
        return float(getattr(subset, funcs[agg_func])())

    val1 = _aggregate(period1)
    val2 = _aggregate(period2)

    if val1 is None:
        return ToolResult(
            success=False, tool_name=tool, result=None, description="",
            error=f"No data found for period '{period1}'.",
        )
    if val2 is None:
        return ToolResult(
            success=False, tool_name=tool, result=None, description="",
            error=f"No data found for period '{period2}'.",
        )

    if val1 != 0:
        pct_change = round((val2 - val1) / abs(val1) * 100, 2)
    else:
        pct_change = None

    direction = "increased" if (pct_change or 0) >= 0 else "decreased"
    abs_change = abs(val2 - val1)

    return ToolResult(
        success=True,
        tool_name=tool,
        result={
            "period1": period1,
            "period2": period2,
            "value1": round(val1, 2),
            "value2": round(val2, 2),
            "absolute_change": round(abs_change, 2),
            "pct_change": pct_change,
            "direction": direction,
        },
        description=(
            f"{value_col} {direction} by {abs(pct_change or 0):.1f}% "
            f"from {period1} ({val1:,.2f}) to {period2} ({val2:,.2f})"
        ),
        metadata={"agg_func": agg_func},
    )


def calculate_percentage_change(
    df: pd.DataFrame,
    date_col: str,
    value_col: str,
    frequency: Literal["ME", "QE", "YE"] = "ME",
) -> ToolResult:
    """
    Calculate period-over-period percentage changes for a full time series.

    Useful for: "How has profit changed month over month?"
    """
    tool = "calculate_percentage_change"
    ts_result = time_series_aggregate(df, date_col, value_col, frequency, "sum")
    if not ts_result.success:
        return ts_result

    series_data = ts_result.result
    if len(series_data) < 2:
        return ToolResult(
            success=False, tool_name=tool, result=None, description="",
            error="Need at least 2 periods to calculate percentage change.",
        )

    result = []
    for i in range(1, len(series_data)):
        prev = series_data[i - 1][value_col]
        curr = series_data[i][value_col]
        pct = round((curr - prev) / abs(prev) * 100, 2) if prev != 0 else None
        result.append({
            "period": series_data[i]["period"],
            "value": round(curr, 2),
            "prev_value": round(prev, 2),
            "pct_change": pct,
        })

    return ToolResult(
        success=True,
        tool_name=tool,
        result=result,
        description=f"Period-over-period % change for {value_col} ({len(result)} periods)",
        metadata={"value_col": value_col, "frequency": frequency},
    )


# ── Value Counts ──────────────────────────────────────────────────────────────

def value_counts(
    df: pd.DataFrame,
    column: str,
    normalize: bool = False,
    top_n_limit: int = 20,
) -> ToolResult:
    """
    Count occurrences of each unique value in a categorical column.

    Args:
        normalize:    If True, return proportions instead of counts.
        top_n_limit:  Return only top N values.
    """
    tool = "value_counts"
    err = _validate_column(df, column, tool)
    if err:
        return err

    vc = df[column].value_counts(normalize=normalize, dropna=False).head(top_n_limit)
    result = [{"value": str(v), "count": float(c)} for v, c in vc.items()]
    label = "proportion" if normalize else "count"
    top = result[0] if result else {}

    return ToolResult(
        success=True,
        tool_name=tool,
        result=result,
        description=f"Top values in '{column}' by {label}. Most common: '{top.get('value')}' ({top.get('count')})",
        metadata={"column": column, "normalize": normalize},
    )
