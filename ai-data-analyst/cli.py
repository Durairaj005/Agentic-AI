"""
cli.py — Interactive CLI Data Analyst
======================================

PURPOSE:
  This is the Phase 1 entry point.
  It's a REPL (Read-Eval-Print Loop) that lets you:
    1. Load a CSV or Excel file
    2. View an automatic dataset profile
    3. Ask analytical questions in plain English
    4. Get results calculated by Pandas

WHAT "PLAIN ENGLISH" MEANS IN PHASE 1:
  Phase 1 doesn't use an LLM. Instead, we parse keywords from your question
  and map them to the appropriate tool function.
  This is called a "rule-based dispatcher" and it teaches you the exact
  mapping that the LLM will automate in Phase 2.

  Example:
    You type:  "total sales"
    CLI sees:  keyword "total" + column "sales"
    It calls:  calculate_sum(df, 'sales')

  In Phase 2:
    You type:  "total sales"
    LLM says:  {"tool": "calculate_sum", "column": "sales"}
    Python calls: calculate_sum(df, 'sales')

  Same result — but Phase 2 is generalised to any question.

HOW TO RUN:
  python cli.py
  python cli.py --file data/sales.csv    # skip file selection prompt

AVAILABLE COMMANDS (type these at the question prompt):
  help                        — show available commands
  profile                     — re-display dataset profile
  total <column>              — calculate sum
  average <column>            — calculate mean
  min <column>                — find minimum
  max <column>                — find maximum
  top <n> <group> by <value>  — top N groups (e.g. "top 5 regions by profit")
  group <group> by <value>    — group_by aggregate
  filter <col> = <value>      — filter rows
  monthly <column>            — monthly time series
  compare <period1> <period2> <column>   — compare two months
  outliers <column>           — detect outliers
  correlate <col1> <col2>     — correlation
  describe <column>           — full stats for a column
  quit / exit                 — exit
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import pandas as pd
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text
from rich import print as rprint

# ── Add project root to path so imports work ─────────────────────────────────
# This is necessary because cli.py is in the project root, not inside backend/
_root = Path(__file__).resolve().parent
sys.path.insert(0, str(_root / "backend"))

from app.profiler.data_profiler import DataProfiler
from app.services.agent_service import AgentService
from app.services.llm_service import (
    LLMQuotaExceededError,
    LLMConnectionError,
    LLMServiceError,
)
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

console = Console()

# ── Banner ────────────────────────────────────────────────────────────────────

BANNER = """
[bold cyan]
  ╔═══════════════════════════════════════════════════════╗
  ║        AI Data Analyst Agent  —  Phase 1 CLI         ║
  ║         Python • Pandas • Rich Terminal               ║
  ╚═══════════════════════════════════════════════════════╝
[/bold cyan]
[dim]  Phase 1: Deterministic analysis without LLM
  Phase 2+ will add: LLM reasoning, LangGraph, FastAPI, React[/dim]
"""

HELP_TEXT = """
[bold yellow]Available Commands:[/bold yellow]

  [cyan]Data[/cyan]
    profile                          Re-display dataset profile
    describe [column]                Full statistics for a column

  [cyan]Aggregation[/cyan]
    total [column]                   Sum of column
    average [column]                 Mean of column
    min [column]                     Minimum value
    max [column]                     Maximum value
    count                            Total row count

  [cyan]Grouping[/cyan]
    top [n] [group_col] by [value_col]
      e.g. top 5 region by profit
      e.g. top 3 category by sales

    group [group_col] by [value_col] [func]
      e.g. group region by sales sum
      e.g. group category by profit mean

  [cyan]Filtering[/cyan]
    filter [col] = [value]           Exact match filter
    filter [col] > [value]           Greater-than filter
    filter [col] < [value]           Less-than filter
      e.g. filter category = Electronics
      e.g. filter sales > 50000

  [cyan]Time Series[/cyan]
    monthly [column]                 Monthly aggregation
    quarterly [column]               Quarterly aggregation
    changes [column]                 Month-over-month % changes
    compare [period1] [period2] [column]
      e.g. compare 2023-02 2023-03 sales

  [cyan]Statistics[/cyan]
    outliers [column]                Detect outliers (IQR)
    correlate [col1] [col2]          Correlation between two columns
    correlations                     Full correlation matrix

  [cyan]System[/cyan]
    help                             Show this help
    columns                          List all column names
    sample                           Show 5 random rows
    quit / exit                      Exit the CLI

