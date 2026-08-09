"""
tests/test_pandas_tools.py — Unit Tests for Analysis Tools
===========================================================

PURPOSE:
  Verify that every analysis tool returns correct results on known data.

WHY TEST DETERMINISTIC TOOLS:
  These tools will be called thousands of times by the LangGraph agent.
  A wrong calculation returned silently is worse than a visible error.
  Tests give us confidence to add the LLM layer on top.

HOW TO RUN:
  # From the ai-data-analyst/ directory:
  .venv/Scripts/pytest backend/tests/test_pandas_tools.py -v

TEACHING NOTE:
  Notice that we test with KNOWN data (not the generated sales.csv).
  This lets tests be fast, reproducible, and specific.
  We'll mock the LLM in Phase 2 tests the same way.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.tools.pandas_tools import (
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
)
from app.tools.statistics_tools import (
    detect_outliers,
    calculate_correlation,
    describe_column,
)


# ── Test Fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture
def sample_df() -> pd.DataFrame:
    """
    A small, known DataFrame for deterministic testing.
    Values are chosen so we can calculate expected results by hand.
    """
    return pd.DataFrame({
        "order_date": pd.date_range("2023-01-01", periods=12, freq="MS"),
        "region":     ["North", "South", "North", "East", "South", "North",
                       "East", "West", "North", "South", "East", "West"],
        "category":   ["Electronics", "Furniture", "Electronics", "Furniture",
                       "Electronics", "Furniture", "Electronics", "Furniture",
                       "Electronics", "Furniture", "Electronics", "Furniture"],
        "sales":      [100, 200, 150, 80, 120, 300, 90, 110, 140, 160, 70, 200],
        "profit":     [20,  50,  30,  10, 25,  80,  15, 20,  28,  40,  12, 45],
        "quantity":   [5,   2,   3,   1,  4,   6,   2,  3,   4,   3,   2,  5],
        "discount":   [0.1, 0.0, 0.1, 0.2, 0.0, 0.15, 0.1, 0.0, 0.05, 0.1, 0.2, 0.0],
    })


@pytest.fixture
def df_with_nulls(sample_df) -> pd.DataFrame:
    """DataFrame with some null values in sales and region."""
    df = sample_df.copy()
    df.loc[0, "sales"] = None
    df.loc[3, "region"] = None
    return df


@pytest.fixture
def df_with_outliers(sample_df) -> pd.DataFrame:
    """DataFrame with obvious outliers in profit."""
    df = sample_df.copy()
    df.loc[11, "profit"] = 5000    # extreme outlier
    df.loc[10, "profit"] = -1000   # negative outlier
    return df


# ── calculate_sum ─────────────────────────────────────────────────────────────

class TestCalculateSum:

    def test_correct_sum(self, sample_df):
        result = calculate_sum(sample_df, "sales")
        assert result.success is True
        assert result.result == pytest.approx(1720)    # sum of the sales column

    def test_invalid_column(self, sample_df):
        result = calculate_sum(sample_df, "nonexistent")
        assert result.success is False
        assert "not found" in result.error.lower()

    def test_non_numeric_column(self, sample_df):
        result = calculate_sum(sample_df, "region")
        assert result.success is False
        # pandas 3.x reports dtype as 'str', message says 'expected numeric'
        assert "expected numeric" in result.error.lower()

    def test_sum_with_nulls(self, df_with_nulls):
        # Pandas sum() ignores NaN by default — tool should behave the same
        result = calculate_sum(df_with_nulls, "sales")
        assert result.success is True
        assert result.result == pytest.approx(1620)   # 1720 - 100 (null row)


# ── calculate_mean ────────────────────────────────────────────────────────────

class TestCalculateMean:

    def test_correct_mean(self, sample_df):
        result = calculate_mean(sample_df, "sales")
        assert result.success is True
        expected = 1720 / 12
        assert result.result == pytest.approx(expected, rel=1e-4)

    def test_profit_mean(self, sample_df):
        result = calculate_mean(sample_df, "profit")
        assert result.success is True
        total_profit = 20+50+30+10+25+80+15+20+28+40+12+45
        assert result.result == pytest.approx(total_profit / 12, rel=1e-4)


# ── calculate_min / calculate_max ─────────────────────────────────────────────

class TestMinMax:

    def test_min_sales(self, sample_df):
        result = calculate_min(sample_df, "sales")
        assert result.success is True
        assert result.result == 70    # row index 10

    def test_max_sales(self, sample_df):
        result = calculate_max(sample_df, "sales")
        assert result.success is True
        assert result.result == 300   # row index 5


# ── group_by ─────────────────────────────────────────────────────────────────

class TestGroupBy:

    def test_group_by_region_sum_profit(self, sample_df):
        result = group_by(sample_df, "region", "profit", "sum")
        assert result.success is True
        data = {row["region"]: row["sum_profit"] for row in result.result}

        # North: 20+30+80+28 = 158
        assert data["North"] == pytest.approx(158)
        # South: 50+25+40 = 115
        assert data["South"] == pytest.approx(115)

    def test_group_by_top_n(self, sample_df):
        result = group_by(sample_df, "region", "sales", "sum", top_n=2)
        assert result.success is True
        assert len(result.result) == 2

    def test_group_by_mean(self, sample_df):
        result = group_by(sample_df, "category", "profit", "mean")
        assert result.success is True
        data = {row["category"]: row["mean_profit"] for row in result.result}
        # Electronics: 20+30+25+15+28+12 = 130 / 6 = 21.666...
        assert data["Electronics"] == pytest.approx(130 / 6, rel=1e-3)


# ── filter_rows ───────────────────────────────────────────────────────────────

class TestFilterRows:

    def test_filter_equals(self, sample_df):
        result = filter_rows(sample_df, "region", "==", "North")
        assert result.success is True
        assert isinstance(result.result, pd.DataFrame)
        assert len(result.result) == 4   # North appears 4 times

    def test_filter_greater_than(self, sample_df):
        result = filter_rows(sample_df, "sales", ">", 150)
        assert result.success is True
        assert all(result.result["sales"] > 150)

    def test_filter_no_match(self, sample_df):
        result = filter_rows(sample_df, "region", "==", "Mars")
        assert result.success is True
        assert len(result.result) == 0

    def test_filter_contains(self, sample_df):
        result = filter_rows(sample_df, "region", "contains", "orth")
        assert result.success is True
        assert len(result.result) == 4   # "North" contains "orth"

    def test_filter_invalid_column(self, sample_df):
        result = filter_rows(sample_df, "badcol", "==", "x")
        assert result.success is False


# ── time_series_aggregate ─────────────────────────────────────────────────────

class TestTimeSeries:

    def test_monthly_sum(self, sample_df):
        result = time_series_aggregate(sample_df, "order_date", "sales", "ME", "sum")
        assert result.success is True
        # Each row is a different month, so each period should have 1 value
        assert len(result.result) == 12
        # Each period's sales should equal the row value
        totals = [r["sales"] for r in result.result]
        expected = [100, 200, 150, 80, 120, 300, 90, 110, 140, 160, 70, 200]
        assert totals == pytest.approx(expected)


# ── compare_periods ───────────────────────────────────────────────────────────

class TestComparePeriods:

    def test_compare_basic(self, sample_df):
        # Jan 2023 = 100, Feb 2023 = 200
        result = compare_periods(sample_df, "order_date", "sales", "2023-01", "2023-02")
        assert result.success is True
        assert result.result["value1"] == pytest.approx(100)
        assert result.result["value2"] == pytest.approx(200)
        assert result.result["pct_change"] == pytest.approx(100.0)   # 100% increase
        assert result.result["direction"] == "increased"

    def test_compare_decrease(self, sample_df):
        # Feb 2023=200, Mar 2023=150 → -25% change
        result = compare_periods(sample_df, "order_date", "sales", "2023-02", "2023-03")
        assert result.success is True
        assert result.result["pct_change"] == pytest.approx(-25.0)
        assert result.result["direction"] == "decreased"

    def test_compare_missing_period(self, sample_df):
        result = compare_periods(sample_df, "order_date", "sales", "2022-01", "2023-01")
        assert result.success is False
        assert "2022-01" in result.error


# ── detect_outliers ───────────────────────────────────────────────────────────

class TestDetectOutliers:

    def test_finds_outliers(self, df_with_outliers):
        result = detect_outliers(df_with_outliers, "profit")
        assert result.success is True
        # At least the 5000 and -1000 rows should be flagged
        outlier_profits = [r["profit"] for r in result.result]
        assert 5000 in outlier_profits
        assert -1000 in outlier_profits

    def test_no_outliers_uniform_data(self):
        df = pd.DataFrame({"values": [100, 101, 99, 100, 102, 98, 100, 101]})
        result = detect_outliers(df, "values")
        assert result.success is True
        assert len(result.result) == 0   # no outliers in uniform data

    def test_invalid_column(self, sample_df):
        result = detect_outliers(sample_df, "badcol")
        assert result.success is False


# ── calculate_correlation ─────────────────────────────────────────────────────

class TestCorrelation:

    def test_perfect_positive_correlation(self):
        df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [2, 4, 6, 8, 10]})
        result = calculate_correlation(df, "x", "y")
        assert result.success is True
        assert result.result["correlation"] == pytest.approx(1.0)
        assert result.result["direction"] == "positive"

    def test_negative_correlation(self):
        df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 8, 6, 4, 2]})
        result = calculate_correlation(df, "x", "y")
        assert result.success is True
        assert result.result["correlation"] == pytest.approx(-1.0)

    def test_sales_profit_correlation(self, sample_df):
        result = calculate_correlation(sample_df, "sales", "profit")
        assert result.success is True
        # They should be positively correlated
        assert result.result["correlation"] > 0

    def test_non_numeric_column(self, sample_df):
        result = calculate_correlation(sample_df, "region", "sales")
        assert result.success is False


# ── describe_column ───────────────────────────────────────────────────────────

class TestDescribeColumn:

    def test_returns_all_fields(self, sample_df):
        result = describe_column(sample_df, "sales")
        assert result.success is True
        r = result.result
        assert "mean" in r
        assert "std" in r
        assert "min" in r
        assert "max" in r
        assert "median" in r
        assert "skewness" in r

    def test_correct_values(self, sample_df):
        result = describe_column(sample_df, "sales")
        assert result.success is True
        assert result.result["min"] == pytest.approx(70.0)
        assert result.result["max"] == pytest.approx(300.0)


# ── Edge Cases ────────────────────────────────────────────────────────────────

class TestEdgeCases:

    def test_empty_dataframe(self):
        df = pd.DataFrame({"sales": [], "region": []})
        result = calculate_sum(df, "sales")
        assert result.success is True
        assert result.result == 0

    def test_single_row(self):
        df = pd.DataFrame({"sales": [42.0], "region": ["North"]})
        result = calculate_mean(df, "sales")
        assert result.success is True
        assert result.result == pytest.approx(42.0)

    def test_all_nulls(self):
        # Use np.nan (float) so pandas infers dtype as float64, not object
        df = pd.DataFrame({"sales": [np.nan, np.nan, np.nan]})
        result = calculate_sum(df, "sales")
        assert result.success is True
        assert result.result == 0.0
