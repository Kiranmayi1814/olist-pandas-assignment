"""
DataKern | Assignment 5 | SELF-CHECK
Run:  python check_my_work.py          (from this folder, with your venv active)

It runs YOUR functions from pipeline.py and compares them with an independent answer
computed in pandas straight from the CSV files. A green check means "matches the
oracle", not "your design is good": the README's Validate section covers the rest.
Functions you have not written yet show as TODO.
"""
import sys
import traceback
from pathlib import Path

import pandas as pd

import helpers as h
import pipeline as p

passed = failed = todo = 0


def check(name, fn):
    global passed, failed, todo
    try:
        problems = fn()
    except NotImplementedError:
        todo += 1
        print(f"  TODO  {name}")
        return None
    except Exception as e:  # noqa: BLE001 - we want to show any student error
        failed += 1
        print(f"  FAIL  {name}: {type(e).__name__}: {str(e).splitlines()[0][:200]}")
        if "-v" in sys.argv:
            traceback.print_exc()
        return None
    if problems:
        failed += 1
        print(f"  FAIL  {name}")
        for line in problems:
            print(f"          - {line}")
    else:
        passed += 1
        print(f"  PASS  {name}")


# ------------------------------------------------------------------ oracle (pandas)
def oracle():
    d = h.DATA_DIR
    items = pd.read_csv(d / "olist_order_items_dataset.csv")
    orders = pd.read_csv(d / "olist_orders_dataset.csv", parse_dates=["order_purchase_timestamp"])
    cust = pd.read_csv(d / "olist_customers_dataset.csv")
    prod = pd.read_csv(d / "olist_products_dataset.csv")[["product_id", "product_category_name"]]
    tr = pd.read_csv(d / "product_category_name_translation.csv")
    s = (
        items.merge(orders, on="order_id")
        .merge(cust, on="customer_id")
        .merge(prod, on="product_id", how="left")
        .merge(tr, on="product_category_name", how="left")
    )
    s["category"] = s["product_category_name_english"].fillna("unknown")
    s["purchase_ts"] = s["order_purchase_timestamp"]
    s["year_month"] = s["purchase_ts"].dt.strftime("%Y-%m")
    return items, s


def rows(df, cols):
    return [tuple(r[c] for c in cols) for r in df.select(*cols).collect()]


def close(a, b, tol=0.011):
    if a is None or b is None or pd.isna(a) or pd.isna(b):
        return (a is None or pd.isna(a)) and (b is None or pd.isna(b))
    return abs(a - b) <= tol


print("DataKern Assignment 5: self-check\n")
spark = h.get_spark("assignment 5 check")
items, S = oracle()
work = h.OUT_DIR / "_check"
state = {}

# ------------------------------------------------------------------ Part 1
def c_sales():
    df = p.build_sales(spark)
    state["sales"] = df.cache()
    bad = []
    if sorted(df.columns) != sorted(p.SALES_COLUMNS):
        bad.append(f"columns must be exactly {p.SALES_COLUMNS}, you have {df.columns}")
        return bad
    n = df.count()
    if n != len(items):
        bad.append(f"{n:,} rows, expected {len(items):,} (one row per order item). A join dropped or duplicated rows.")
    if df.filter("category is null").count():
        bad.append("some category values are null: use 'unknown' for items without an English category")
    if df.dropDuplicates(["order_id", "order_item_id"]).count() != n:
        bad.append("duplicate (order_id, order_item_id) pairs: a join multiplied rows")
    total = df.agg({"price": "sum"}).collect()[0][0]
    if not close(total, S["price"].sum(), 1.0):
        bad.append(f"sum(price) = {total:,.2f}, expected {S['price'].sum():,.2f}")
    types = dict(df.dtypes)
    if types.get("price") != "double" or not types.get("purchase_ts", "").startswith("timestamp"):
        bad.append(f"price must be double and purchase_ts a timestamp, you have {types}")
    return bad


check("1  build_sales: right shape, no lost or duplicated rows", c_sales)
if "sales" not in state:
    print("\nFix build_sales first: everything else needs it.")
    sys.exit(1)
sales = state["sales"]

# ------------------------------------------------------------------ Part 2
silver = work / "silver"