[dim]Type a command and press Enter.[/dim]
"""


# ── File Loader ───────────────────────────────────────────────────────────────

def load_file(path: str) -> pd.DataFrame:
    """Load a CSV or Excel file into a DataFrame."""
    p = Path(path)
    if not p.exists():
        console.print(f"[red]❌  File not found: {path}[/red]")
        sys.exit(1)

    suffix = p.suffix.lower()
    with console.status(f"[cyan]Loading {p.name}...[/cyan]"):
        if suffix == ".csv":
            df = pd.read_csv(path)
        elif suffix in (".xlsx", ".xls"):
            df = pd.read_excel(path)
        elif suffix == ".parquet":
            df = pd.read_parquet(path)
        else:
            console.print(f"[red]❌  Unsupported file type: {suffix}[/red]")
            sys.exit(1)

    console.print(f"[green]✅  Loaded '{p.name}' — {len(df):,} rows, {len(df.columns)} columns[/green]")
    return df


# ── Result Printer ────────────────────────────────────────────────────────────

def print_result(result: ToolResult) -> None:
    if not result:
        return

    if not result.success:
        console.print(f"\n[red]❌  Error:[/red] {result.error}\n")
        return

    console.print()
    
    # Custom format for visualization tools
    if result.tool_name and result.tool_name.startswith("plot_"):
        console.print(Panel(
            f"[bold cyan]📊  Visual Asset Generated Successfully![/bold cyan]\n\n"
            f"  • [bold]Tool:[/bold] {result.tool_name}\n"
            f"  • [bold]Saved Path:[/bold] [green]{result.result}[/green]\n"
            f"  • [bold]Resolution:[/bold] 1000x600 px (crisp 2x scaling)\n\n"
            f"[dim]Tip: You can open this file in your image viewer to see the chart.[/dim]",
            border_style="cyan",
            title=f"[bold cyan]Chart Export[/bold cyan]",
            box=box.ROUNDED,
        ))
    else:
        console.print(Panel(
            f"[bold green]{result.description}[/bold green]",
            border_style="green",
            title=f"[dim]{result.tool_name}[/dim]",
        ))

        # If result is a list of dicts → render as table
        data = result.result
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            _print_dict_list_as_table(data)

        # If result is a DataFrame → render as table
        elif isinstance(data, pd.DataFrame):
            _print_dataframe(data.head(20))

    console.print()


def _print_dict_list_as_table(data: list[dict]) -> None:
    """Render a list of dicts as a Rich table."""
    if not data:
        return

    tbl = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan")
    cols = list(data[0].keys())
    for col in cols:
        tbl.add_column(str(col))

    for row in data[:30]:   # cap at 30 rows for readability
        tbl.add_row(*[_fmt(row.get(c)) for c in cols])

    console.print(tbl)
    if len(data) > 30:
        console.print(f"[dim]  ... and {len(data) - 30} more rows[/dim]")


def _print_dataframe(df: pd.DataFrame) -> None:
    """Render a DataFrame as a Rich table (top 20 rows)."""
    tbl = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan")
    for col in df.columns:
        tbl.add_column(str(col))
    for _, row in df.iterrows():
        tbl.add_row(*[_fmt(v) for v in row])
    console.print(tbl)


def _fmt(val: Any) -> str:
    """Format a value for table display."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "[dim]—[/dim]"
    if isinstance(val, float):
        return f"{val:,.2f}"
    if isinstance(val, int):
        return f"{val:,}"
    return str(val)


# ── Command Dispatcher ────────────────────────────────────────────────────────
# TEACHING NOTE:
# This is the CORE of Phase 1. We manually parse the user's text into tool calls.
# In Phase 2, the LLM does this parsing automatically.
# Comparing Phase 1 and Phase 2 side-by-side will help you understand exactly
# what value the LLM adds.

