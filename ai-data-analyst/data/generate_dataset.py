"""
data/generate_dataset.py — Synthetic Sales Dataset Generator
=============================================================

PURPOSE:
  Generates a realistic sales.csv with 10,000+ rows for development and testing.
  The data contains deliberate patterns so the AI agent can "discover" them:

  BUILT-IN PATTERNS (things the agent should find):
    • March dip       — sales drop ~35% in March (every year)
    • Electronics     — highest revenue but thinner margins
    • Furniture       — highest profit margin
    • South region    — consistently underperforms
    • North region    — consistently leads
    • Customer loyalty — top 20% of customers → 60% of revenue (Pareto)
    • Weekend effect  — 15% lower sales on weekends

  BUILT-IN ANOMALIES (things the outlier detector should catch):
    • ~50 transactions with abnormally high discount (>0.6)
    • ~30 negative-profit rows (sold below cost)
    • ~20 suspiciously large quantity orders

HOW TO RUN:
  python data/generate_dataset.py

  This creates: data/sales.csv

TEACHING NOTE:
  We use numpy's random seed so the data is reproducible.
  Every time you run this script with the same seed, you get the exact
  same dataset. This is important for testing — your agent's answers
  should be deterministic against a fixed dataset.
"""

import random
from pathlib import Path
from datetime import date, timedelta

import numpy as np
import pandas as pd


# ── Configuration ─────────────────────────────────────────────────────────────
SEED = 42               # reproducibility
N_ROWS = 12_000         # ~1 year of daily transactions
OUTPUT_PATH = Path(__file__).parent / "sales.csv"

np.random.seed(SEED)
random.seed(SEED)


# ── Reference Data ────────────────────────────────────────────────────────────

REGIONS = ["North", "South", "East", "West", "Central"]
REGION_WEIGHTS = [0.28, 0.12, 0.22, 0.20, 0.18]   # North dominates, South lags

CATEGORIES = ["Electronics", "Furniture", "Office Supplies", "Clothing", "Food & Beverage"]
CATEGORY_WEIGHTS = [0.30, 0.15, 0.25, 0.18, 0.12]

# (product_name, category, base_price, cost_ratio)
PRODUCTS = [
    # Electronics — high revenue, moderate margin
    ("Laptop Pro 15",        "Electronics",      85000, 0.72),
    ("Wireless Headphones",  "Electronics",       4500, 0.55),
    ("Smartphone X12",       "Electronics",      55000, 0.68),
    ("Smart Watch Ultra",    "Electronics",      25000, 0.60),
    ("Tablet Air",           "Electronics",      35000, 0.65),
    ("Bluetooth Speaker",    "Electronics",       3200, 0.50),
    ("USB-C Hub 7-in-1",     "Electronics",       2800, 0.45),
    # Furniture — lower revenue, best margins
    ("Executive Desk",       "Furniture",        22000, 0.40),
    ("Ergonomic Chair",      "Furniture",        18000, 0.38),
    ("Bookshelf Pro",        "Furniture",         8500, 0.35),
    ("Standing Desk",        "Furniture",        28000, 0.42),
    # Office Supplies — volume play
    ("Premium Pen Set",      "Office Supplies",    450, 0.30),
    ("A4 Paper (500 sheets)","Office Supplies",    280, 0.25),
    ("Stapler Pro",          "Office Supplies",    850, 0.35),
    ("Sticky Notes Pack",    "Office Supplies",    220, 0.28),
    ("Desk Organizer",       "Office Supplies",   1200, 0.33),
    # Clothing
    ("Business Shirt",       "Clothing",          2200, 0.45),
    ("Casual Jeans",         "Clothing",          3500, 0.48),
    ("Running Shoes",        "Clothing",          5800, 0.52),
    ("Winter Jacket",        "Clothing",          8900, 0.55),
    # Food & Beverage
    ("Premium Coffee Beans", "Food & Beverage",    950, 0.40),
    ("Green Tea Pack",       "Food & Beverage",    480, 0.35),
    ("Protein Bars (12pk)",  "Food & Beverage",   1200, 0.42),
]

