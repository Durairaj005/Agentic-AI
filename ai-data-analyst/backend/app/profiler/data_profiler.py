"""
profiler/data_profiler.py — Dataset Profiler
=============================================

PURPOSE:
  The DataProfiler is the FIRST thing that runs after a dataset is uploaded.
  It produces a structured summary of the dataset WITHOUT sending any data
  to an LLM — everything here is pure Python/Pandas.

WHY DETERMINISTIC PROFILING MATTERS:
  • The Manager Agent (Phase 3) needs to know column names, types, and
    data ranges to write an analysis plan. It reads the profile, not the CSV.
  • The LLM never sees raw data rows — it only sees the profile + aggregated
    results. This is how we handle large datasets safely.
  • The profile is cached in Redis (Phase 7) so repeated questions about the
    same dataset don't re-read the file.

WHAT IT DETECTS:
  • Row/column counts
  • Column data types (auto-detected: numeric, categorical, date, boolean)
  • Missing values per column
  • Duplicate rows
  • Unique values per categorical column (up to top 20)
  • Descriptive statistics (mean, std, min, max, quartiles) for numerics
  • Potential outliers using the IQR method for numerics
  • Date range detection for date columns

HOW TO USE:
  from app.profiler.data_profiler import DataProfiler

  profiler = DataProfiler()
  profile = profiler.profile(df)
  profiler.display(profile)      # pretty-print in terminal

DATA STRUCTURES:
  The profile is returned as a plain Python dict so it can be:
  • JSON-serialised for the REST API (Phase 5)
  • Stored in the database (Phase 6)
  • Passed as context to the LLM (Phase 2)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any

import numpy as np
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()


# ── Data Classes ─────────────────────────────────────────────────────────────

@dataclass
class ColumnProfile:
    """Profile of a single column."""
    name: str
    dtype_raw: str                  # pandas dtype string e.g. "int64", "object"
    dtype_category: str             # "numeric" | "categorical" | "date" | "boolean"
    missing_count: int
    missing_pct: float
    unique_count: int

    # Numeric-only fields
    mean: float | None = None
    std: float | None = None
    min_val: float | None = None
    max_val: float | None = None
    q25: float | None = None
    median: float | None = None
    q75: float | None = None
    outlier_count: int | None = None

    # Categorical-only fields
    top_values: list[dict] | None = None   # [{"value": "North", "count": 3200}]

    # Date-only fields
    date_min: str | None = None
    date_max: str | None = None
    date_range_days: int | None = None


@dataclass
class DatasetProfile:
    """Full profile of a dataset."""
    file_name: str
    total_rows: int
    total_columns: int
    duplicate_rows: int
    total_missing: int
    total_missing_pct: float
    memory_mb: float

    numeric_columns: list[str] = field(default_factory=list)
    categorical_columns: list[str] = field(default_factory=list)
    date_columns: list[str] = field(default_factory=list)
    boolean_columns: list[str] = field(default_factory=list)

    columns: list[ColumnProfile] = field(default_factory=list)

    # Convenience dict for fast lookup by column name
    column_map: dict[str, ColumnProfile] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to plain dict (for JSON serialisation / LLM context)."""
        d = asdict(self)
        d.pop("column_map", None)  # not serialisable directly
        return d

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)


# ── Profiler ─────────────────────────────────────────────────────────────────

