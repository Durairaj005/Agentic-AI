"""
tests/test_visualization.py — Unit Tests for Visualizations
============================================================

PURPOSE:
  Tests generation and PNG exports of bar, line, pie, and scatter charts.
  Verifies that they are styled correctly and saved in the exports directory.
"""

from __future__ import annotations

import os
import shutil
import unittest
from pathlib import Path
import pandas as pd

from app.tools.visualization_tools import (
    plot_bar_chart,
    plot_line_chart,
    plot_pie_chart,
    plot_scatter_chart,
    EXPORT_DIR,
)


class TestVisualizationTools(unittest.TestCase):

    def setUp(self):
        # Create a tiny test dataframe
        self.df = pd.DataFrame({
            "product": ["Apples", "Bananas", "Cherries"],
            "sales": [120, 240, 80],
            "profit": [45.5, 92.0, 18.2]
        })
        # Use a separate test exports directory to isolate unit tests
        self.test_export_dir = Path("exports/test_charts")
        os.makedirs(self.test_export_dir, exist_ok=True)

    def tearDown(self):
        # Clean up any created files and directories
        if self.test_export_dir.exists():
            shutil.rmtree(self.test_export_dir)
        
        # Also clean up standard test files in main exports if generated
        for path in EXPORT_DIR.glob("test_*"):
            try:
                path.unlink()
            except OSError:
                pass

    def test_plot_bar_chart_success(self):
        """Verifies bar chart is successfully generated and exported as a PNG."""
        res = plot_bar_chart(
            self.df,
            x_col="product",
            y_col="sales",
            title="Test Bar Chart",
            filename="test_bar_chart"
        )
        assert res.success is True
        assert Path(res.result).exists()
        assert Path(res.result).suffix == ".png"
        assert res.tool_name == "plot_bar_chart"

    def test_plot_line_chart_success(self):
        """Verifies line chart is successfully generated and exported as a PNG."""
        res = plot_line_chart(
            self.df,
            x_col="product",
            y_col="profit",
            title="Test Line Chart",
            filename="test_line_chart"
        )
        assert res.success is True
        assert Path(res.result).exists()
        assert res.tool_name == "plot_line_chart"

    def test_plot_pie_chart_success(self):
        """Verifies pie chart is successfully generated and exported as a PNG."""
        res = plot_pie_chart(
            self.df,
            names_col="product",
            values_col="sales",
            title="Test Pie Chart",
            filename="test_pie_chart"
        )
        assert res.success is True
        assert Path(res.result).exists()
        assert res.tool_name == "plot_pie_chart"

    def test_plot_scatter_chart_success(self):
        """Verifies scatter chart is successfully generated and exported as a PNG."""
        res = plot_scatter_chart(
            self.df,
            x_col="sales",
            y_col="profit",
            title="Test Scatter Chart",
            filename="test_scatter_chart"
        )
        assert res.success is True
        assert Path(res.result).exists()
        assert res.tool_name == "plot_scatter_chart"

    def test_invalid_column_failure(self):
        """Verifies that an error is returned if columns do not exist in the DataFrame."""
        res = plot_bar_chart(
            self.df,
            x_col="invalid_column",
            y_col="sales",
            title="Test Bar Chart",
            filename="test_fail_bar"
        )
        assert res.success is False
        assert "not found" in res.description
        assert "does not exist" in res.error