PRODUCT_NAMES = [p[0] for p in PRODUCTS]
PRODUCT_MAP = {p[0]: {"category": p[1], "price": p[2], "cost_ratio": p[3]}
               for p in PRODUCTS}


def generate_dates(n: int, start: str = "2023-01-01", end: str = "2024-01-31") -> list[date]:
    """
    Generate n random dates between start and end.
    Uses weighted sampling so weekdays get more orders than weekends.
    """
    start_d = date.fromisoformat(start)
    end_d = date.fromisoformat(end)
    all_dates = [start_d + timedelta(days=i) for i in range((end_d - start_d).days + 1)]

    # Weekend effect: weekdays get 1.0 weight, weekends get 0.5
    weights = [0.5 if d.weekday() >= 5 else 1.0 for d in all_dates]
    total = sum(weights)
    probs = [w / total for w in weights]

    chosen = np.random.choice(len(all_dates), size=n, p=probs)
    return [all_dates[i] for i in chosen]


def apply_march_dip(quantity: int, sale_date: date, product: str) -> int:
    """
    Reduce quantity in March by ~35% to simulate seasonal slump.
    This is the KEY PATTERN the agent should discover.
    """
    if sale_date.month == 3:
        # Extra penalty for Electronics in March (mimics supply chain issue)
        if PRODUCT_MAP[product]["category"] == "Electronics":
            quantity = max(1, int(quantity * 0.55))
        else:
            quantity = max(1, int(quantity * 0.68))
    return quantity


def generate_discount(category: str, is_anomaly: bool = False) -> float:
    """Generate a realistic discount. Anomalies get 0.5–0.7 discount."""
    if is_anomaly:
        return round(np.random.uniform(0.50, 0.70), 2)

    base_discounts = {
        "Electronics": (0.00, 0.20),
        "Furniture": (0.05, 0.25),
        "Office Supplies": (0.00, 0.15),
        "Clothing": (0.10, 0.40),
        "Food & Beverage": (0.00, 0.10),
    }
    low, high = base_discounts.get(category, (0.0, 0.2))
    return round(np.random.uniform(low, high), 2)


def build_row(
    order_id: str,
    order_date: date,
    product: str,
    region: str,
    customer_id: str,
    is_anomaly_discount: bool = False,
    is_anomaly_quantity: bool = False,
    is_loss_sale: bool = False,
) -> dict:
    """Build a single sales record with realistic calculations."""
    info = PRODUCT_MAP[product]
    category = info["category"]
    base_price = info["price"]
    cost_ratio = info["cost_ratio"]

    # Quantity
    if is_anomaly_quantity:
        quantity = int(np.random.uniform(50, 200))   # abnormally large
    else:
        # Different product categories have different typical order sizes
        qty_ranges = {
            "Electronics": (1, 5),
            "Furniture": (1, 3),
            "Office Supplies": (5, 50),
            "Clothing": (1, 8),
            "Food & Beverage": (3, 30),
        }
        lo, hi = qty_ranges.get(category, (1, 10))
        quantity = int(np.random.randint(lo, hi + 1))

    quantity = apply_march_dip(quantity, order_date, product)

    # Price with small noise (~±5%)
    unit_price = round(base_price * np.random.uniform(0.95, 1.05), 2)

    # Discount
    discount = generate_discount(category, is_anomaly=is_anomaly_discount)

    # Revenue
    sales = round(unit_price * quantity * (1 - discount), 2)

    # Profit
    unit_cost = base_price * cost_ratio
    if is_loss_sale:
        # Sell below cost — creates negative profit rows
        profit = round(-abs(np.random.uniform(0.05, 0.25)) * sales, 2)
    else:
        gross_profit = (unit_price - unit_cost) * quantity * (1 - discount)
        # Add noise to profit
        profit = round(gross_profit * np.random.uniform(0.85, 1.10), 2)

    return {
        "order_id": order_id,
        "order_date": order_date.isoformat(),
        "product": product,
        "category": category,
        "region": region,
        "customer_id": customer_id,
        "quantity": quantity,
        "unit_price": unit_price,
        "discount": discount,
        "sales": sales,
        "profit": profit,
        "cost": round(unit_cost * quantity, 2),
    }


