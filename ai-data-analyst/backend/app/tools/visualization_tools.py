"""
tools/visualization_tools.py — Plotly Data Visualization Primitives
=====================================================================

PURPOSE:
  These are the "visual eyes" of the agent.
  This module generates premium-designed charts (bar, line, pie, scatter) using
  Plotly and exports them to static high-resolution PNGs in:
  `exports/charts/<filename>.png`

DESIGN RULES (Aesthetics "Wow the User"):
  1. We avoid default Plotly templates.
  2. We apply a cohesive, modern visual theme:
     - Curated high-contrast colors (Deep Blue, Cyan, Coral Rose, Amber, Emerald).
     - Clean, responsive layouts (default 1000x600 px at scale=2).
     - Light/transparent canvas margins with thin gridlines.
"""

from __future__ import annotations

import os
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.io as pio

# Import result wrapper
from app.tools.pandas_tools import ToolResult

# ── Custom Premium Styling Configuration ──────────────────────────────────────
# Curated palettes replacing basic default primaries
COLOR_SEQUENCE = ["#1E3A8A", "#06B6D4", "#F43F5E", "#F59E0B", "#10B981"]
THEME_TEMPLATE = "plotly_white"

# Target export folder
EXPORT_DIR = Path("exports/charts")


def _apply_premium_styling(fig: px.Figure, title: str) -> px.Figure:
    """Applies our custom style tokens to make charts look highly premium."""
    fig.update_layout(
        template=THEME_TEMPLATE,
        title={
            "text": f"<b>{title}</b>",
            "y": 0.95,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
            "font": {"size": 20, "color": "#111827", "family": "Inter, Arial, sans-serif"}
        },
        font={"family": "Inter, Arial, sans-serif", "color": "#4B5563"},
        margin={"t": 80, "b": 60, "l": 60, "r": 60},
        paper_bgcolor="rgba(255, 255, 255, 0.95)",
        plot_bgcolor="rgba(249, 250, 251, 0.8)",
        hovermode="closest"
    )
    
    # Sleek gridlines styling
    fig.update_xaxes(showgrid=True, gridcolor="#E5E7EB", linecolor="#D1D5DB", linewidth=1)
    fig.update_yaxes(showgrid=True, gridcolor="#E5E7EB", linecolor="#D1D5DB", linewidth=1)
    
    return fig


def _ensure_export_directory() -> None:
    """Creates the charts directory if not present."""
    if not EXPORT_DIR.exists():
        os.makedirs(EXPORT_DIR, exist_ok=True)


# ── Chart Plotting Functions ──────────────────────────────────────────────────

def plot_bar_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str,
    filename: str
) -> ToolResult:
    """
    Generate a bar chart and save it as a PNG image.

    Args:
        df: Input DataFrame containing the columns to plot.
        x_col: Column name to plot on the X-axis (e.g. categorical).
        y_col: Column name to plot on the Y-axis (e.g. numeric).
        title: Title of the chart.
        filename: Target filename (e.g., 'sales_by_region').
    """
    tool_name = "plot_bar_chart"
    if x_col not in df.columns:
        return ToolResult(success=False, tool_name=tool_name, result=None, description=f"X Column '{x_col}' not found.", error=f"Column '{x_col}' does not exist.")
    if y_col not in df.columns:
        return ToolResult(success=False, tool_name=tool_name, result=None, description=f"Y Column '{y_col}' not found.", error=f"Column '{y_col}' does not exist.")

    try:
        _ensure_export_directory()
        filepath = EXPORT_DIR / f"{filename}.png"
        
        # Aggregate if there are duplicate values in x_col to make the bar visual clean and flat
        if df[x_col].duplicated().any():
            plot_df = df.groupby(x_col)[y_col].sum().reset_index()
        else:
            plot_df = df.copy()
            
        # Sort in descending order for a premium, structured ranking visual
        if pd.api.types.is_numeric_dtype(plot_df[y_col]):
            plot_df = plot_df.sort_values(by=y_col, ascending=False)
            
        # Plot
        fig = px.bar(
            plot_df,
            x=x_col,
            y=y_col,
            color_discrete_sequence=COLOR_SEQUENCE
        )
        
        # Apply custom theme
        fig = _apply_premium_styling(fig, title)
        
        # Save static high-res PNG image
        fig.write_image(str(filepath), format="png", width=1000, height=600, scale=2)
        
        return ToolResult(
            success=True,
            tool_name=tool_name,
            result=str(filepath),
            description=f"Bar chart generated and saved successfully to {filepath}.",
            metadata={"filepath": str(filepath), "x": x_col, "y": y_col}
        )
    except Exception as e:
        return ToolResult(
            success=False,
            tool_name=tool_name,
            result=None,
            description=f"Failed to generate bar chart: {e}",
            error=str(e)
        )


