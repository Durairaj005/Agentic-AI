"""
tools/statistics_tools.py — Statistical Analysis Tools
=======================================================

PURPOSE:
  Advanced statistical operations that go beyond simple aggregation.
  These are separate from pandas_tools.py because they:
    • Use SciPy for more rigorous calculations
    • Detect anomalies in data
    • Measure relationships between columns
    • Provide descriptive statistics for a single column

WHY SEPARATE FROM pandas_tools.py:
  Separation of concerns. When the Analysis Agent plans its workflow:
    • Simple aggregation → pandas_tools
    • Statistical analysis → statistics_tools
    • Visualisation → visualization_tools
  This makes it easy for the LLM to understand which module to look at.

PHASE ROADMAP:
  Phase 1: Used in CLI directly
  Phase 3: Called by Analysis Agent node in LangGraph
  Phase 5: Exposed via /api/v1/analysis endpoint
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

try:
    from scipy import stats as scipy_stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

from app.tools.pandas_tools import ToolResult, _validate_column, _validate_numeric


# ── Outlier Detection ─────────────────────────────────────────────────────────

def detect_outliers(
    df: pd.DataFrame,
    column: str,
    method: str = "iqr",
    threshold: float = 1.5,
) -> ToolResult:
    """
    Detect outliers in a numeric column.

    Args:
        df:        Source DataFrame.
        column:    Numeric column to analyse.
        method:    'iqr' (default) or 'zscore'.
        threshold: For IQR: multiplier (1.5=mild, 3.0=extreme).
                   For z-score: number of standard deviations.

    HOW IQR METHOD WORKS:
        Q1 = 25th percentile
        Q3 = 75th percentile
        IQR = Q3 - Q1
        Lower fence = Q1 - threshold × IQR
        Upper fence = Q3 + threshold × IQR
        Anything outside the fences is an outlier.

    HOW Z-SCORE METHOD WORKS:
        z = (value - mean) / std
        If |z| > threshold, it's an outlier.
        Assumes roughly normal distribution.

    WHY IQR IS DEFAULT:
        IQR is robust to extreme values and works for skewed distributions.
        Z-score can be thrown off by the very outliers you're trying to detect.
        For real sales data, IQR is usually more reliable.
    """
    tool = "detect_outliers"
    err = _validate_column(df, column, tool) or _validate_numeric(df, column, tool)
    if err:
        return err

    clean = df[column].dropna()
    if len(clean) == 0:
        return ToolResult(
            success=False, tool_name=tool, result=None, description="",
            error=f"Column '{column}' has no non-null values.",
        )

    if method == "iqr":
        q1 = clean.quantile(0.25)
        q3 = clean.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - threshold * iqr
        upper = q3 + threshold * iqr
        is_outlier = (df[column] < lower) | (df[column] > upper)

    elif method == "zscore":
        z_scores = np.abs((clean - clean.mean()) / clean.std())
        is_outlier = pd.Series(False, index=df.index)
        is_outlier.loc[clean.index] = z_scores > threshold

    else:
        return ToolResult(
            success=False, tool_name=tool, result=None, description="",
            error=f"Unknown method '{method}'. Use 'iqr' or 'zscore'.",
        )

    outlier_rows = df[is_outlier].copy()
    n_outliers = len(outlier_rows)
    outlier_pct = round(n_outliers / len(df) * 100, 2)

    # Summary stats of outlier values
    outlier_values = df.loc[is_outlier, column].tolist()
    sample = sorted(outlier_values, key=abs, reverse=True)[:10]

    meta: dict[str, Any] = {
        "method": method,
        "column": column,
        "n_outliers": n_outliers,
        "outlier_pct": outlier_pct,
        "sample_values": [round(v, 2) for v in sample],
    }

    if method == "iqr":
        meta["lower_fence"] = round(float(lower), 2)
        meta["upper_fence"] = round(float(upper), 2)
        meta["q1"] = round(float(q1), 2)
        meta["q3"] = round(float(q3), 2)
        meta["iqr"] = round(float(iqr), 2)
    elif method == "zscore":
        meta["threshold_std"] = threshold

    return ToolResult(
        success=True,
        tool_name=tool,
        result=outlier_rows.to_dict(orient="records"),
        description=(
            f"Found {n_outliers:,} outliers in '{column}' ({outlier_pct}%) "
            f"using {method.upper()} method."
        ),
        metadata=meta,
    )


# ── Correlation Analysis ──────────────────────────────────────────────────────

def calculate_correlation(
    df: pd.DataFrame,
    col1: str,
    col2: str,
    method: str = "pearson",
) -> ToolResult:
    """
    Calculate the correlation between two numeric columns.

    Args:
        col1, col2: Columns to correlate.
        method:     'pearson' (linear), 'spearman' (rank), 'kendall' (rank).

    WHAT CORRELATION TELLS YOU:
        +1.0 = perfect positive relationship (both go up together)
         0.0 = no relationship
        -1.0 = perfect inverse relationship (one goes up, other goes down)

    WHY SPEARMAN SOMETIMES BETTER:
        Pearson assumes linear relationship and is sensitive to outliers.
        Spearman measures monotonic relationship (non-linear) and is robust.
        For sales data with outliers, Spearman is often more informative.

    IMPORTANT — CORRELATION ≠ CAUSATION:
        The LLM should always qualify this when presenting to users.
    """
    tool = "calculate_correlation"
    for col in [col1, col2]:
        err = _validate_column(df, col, tool) or _validate_numeric(df, col, tool)
        if err:
            return err

    valid = df[[col1, col2]].dropna()
    if len(valid) < 3:
        return ToolResult(
            success=False, tool_name=tool, result=None, description="",
            error=f"Need at least 3 non-null pairs. Found {len(valid)}.",
        )

    corr = round(float(valid[col1].corr(valid[col2], method=method)), 4)

    # Interpret the strength
    abs_corr = abs(corr)
    if abs_corr >= 0.8:
        strength = "very strong"
    elif abs_corr >= 0.6:
        strength = "strong"
    elif abs_corr >= 0.4:
        strength = "moderate"
    elif abs_corr >= 0.2:
        strength = "weak"
    else:
        strength = "very weak / negligible"

    direction = "positive" if corr > 0 else "negative"

    # Optional p-value via SciPy
    p_value = None
    if SCIPY_AVAILABLE:
        if method == "pearson":
            _, p_value = scipy_stats.pearsonr(valid[col1], valid[col2])
        elif method == "spearman":
            _, p_value = scipy_stats.spearmanr(valid[col1], valid[col2])

    p_str = f" (p={p_value:.4f})" if p_value is not None else ""

    return ToolResult(
        success=True,
        tool_name=tool,
        result={
            "col1": col1,
            "col2": col2,
            "correlation": corr,
            "method": method,
            "strength": strength,
            "direction": direction,
            "p_value": round(float(p_value), 6) if p_value is not None else None,
            "n_pairs": len(valid),
        },
        description=(
            f"{method.capitalize()} correlation between '{col1}' and '{col2}': "
            f"{corr:.4f} ({strength} {direction}){p_str}"
        ),
        metadata={"n_pairs": len(valid)},
    )


def correlation_matrix(df: pd.DataFrame, method: str = "pearson") -> ToolResult:
    """
    Calculate the full correlation matrix for all numeric columns.

    Useful for: "Which variables are correlated with profit?"
    """
    tool = "correlation_matrix"
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    if len(numeric_cols) < 2:
        return ToolResult(
            success=False, tool_name=tool, result=None, description="",
            error="Need at least 2 numeric columns for a correlation matrix.",
        )

    corr_matrix = df[numeric_cols].corr(method=method).round(4)

    # Convert to list-of-dicts format
    result = corr_matrix.reset_index().rename(columns={"index": "column"}).to_dict(orient="records")

    return ToolResult(
        success=True,
        tool_name=tool,
        result=result,
        description=(
            f"{method.capitalize()} correlation matrix for {len(numeric_cols)} "
            f"numeric columns: {', '.join(numeric_cols)}"
        ),
        metadata={"columns": numeric_cols, "method": method},
    )


# ── Descriptive Statistics ────────────────────────────────────────────────────

def describe_column(df: pd.DataFrame, column: str) -> ToolResult:
    """
    Full descriptive statistics for a single numeric column.

    Returns mean, std, min, max, quartiles, skewness, kurtosis.
    """
    tool = "describe_column"
    err = _validate_column(df, column, tool) or _validate_numeric(df, column, tool)
    if err:
        return err

    clean = df[column].dropna()

    desc = clean.describe()
    skewness = round(float(clean.skew()), 4)
    kurt = round(float(clean.kurtosis()), 4)

    result = {
        "column": column,
        "count": int(desc["count"]),
        "mean": round(float(desc["mean"]), 4),
        "std": round(float(desc["std"]), 4),
        "min": round(float(desc["min"]), 4),
        "q25": round(float(desc["25%"]), 4),
        "median": round(float(desc["50%"]), 4),
        "q75": round(float(desc["75%"]), 4),
        "max": round(float(desc["max"]), 4),
        "skewness": skewness,
        "kurtosis": kurt,
        "missing": int(df[column].isnull().sum()),
    }

    # Skewness interpretation
    if abs(skewness) < 0.5:
        skew_label = "approximately symmetric"
    elif skewness > 0:
        skew_label = "right-skewed (long tail on right)"
    else:
        skew_label = "left-skewed (long tail on left)"

    return ToolResult(
        success=True,
        tool_name=tool,
        result=result,
        description=(
            f"'{column}': mean={result['mean']:,.2f}, "
            f"median={result['median']:,.2f}, std={result['std']:,.2f}. "
            f"Distribution is {skew_label}."
        ),
        metadata={"skew_label": skew_label},
    )


def normality_test(df: pd.DataFrame, column: str) -> ToolResult:
    """
    Test whether a column's distribution is approximately normal.
    Uses Shapiro-Wilk test (best for n < 5000) or D'Agostino for larger samples.

    WHY THIS MATTERS:
        Some statistical tests assume normal distribution.
        If data is heavily skewed, the agent should use median instead of mean,
        and Spearman instead of Pearson correlation.
    """
    tool = "normality_test"
    err = _validate_column(df, column, tool) or _validate_numeric(df, column, tool)
    if err:
        return err

    if not SCIPY_AVAILABLE:
        return ToolResult(
            success=False, tool_name=tool, result=None, description="",
            error="SciPy not installed. Run: pip install scipy",
        )

    clean = df[column].dropna()
    n = len(clean)

    if n < 8:
        return ToolResult(
            success=False, tool_name=tool, result=None, description="",
            error=f"Need at least 8 values for normality test. Found {n}.",
        )

    # Choose test based on sample size
    if n <= 5000:
        stat, p_value = scipy_stats.shapiro(clean)
        test_name = "Shapiro-Wilk"
    else:
        # Sample for performance
        sample = clean.sample(n=5000, random_state=42)
        stat, p_value = scipy_stats.shapiro(sample)
        test_name = "Shapiro-Wilk (5000-sample)"

    is_normal = p_value > 0.05
    interpretation = (
        "Approximately normal (p > 0.05)" if is_normal
        else f"NOT normal — distribution is significantly non-normal (p={p_value:.4f})"
    )

    return ToolResult(
        success=True,
        tool_name=tool,
        result={
            "test": test_name,
            "statistic": round(float(stat), 4),
            "p_value": round(float(p_value), 6),
            "is_normal": is_normal,
            "n": n,
        },
        description=f"'{column}' normality ({test_name}): {interpretation}",
        metadata={"column": column},
    )