def generate_dataset(n_rows: int = N_ROWS) -> pd.DataFrame:
    """
    Main generation function.
    Returns a DataFrame with n_rows of realistic sales data.
    """
    print(f"  Generating {n_rows:,} sales records...")

    # Pre-generate dates, products, regions
    dates = generate_dates(n_rows)

    products = np.random.choice(
        PRODUCT_NAMES,
        size=n_rows,
        p=[1 / len(PRODUCT_NAMES)] * len(PRODUCT_NAMES),
    )

    regions = np.random.choice(REGIONS, size=n_rows, p=REGION_WEIGHTS)

    # Customer pool: 500 unique customers, top 20% buy more frequently (Pareto)
    n_customers = 500
    customer_ids = [f"CUST-{i:04d}" for i in range(1, n_customers + 1)]
    # Top 100 customers get 3x more weight
    cust_weights = [3.0] * 100 + [1.0] * 400
    cust_total = sum(cust_weights)
    cust_probs = [w / cust_total for w in cust_weights]
    customers = np.random.choice(customer_ids, size=n_rows, p=cust_probs)

    # Mark anomaly rows
    anomaly_discount_idx = set(np.random.choice(n_rows, size=50, replace=False))
    anomaly_qty_idx = set(np.random.choice(n_rows, size=20, replace=False))
    loss_sale_idx = set(np.random.choice(n_rows, size=30, replace=False))

    rows = []
    for i in range(n_rows):
        order_id = f"ORD-{i+1:06d}"
        row = build_row(
            order_id=order_id,
            order_date=dates[i],
            product=products[i],
            region=regions[i],
            customer_id=customers[i],
            is_anomaly_discount=(i in anomaly_discount_idx),
            is_anomaly_quantity=(i in anomaly_qty_idx),
            is_loss_sale=(i in loss_sale_idx),
        )
        rows.append(row)

    df = pd.DataFrame(rows)

    # Sort by date for realistic time-series appearance
    df = df.sort_values("order_date").reset_index(drop=True)

    # Introduce a small number of missing values (realistic data quality issue)
    null_mask_discount = np.random.choice(df.index, size=25, replace=False)
    null_mask_region = np.random.choice(df.index, size=10, replace=False)
    df.loc[null_mask_discount, "discount"] = np.nan
    df.loc[null_mask_region, "region"] = np.nan

    return df


def print_summary(df: pd.DataFrame) -> None:
    """Print a brief summary of the generated dataset."""
    print("\n  ── Dataset Summary ──────────────────────────────")
    print(f"  Rows          : {len(df):,}")
    print(f"  Columns       : {len(df.columns)}")
    print(f"  Date range    : {df['order_date'].min()} → {df['order_date'].max()}")
    print(f"  Total sales   : ₹{df['sales'].sum():,.2f}")
    print(f"  Total profit  : ₹{df['profit'].sum():,.2f}")
    print(f"  Null values   : {df.isnull().sum().sum()}")
    print(f"  Unique products: {df['product'].nunique()}")
    print(f"  Unique customers: {df['customer_id'].nunique()}")

    print("\n  Monthly Sales (Jan–Dec 2023):")
    df["month"] = pd.to_datetime(df["order_date"]).dt.to_period("M")
    monthly = df[df["order_date"] < "2024-01-01"].groupby("month")["sales"].sum()
    for period, val in monthly.items():
        marker = " <-- DIPS HERE" if str(period).endswith("-03") else ""
        print(f"    {period}: ₹{val:>14,.2f}{marker}")


if __name__ == "__main__":
    print("\n[*]  AI Data Analyst Agent -- Dataset Generator")
    print("=" * 55)

    df = generate_dataset(N_ROWS)
    print_summary(df)

    # Remove helper column before saving
    df = df.drop(columns=["month"], errors="ignore")

    # Save
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)

    print(f"\n  [OK]  Saved to: {OUTPUT_PATH}")
    print(f"  File size : {OUTPUT_PATH.stat().st_size / 1024:.1f} KB\n")