def plot_line_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str,
    filename: str
) -> ToolResult:
    """
    Generate a line chart and save it as a PNG image (best for time-series).

    Args:
        df: Input DataFrame.
        x_col: Column name for X-axis (e.g. datetime).
        y_col: Column name for Y-axis (e.g. numeric).
        title: Title of the chart.
        filename: Target filename.
    """
    tool_name = "plot_line_chart"
    if x_col not in df.columns:
        return ToolResult(success=False, tool_name=tool_name, result=None, description=f"X Column '{x_col}' not found.", error=f"Column '{x_col}' does not exist.")
    if y_col not in df.columns:
        return ToolResult(success=False, tool_name=tool_name, result=None, description=f"Y Column '{y_col}' not found.", error=f"Column '{y_col}' does not exist.")

    try:
        _ensure_export_directory()
        filepath = EXPORT_DIR / f"{filename}.png"
        
        # Plot
        fig = px.line(
            df,
            x=x_col,
            y=y_col,
            color_discrete_sequence=COLOR_SEQUENCE,
            markers=True
        )
        
        # Apply theme
        fig = _apply_premium_styling(fig, title)
        
        # Save
        fig.write_image(str(filepath), format="png", width=1000, height=600, scale=2)
        
        return ToolResult(
            success=True,
            tool_name=tool_name,
            result=str(filepath),
            description=f"Line chart generated and saved successfully to {filepath}.",
            metadata={"filepath": str(filepath), "x": x_col, "y": y_col}
        )
    except Exception as e:
        return ToolResult(
            success=False,
            tool_name=tool_name,
            result=None,
            description=f"Failed to generate line chart: {e}",
            error=str(e)
        )


def plot_pie_chart(
    df: pd.DataFrame,
    names_col: str,
    values_col: str,
    title: str,
    filename: str
) -> ToolResult:
    """
    Generate a pie chart and save it as a PNG image (best for category proportions).

    Args:
        df: Input DataFrame.
        names_col: Column name containing categories/labels.
        values_col: Column name containing slices numeric weights.
        title: Title of the chart.
        filename: Target filename.
    """
    tool_name = "plot_pie_chart"
    if names_col not in df.columns:
        return ToolResult(success=False, tool_name=tool_name, result=None, description=f"Names Column '{names_col}' not found.", error=f"Column '{names_col}' does not exist.")
    if values_col not in df.columns:
        return ToolResult(success=False, tool_name=tool_name, result=None, description=f"Values Column '{values_col}' not found.", error=f"Column '{values_col}' does not exist.")

    try:
        _ensure_export_directory()
        filepath = EXPORT_DIR / f"{filename}.png"
        
        # Aggregate if there are duplicate categories to avoid duplicate slice segments
        if df[names_col].duplicated().any():
            plot_df = df.groupby(names_col)[values_col].sum().reset_index()
        else:
            plot_df = df.copy()
            
        # Plot
        fig = px.pie(
            plot_df,
            names=names_col,
            values=values_col,
            color_discrete_sequence=COLOR_SEQUENCE,
            hole=0.4  # clean donut chart style
        )
        
        # Apply theme
        fig = _apply_premium_styling(fig, title)
        
        # Save
        fig.write_image(str(filepath), format="png", width=1000, height=600, scale=2)
        
        return ToolResult(
            success=True,
            tool_name=tool_name,
            result=str(filepath),
            description=f"Pie chart generated and saved successfully to {filepath}.",
            metadata={"filepath": str(filepath), "names": names_col, "values": values_col}
        )
    except Exception as e:
        return ToolResult(
            success=False,
            tool_name=tool_name,
            result=None,
            description=f"Failed to generate pie chart: {e}",
            error=str(e)
        )


def plot_scatter_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str,
    filename: str
) -> ToolResult:
    """
    Generate a scatter plot and save it as a PNG image (best for correlations/clusters).

    Args:
        df: Input DataFrame.
        x_col: Column name for X-axis (numeric).
        y_col: Column name for Y-axis (numeric).
        title: Title of the chart.
        filename: Target filename.
    """
    tool_name = "plot_scatter_chart"
    if x_col not in df.columns:
        return ToolResult(success=False, tool_name=tool_name, result=None, description=f"X Column '{x_col}' not found.", error=f"Column '{x_col}' does not exist.")
    if y_col not in df.columns:
        return ToolResult(success=False, tool_name=tool_name, result=None, description=f"Y Column '{y_col}' not found.", error=f"Column '{y_col}' does not exist.")

    try:
        _ensure_export_directory()
        filepath = EXPORT_DIR / f"{filename}.png"
        
        # Plot
        fig = px.scatter(
            df,
            x=x_col,
            y=y_col,
            color_discrete_sequence=COLOR_SEQUENCE,
            trendline="ols" if pd.api.types.is_numeric_dtype(df[x_col]) and pd.api.types.is_numeric_dtype(df[y_col]) else None
        )
        
        # Apply theme
        fig = _apply_premium_styling(fig, title)
        
        # Save
        fig.write_image(str(filepath), format="png", width=1000, height=600, scale=2)
        
        return ToolResult(
            success=True,
            tool_name=tool_name,
            result=str(filepath),
            description=f"Scatter chart generated and saved successfully to {filepath}.",
            metadata={"filepath": str(filepath), "x": x_col, "y": y_col}
        )
    except Exception as e:
        return ToolResult(
            success=False,
            tool_name=tool_name,
            result=None,
            description=f"Failed to generate scatter chart: {e}",
            error=str(e)
        )