def c_silver():
    h.fresh_dir(silver)
    p.write_silver(sales, silver)
    bad = []
    folders = sorted(x.name for x in silver.iterdir() if x.is_dir())
    months = sorted(S["year_month"].unique())
    if folders != [f"year_month={m}" for m in months]:
        bad.append(f"expected one folder per month ({len(months)}), found {folders[:3]}... ({len(folders)} folders)")
        return bad
    for f in folders:
        n = h.count_files(silver / f)
        if n != 1:
            bad.append(f"{f} has {n} parquet files, expected exactly 1 (tidy write)")
            break
    back = spark.read.parquet(h.uri(silver))
    if back.count() != sales.count():
        bad.append("row count after read-back differs from sales")
    if "year_month" not in back.columns:
        bad.append("year_month column is missing after read-back")
    return bad


def c_compare():
    r = p.compare_csv_parquet(sales, work / "compare")
    bad = []
    for k in ("csv_mb", "parquet_mb", "csv_files", "parquet_files"):
        if k not in r:
            bad.append(f"result is missing key '{k}'")
    if bad:
        return bad
    if not (0 < r["parquet_mb"] < r["csv_mb"]):
        bad.append(f"Parquet ({r['parquet_mb']:.1f} MB) should be smaller than CSV ({r['csv_mb']:.1f} MB)")
    if r["csv_files"] < 1 or r["parquet_files"] < 1:
        bad.append("file counts must be at least 1")
    return bad


check("2a write_silver: one folder per month, one file per folder", c_silver)
check("2b compare_csv_parquet: sizes measured on disk", c_compare)

# ------------------------------------------------------------------ Part 3
def c_latest():
    df = p.latest_order_per_customer(sales)
    bad = []
    if sorted(df.columns) != ["customer_unique_id", "order_id", "purchase_ts"]:
        return [f"columns must be customer_unique_id, order_id, purchase_ts; you have {df.columns}"]
    exp = (
        S.sort_values(["purchase_ts", "order_id"], ascending=False)
        .drop_duplicates("customer_unique_id")[["customer_unique_id", "order_id"]]
    )
    got = {r["customer_unique_id"]: r["order_id"] for r in df.collect()}
    if df.count() != len(exp):
        bad.append(f"{df.count():,} rows, expected {len(exp):,} (one row per customer_unique_id)")
    wrong = sum(1 for c, o in zip(exp["customer_unique_id"], exp["order_id"]) if got.get(c) != o)
    if wrong:
        bad.append(f"{wrong:,} customers have the wrong 'latest' order (check sort direction and tie-break)")
    return bad


def c_top3():
    df = p.top3_products_per_category(sales)
    need = {"category", "product_id", "revenue", "rank"}
    if not need <= set(df.columns):
        return [f"columns must include {sorted(need)}; you have {df.columns}"]
    rev = S.groupby(["category", "product_id"], as_index=False)["price"].sum().rename(columns={"price": "revenue"})
    rev["revenue"] = rev["revenue"].round(2)
    rev = rev.sort_values(["category", "revenue", "product_id"], ascending=[True, False, True])
    rev["rank"] = rev.groupby("category").cumcount() + 1
    exp = {(r.category, r.product_id): r.rank for r in rev[rev["rank"] <= 3].itertuples()}
    got = {(r["category"], r["product_id"]): r["rank"] for r in df.collect()}
    bad = []
    if len(got) != len(exp):
        bad.append(f"{len(got)} rows, expected {len(exp)} (top 3 per category, fewer if a category has fewer products)")
    if got != exp:
        bad.append("some (category, product, rank) triples differ: revenue = round(sum(price), 2), "
                   "ties broken by product_id ascending")
    return bad