class DataProfiler:
    """
    Profiles a pandas DataFrame and returns a DatasetProfile.

    The profiler is intentionally stateless — you can reuse the same
    instance for multiple DataFrames without side effects.
    """

    # Columns whose names suggest they are date columns even if pandas
    # doesn't auto-detect them as datetime
    _DATE_HINTS = {"date", "time", "datetime", "timestamp", "created", "updated",
                   "ordered", "shipped", "delivered"}

    def profile(self, df: pd.DataFrame, file_name: str = "unknown.csv") -> DatasetProfile:
        """
        Run a full profile on the given DataFrame.

        Args:
            df:         The pandas DataFrame to profile.
            file_name:  Original filename (for display).

        Returns:
            DatasetProfile — a structured, serialisable profile object.
        """
        n_rows, n_cols = df.shape
        duplicate_rows = int(df.duplicated().sum())
        total_missing = int(df.isnull().sum().sum())
        total_cells = n_rows * n_cols
        total_missing_pct = round(total_missing / total_cells * 100, 2) if total_cells else 0.0
        memory_mb = round(df.memory_usage(deep=True).sum() / 1024 / 1024, 3)

        # Try to parse date-like columns
        df = self._coerce_dates(df)

        column_profiles: list[ColumnProfile] = []
        numeric_cols, cat_cols, date_cols, bool_cols = [], [], [], []

        for col in df.columns:
            cp = self._profile_column(df, col, n_rows)
            column_profiles.append(cp)

            if cp.dtype_category == "numeric":
                numeric_cols.append(col)
            elif cp.dtype_category == "categorical":
                cat_cols.append(col)
            elif cp.dtype_category == "date":
                date_cols.append(col)
            elif cp.dtype_category == "boolean":
                bool_cols.append(col)

        col_map = {cp.name: cp for cp in column_profiles}

        return DatasetProfile(
            file_name=file_name,
            total_rows=n_rows,
            total_columns=n_cols,
            duplicate_rows=duplicate_rows,
            total_missing=total_missing,
            total_missing_pct=total_missing_pct,
            memory_mb=memory_mb,
            numeric_columns=numeric_cols,
            categorical_columns=cat_cols,
            date_columns=date_cols,
            boolean_columns=bool_cols,
            columns=column_profiles,
            column_map=col_map,
        )

    # ── Private Helpers ──────────────────────────────────────────────────────

    def _coerce_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Try to parse object columns that look like dates into datetime.
        We use column-name hints and attempt a parse on a sample.
        """
        df = df.copy()
        for col in df.columns:
            if df[col].dtype == object:
                lower = col.lower()
                is_hint = any(hint in lower for hint in self._DATE_HINTS)
                if is_hint:
                    try:
                        df[col] = pd.to_datetime(df[col], infer_datetime_format=True)
                    except (ValueError, TypeError):
                        pass  # leave as string
        return df

    def _profile_column(self, df: pd.DataFrame, col: str, n_rows: int) -> ColumnProfile:
        """Build a ColumnProfile for a single column."""
        series = df[col]
        dtype_raw = str(series.dtype)
        missing_count = int(series.isnull().sum())
        missing_pct = round(missing_count / n_rows * 100, 2) if n_rows else 0.0
        unique_count = int(series.nunique(dropna=True))

        # ── Classify dtype ────────────────────────────────────────────────
        if pd.api.types.is_bool_dtype(series):
            dtype_cat = "boolean"
        elif pd.api.types.is_datetime64_any_dtype(series):
            dtype_cat = "date"
        elif pd.api.types.is_numeric_dtype(series):
            dtype_cat = "numeric"
        else:
            dtype_cat = "categorical"

        base = ColumnProfile(
            name=col,
            dtype_raw=dtype_raw,
            dtype_category=dtype_cat,
            missing_count=missing_count,
            missing_pct=missing_pct,
            unique_count=unique_count,
        )

        # ── Numeric enrichment ────────────────────────────────────────────
        if dtype_cat == "numeric":
            clean = series.dropna()
            if len(clean) > 0:
                q25 = float(clean.quantile(0.25))
                q75 = float(clean.quantile(0.75))
                iqr = q75 - q25
                lower_fence = q25 - 1.5 * iqr
                upper_fence = q75 + 1.5 * iqr
                outlier_count = int(((clean < lower_fence) | (clean > upper_fence)).sum())

                base.mean = round(float(clean.mean()), 4)
                base.std = round(float(clean.std()), 4)
                base.min_val = round(float(clean.min()), 4)
                base.max_val = round(float(clean.max()), 4)
                base.q25 = round(q25, 4)
                base.median = round(float(clean.median()), 4)
                base.q75 = round(q75, 4)
                base.outlier_count = outlier_count

        # ── Categorical enrichment ────────────────────────────────────────
        elif dtype_cat == "categorical":
            vc = series.value_counts(dropna=True).head(20)
            base.top_values = [
                {"value": str(v), "count": int(c)} for v, c in vc.items()
            ]

        # ── Date enrichment ───────────────────────────────────────────────
        elif dtype_cat == "date":
            clean = series.dropna()
            if len(clean) > 0:
                base.date_min = str(clean.min().date())
                base.date_max = str(clean.max().date())
                base.date_range_days = (clean.max() - clean.min()).days

        return base

    # ── Display ──────────────────────────────────────────────────────────────

    def display(self, profile: DatasetProfile) -> None:
        """
        Pretty-print the profile to the terminal using Rich.
        This is what the CLI shows after loading a file.
        """
        console.print()
        console.print(Panel(
            f"[bold cyan]📊 Dataset Profile[/bold cyan]\n"
            f"[white]{profile.file_name}[/white]",
            border_style="cyan"
        ))

        # ── Overview table ────────────────────────────────────────────────
        overview = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
        overview.add_column(style="bold yellow")
        overview.add_column(style="white")

        overview.add_row("Rows",         f"{profile.total_rows:,}")
        overview.add_row("Columns",      f"{profile.total_columns}")
        overview.add_row("Duplicate rows", f"{profile.duplicate_rows:,}")
        overview.add_row("Total missing", f"{profile.total_missing:,} ({profile.total_missing_pct}%)")
        overview.add_row("Memory usage",  f"{profile.memory_mb:.2f} MB")
        overview.add_row("Numeric cols",  ", ".join(profile.numeric_columns) or "—")
        overview.add_row("Categorical",   ", ".join(profile.categorical_columns) or "—")
        overview.add_row("Date cols",     ", ".join(profile.date_columns) or "—")

        console.print(overview)

        # ── Per-column table ──────────────────────────────────────────────
        tbl = Table(
            title="Column Details",
            box=box.ROUNDED,
            show_lines=True,
            header_style="bold magenta",
        )
        tbl.add_column("Column",    style="cyan", no_wrap=True)
        tbl.add_column("Type",      style="yellow")
        tbl.add_column("Missing",   justify="right")
        tbl.add_column("Unique",    justify="right")
        tbl.add_column("Stats / Top Values", style="dim")

        for cp in profile.columns:
            # Missing display
            missing_str = (
                f"{cp.missing_count} ({cp.missing_pct}%)"
                if cp.missing_count > 0
                else "[green]0[/green]"
            )

            # Stats / values display
            if cp.dtype_category == "numeric":
                extra = (
                    f"mean={cp.mean:,.2f}  "
                    f"std={cp.std:,.2f}  "
                    f"min={cp.min_val:,.2f}  "
                    f"max={cp.max_val:,.2f}"
                )
                if cp.outlier_count:
                    extra += f"  [red]outliers={cp.outlier_count}[/red]"
            elif cp.dtype_category == "categorical" and cp.top_values:
                top3 = cp.top_values[:3]
                extra = "  |  ".join(f"{t['value']} ({t['count']:,})" for t in top3)
            elif cp.dtype_category == "date":
                extra = f"{cp.date_min} → {cp.date_max}  ({cp.date_range_days} days)"
            else:
                extra = ""

            tbl.add_row(cp.name, cp.dtype_category, missing_str, str(cp.unique_count), extra)

        console.print(tbl)
        console.print()