def dispatch_command(df: pd.DataFrame, profile: Any, command: str) -> bool:
    """
    Parse a command string and call the appropriate analysis tool.
    Returns False if the user wants to exit, True otherwise.
    """
    cmd = command.strip()
    if not cmd:
        return True

    parts = cmd.lower().split()
    raw_parts = cmd.split()   # preserve original case for values

    # ── Exit ──────────────────────────────────────────────────────────────
    if parts[0] in ("quit", "exit", "q"):
        console.print("\n[cyan]👋  Goodbye! See you in Phase 2.[/cyan]\n")
        return False

    # ── Help ──────────────────────────────────────────────────────────────
    if parts[0] == "help":
        console.print(HELP_TEXT)
        return True

    # ── Profile ───────────────────────────────────────────────────────────
    if parts[0] == "profile":
        profiler = DataProfiler()
        profiler.display(profile)
        return True

    # ── Columns ───────────────────────────────────────────────────────────
    if parts[0] == "columns":
        cols = df.columns.tolist()
        tbl = Table(title="Dataset Columns", box=box.SIMPLE, header_style="bold cyan")
        tbl.add_column("#", style="dim")
        tbl.add_column("Column", style="cyan")
        tbl.add_column("Dtype", style="yellow")
        for i, col in enumerate(cols, 1):
            tbl.add_row(str(i), col, str(df[col].dtype))
        console.print(tbl)
        return True

    # ── Sample ────────────────────────────────────────────────────────────
    if parts[0] == "sample":
        sample_df = df.sample(min(5, len(df)), random_state=42)
        _print_dataframe(sample_df)
        return True

    # ── Total / Sum ───────────────────────────────────────────────────────
    # "total sales", "sum profit"
    if parts[0] in ("total", "sum") and len(parts) >= 2:
        col = _find_column(df, parts[1])
        if col:
            print_result(calculate_sum(df, col))
        return True

    # ── Average / Mean ────────────────────────────────────────────────────
    if parts[0] in ("average", "mean", "avg") and len(parts) >= 2:
        col = _find_column(df, parts[1])
        if col:
            print_result(calculate_mean(df, col))
        return True

    # ── Min ───────────────────────────────────────────────────────────────
    if parts[0] == "min" and len(parts) >= 2:
        col = _find_column(df, parts[1])
        if col:
            print_result(calculate_min(df, col))
        return True

    # ── Max ───────────────────────────────────────────────────────────────
    if parts[0] == "max" and len(parts) >= 2:
        col = _find_column(df, parts[1])
        if col:
            print_result(calculate_max(df, col))
        return True

    # ── Count ─────────────────────────────────────────────────────────────
    if parts[0] == "count":
        col = parts[1] if len(parts) >= 2 else None
        if col:
            col = _find_column(df, col)
        print_result(calculate_count(df, col))
        return True

    # ── Describe ──────────────────────────────────────────────────────────
    # "describe sales", "describe profit"
    if parts[0] == "describe" and len(parts) >= 2:
        col = _find_column(df, parts[1])
        if col:
            print_result(describe_column(df, col))
        return True

    # ── Top N ─────────────────────────────────────────────────────────────
    # "top 5 region by profit"
    # "top 3 category by sales"
    if parts[0] == "top" and len(parts) >= 5 and parts[3] == "by":
        try:
            n = int(parts[1])
            group_col = _find_column(df, parts[2])
            value_col = _find_column(df, parts[4])
            agg = parts[5] if len(parts) >= 6 else "sum"
            if group_col and value_col:
                print_result(top_n(df, group_col, value_col, n, agg))
        except ValueError:
            console.print("[red]Usage: top [n] [group_col] by [value_col][/red]")
        return True

    # ── Group by ─────────────────────────────────────────────────────────
    # "group region by profit"
    # "group category by sales mean"
    if parts[0] == "group" and len(parts) >= 4 and parts[2] == "by":
        group_col = _find_column(df, parts[1])
        value_col = _find_column(df, parts[3])
        agg = parts[4] if len(parts) >= 5 else "sum"
        if group_col and value_col:
            print_result(group_by(df, group_col, value_col, agg))
        return True

    # ── Filter ────────────────────────────────────────────────────────────
    # "filter category = Electronics"
    # "filter sales > 50000"
    if parts[0] == "filter" and len(parts) >= 4:
        col = _find_column(df, parts[1])
        operator = parts[2]
        value_raw = " ".join(raw_parts[3:])   # preserve original case

        # Try to cast value to number
        try:
            value: Any = float(value_raw)
            if value == int(value):
                value = int(value)
        except ValueError:
            value = value_raw

        if col and operator in ("==", "=", "!=", ">", ">=", "<", "<=", "contains"):
            op = "==" if operator == "=" else operator
            result = filter_rows(df, col, op, value)
            if result.success and isinstance(result.result, pd.DataFrame):
                console.print()
                console.print(Panel(
                    f"[bold green]{result.description}[/bold green]",
                    border_style="green",
                    title="[dim]filter_rows[/dim]",
                ))
                _print_dataframe(result.result.head(20))
                console.print()
        return True

    # ── Monthly ───────────────────────────────────────────────────────────
    # "monthly sales", "monthly profit"
    if parts[0] == "monthly" and len(parts) >= 2:
        val_col = _find_column(df, parts[1])
        date_col = _find_date_column(df)
        if val_col and date_col:
            print_result(time_series_aggregate(df, date_col, val_col, "ME", "sum"))
        return True

    # ── Quarterly ─────────────────────────────────────────────────────────
    if parts[0] == "quarterly" and len(parts) >= 2:
        val_col = _find_column(df, parts[1])
        date_col = _find_date_column(df)
        if val_col and date_col:
            print_result(time_series_aggregate(df, date_col, val_col, "QE", "sum"))
        return True

    # ── Changes / MoM ────────────────────────────────────────────────────
    # "changes sales", "changes profit"
    if parts[0] == "changes" and len(parts) >= 2:
        val_col = _find_column(df, parts[1])
        date_col = _find_date_column(df)
        if val_col and date_col:
            print_result(calculate_percentage_change(df, date_col, val_col, "ME"))
        return True

    # ── Compare ───────────────────────────────────────────────────────────
    # "compare 2023-02 2023-03 sales"
    if parts[0] == "compare" and len(parts) >= 4:
        period1 = parts[1]
        period2 = parts[2]
        val_col = _find_column(df, parts[3])
        date_col = _find_date_column(df)
        if val_col and date_col:
            print_result(compare_periods(df, date_col, val_col, period1, period2))
        return True

    # ── Outliers ──────────────────────────────────────────────────────────
    # "outliers profit", "outliers sales"
    if parts[0] == "outliers" and len(parts) >= 2:
        col = _find_column(df, parts[1])
        if col:
            print_result(detect_outliers(df, col))
        return True

    # ── Correlate ─────────────────────────────────────────────────────────
    # "correlate sales profit"
    if parts[0] == "correlate" and len(parts) >= 3:
        col1 = _find_column(df, parts[1])
        col2 = _find_column(df, parts[2])
        if col1 and col2:
            print_result(calculate_correlation(df, col1, col2))
        return True

    # ── Correlations (full matrix) ────────────────────────────────────────
    if parts[0] in ("correlations", "correlation_matrix"):
        print_result(correlation_matrix(df))
        return True

    # ── Unknown ───────────────────────────────────────────────────────────
    console.print(
        f"\n[yellow]⚠  Unrecognised command: '{cmd}'[/yellow]\n"
        "  Type [bold cyan]help[/bold cyan] to see available commands.\n"
    )
    return True