def c_monthly():
    df = p.seller_monthly(sales)
    cols = ["seller_id", "year_month", "month_revenue", "prev_month_revenue", "mom_growth_pct", "running_revenue"]
    if sorted(df.columns) != sorted(cols):
        return [f"columns must be exactly {cols}; you have {df.columns}"]
    m = S.groupby(["seller_id", "year_month"], as_index=False)["price"].sum().rename(columns={"price": "month_revenue"})
    m["month_revenue"] = m["month_revenue"].round(2)
    m = m.sort_values(["seller_id", "year_month"])
    g = m.groupby("seller_id")["month_revenue"]
    m["prev"] = g.shift(1)
    m["growth"] = ((m["month_revenue"] - m["prev"]) / m["prev"] * 100).round(1)
    m["running"] = g.cumsum().round(2)
    exp = {(r.seller_id, r.year_month): r for r in m.itertuples()}
    got = {(r["seller_id"], r["year_month"]): r for r in df.collect()}
    bad = []
    if set(got) != set(exp):
        return [f"{len(got):,} (seller, month) rows, expected {len(exp):,}"]
    for col, ecol, tol in (("month_revenue", "month_revenue", 0.011), ("prev_month_revenue", "prev", 0.011),
                           ("mom_growth_pct", "growth", 0.11), ("running_revenue", "running", 0.05)):
        wrong = sum(1 for k, e in exp.items() if not close(got[k][col], getattr(e, ecol), tol))
        if wrong:
            bad.append(f"column {col}: {wrong:,} rows differ from the oracle")
    return bad


check("3a latest_order_per_customer", c_latest)
check("3b top3_products_per_category", c_top3)
check("3c seller_monthly (lag, growth, running total)", c_monthly)

# ------------------------------------------------------------------ Part 4
def c_month():
    ym = "2018-03"
    df = p.read_month(spark, silver, ym)
    bad = []
    n, exp = df.count(), int((S["year_month"] == ym).sum())
    if n != exp:
        bad.append(f"{n:,} rows for {ym}, expected {exp:,}")
    plan = h.plan_text(df)
    if "PartitionFilters: []" in plan or "PartitionFilters" not in plan or "year_month" not in plan.split("PartitionFilters")[1][:200]:
        bad.append("the plan shows NO partition filter on year_month: Spark would read every folder. "
                   "Print h.plan_text(df) and look at the FileScan line.")
    return bad


check("4  read_month: partition pruning is visible in the plan", c_month)

# ------------------------------------------------------------------ Part 5
def c_bands():
    bad = []
    exp = (
        pd.cut(S["price"], [-1, 19.999999, 99.999999, 1e12], labels=["budget", "mid", "premium"])
        .value_counts().to_dict()
    )
    for label, fn, needs_udf in (("built-in", p.add_price_band_builtin, False), ("UDF", p.add_price_band_udf, True)):
        df = fn(sales)
        got = {r["price_band"]: r["count"] for r in df.groupBy("price_band").count().collect()}
        if got != {k: int(v) for k, v in exp.items()}:
            bad.append(f"{label}: band counts {got} differ from expected {exp}")
        has_udf = "EvalPython" in h.plan_text(df)
        if needs_udf and not has_udf:
            bad.append("add_price_band_udf does not use a Python UDF (plan has no EvalPython node)")
        if not needs_udf and has_udf:
            bad.append("add_price_band_builtin must use built-in functions only, but the plan has a Python UDF")
    return bad


check("5  price bands: built-in and UDF agree, and really are different", c_bands)

# ------------------------------------------------------------------ Part 6
def c_gold():
    gold = work / "gold"
    h.fresh_dir(gold)
    tables = {
        "latest_order": p.latest_order_per_customer(sales),
        "top3_products": p.top3_products_per_category(sales),
        "seller_monthly": p.seller_monthly(sales),
    }
    p.write_gold(tables, gold)
    bad = []
    for name, df in tables.items():
        folder = gold / name
        n = h.count_files(folder) if folder.exists() else 0
        if n != 1:
            bad.append(f"gold/{name} has {n} parquet files, expected exactly 1")
            continue
        if any("=" in x.name for x in folder.iterdir()):
            bad.append(f"gold/{name} has partition sub-folders: these tables are small, do not partitionBy")
        back = spark.read.parquet(h.uri(folder))
        if back.count() != df.count() or sorted(back.columns) != sorted(df.columns):
            bad.append(f"gold/{name}: read-back rows or columns differ from what you wrote")
    return bad


check("6  write_gold: small tables, one tidy file each, no partition folders", c_gold)

print(f"\n{passed} passed, {failed} failed, {todo} still TODO")
if failed == 0 and todo == 0:
    print("All green. Now do the Validate section of the README: the checker cannot judge your reasoning.")
spark.stop()
sys.exit(1 if failed else 0)