# ── Column Finder Helpers ─────────────────────────────────────────────────────

def _find_column(df: pd.DataFrame, name: str) -> str | None:
    """
    Find a column by name (case-insensitive, partial match).
    Prints a helpful error if not found.
    """
    # Exact match first
    if name in df.columns:
        return name

    # Case-insensitive exact
    for col in df.columns:
        if col.lower() == name.lower():
            return col

    # Partial match
    matches = [col for col in df.columns if name.lower() in col.lower()]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        console.print(
            f"[yellow]⚠  Ambiguous column '{name}'. Matches: {matches}. "
            f"Please be more specific.[/yellow]"
        )
        return None

    console.print(
        f"[red]❌  Column '{name}' not found.[/red]\n"
        f"  Available: [cyan]{', '.join(df.columns)}[/cyan]"
    )
    return None


def _find_date_column(df: pd.DataFrame) -> str | None:
    """Auto-detect the date column from the profile."""
    date_hints = ["date", "time", "datetime", "timestamp", "ordered", "created"]
    for hint in date_hints:
        for col in df.columns:
            if hint in col.lower():
                return col

    # Fall back: try any datetime-typed column
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            return col

    console.print(
        "[yellow]⚠  Could not auto-detect date column.\n"
        "  Please ensure your dataset has a column with 'date' or 'time' in the name.[/yellow]"
    )
    return None


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    """Entry point."""
    # ── CLI argument parsing ──────────────────────────────────────────────
    parser = argparse.ArgumentParser(description="AI Data Analyst Agent — Phase 1 CLI")
    parser.add_argument("--file", "-f", type=str, help="Path to CSV/Excel file")
    args = parser.parse_args()

    # ── Banner ────────────────────────────────────────────────────────────
    console.print(BANNER)

    # ── File selection ────────────────────────────────────────────────────
    if args.file:
        file_path = args.file
    else:
        file_path = Prompt.ask(
            "[bold cyan]Enter path to your CSV or Excel file[/bold cyan]",
            default="data/sales.csv",
        )

    df = load_file(file_path)

    # ── Profiling ─────────────────────────────────────────────────────────
    console.print()
    console.print("[cyan]🔍  Profiling dataset...[/cyan]")
    profiler = DataProfiler()
    profile = profiler.profile(df, Path(file_path).name)
    profiler.display(profile)

    # ── Intro instructions ────────────────────────────────────────────────
    console.print(Panel(
        "Type [bold cyan]help[/bold cyan] to see all commands.\n"
        "Type [bold cyan]quit[/bold cyan] to exit.\n\n"
        "Example commands:\n"
        "  [dim]total sales[/dim]\n"
        "  [dim]top 5 region by profit[/dim]\n"
        "  [dim]monthly sales[/dim]\n"
        "  [dim]compare 2023-02 2023-03 sales[/dim]\n"
        "  [dim]outliers profit[/dim]",
        border_style="cyan",
        title="[bold]Quick Start[/bold]",
    ))

    # Initialize AgentService
    agent_service = None
    try:
        agent_service = AgentService(df, Path(file_path).name)
        console.print(f"[green]🤖  AI Agent initialized with {agent_service.llm.provider.title()} routing.[/green]")
    except Exception as e:
        console.print(
            f"[yellow]⚠  Could not initialize Agent Service: {e}\n"
            "  Running in Local Fallback mode (keyword parsing only).[/yellow]"
        )

    # ── REPL loop ─────────────────────────────────────────────────────────
    while True:
        try:
            command = Prompt.ask("\n[bold yellow]analyst>[/bold yellow]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[cyan]👋  Goodbye![/cyan]\n")
            break

        cmd_stripped = command.strip()
        if not cmd_stripped:
            continue

        # Check if it is a built-in system command
        first_word = cmd_stripped.lower().split()[0]
        system_cmds = {"quit", "exit", "q", "help", "profile", "columns", "sample"}

        if first_word in system_cmds:
            should_continue = dispatch_command(df, profile, command)
            if not should_continue:
                break
            continue

        # Route via Agent Workflow
        if agent_service is not None:
            with console.status("[cyan]AI Agent is thinking...[/cyan]"):
                try:
                    explanation, tool_res, errors = agent_service.run(cmd_stripped)
                    
                    # If the agent went through correction cycles, print the log
                    if errors:
                        console.print()
                        console.print(Panel(
                            "\n".join(f"[dim]• Attempt {i+1} failed: [yellow]{err}[/yellow][/dim]" for i, err in enumerate(errors)),
                            title="[bold yellow]⚠ Agent Self-Correction Log[/bold yellow]",
                            border_style="yellow",
                            box=box.ROUNDED,
                        ))
                    
                    # If a tool was executed, print its raw execution results first
                    if tool_res is not None:
                        print_result(tool_res)
                    
                    # Print the LLM's final synthesized explanation
                    console.print()
                    console.print(Panel(
                        explanation or "[dim]No explanation returned.[/dim]",
                        title="[bold cyan]AI Analyst Response[/bold cyan]",
                        border_style="cyan",
                        box=box.ROUNDED,
                    ))
                    continue
                except (LLMQuotaExceededError, LLMConnectionError) as e:
                    console.print()
                    console.print(Panel(
                        f"[bold yellow]⚠  Gemini/Groq API Quota Exceeded or Offline: {e}[/bold yellow]\n"
                        "[dim]Gracefully falling back to rule-based keyword routing...[/dim]",
                        border_style="yellow",
                        title="[yellow]Fallback Triggered[/yellow]",
                    ))
                except LLMServiceError as e:
                    console.print(f"\n[red]❌  Agent Service Error:[/red] {e}")
                    console.print("[dim]Falling back to rule-based parser...[/dim]")

        # Fallback to Phase 1 keyword matching dispatcher
        should_continue = dispatch_command(df, profile, command)
        if not should_continue:
            break


if __name__ == "__main__":
    main()
