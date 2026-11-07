"""
DataKern | Assignment 5 | Olist seller scorecard: windows and Parquet

Run the whole thing:   python pipeline.py
Check yourself:        python check_my_work.py
"""
from pathlib import Path

from pyspark.sql import functions as F
from pyspark.sql.window import Window
from pyspark.sql.types import StringType

from helpers import OUT_DIR, count_files, csv_path, folder_size_mb, fresh_dir, get_spark, plan_text, timed, uri

# Explicit schemas (given). A CSV has no types, and column ORDER matters: Spark matches by position.
ORDERS_DDL = (
    "order_id STRING, customer_id STRING, order_status STRING, order_purchase_timestamp TIMESTAMP, "
    "order_approved_at TIMESTAMP, order_delivered_carrier_date TIMESTAMP, "
    "order_delivered_customer_date TIMESTAMP, order_estimated_delivery_date TIMESTAMP"
)
ITEMS_DDL = (
    "order_id STRING, order_item_id INT, product_id STRING, seller_id STRING, "
    "shipping_limit_date TIMESTAMP, price DOUBLE, freight_value DOUBLE"
)
CUSTOMERS_DDL = (
    "customer_id STRING, customer_unique_id STRING, customer_zip_code_prefix STRING, "
    "customer_city STRING, customer_state STRING"
)
PRODUCTS_DDL = (
    "product_id STRING, product_category_name STRING, product_name_lenght INT, "
    "product_description_lenght INT, product_photos_qty INT, product_weight_g INT, "
    "product_length_cm INT, product_height_cm INT, product_width_cm INT"
)
TRANSLATION_DDL = "product_category_name STRING, product_category_name_english STRING"

# The columns of the "sales" table you build in Part 1 (one row per order item).
SALES_COLUMNS = [
    "order_id", "order_item_id", "customer_unique_id", "purchase_ts", "seller_id",
    "product_id", "category", "price", "freight_value", "state",
]


# ============================================================================ PART 1
def build_sales(spark):
    """Read the five CSV files and return ONE wide DataFrame with exactly SALES_COLUMNS.

    Items is the "driver" table (one row per order item = the grain we must keep), so every
    join is a LEFT join from items: an item with no match is kept, never dropped.
    Measured on this data: an inner join to the translation table would lose 1,627 items.
    """
    orders = spark.read.csv(csv_path("olist_orders_dataset.csv"), schema=ORDERS_DDL, header=True)
    items = spark.read.csv(csv_path("olist_order_items_dataset.csv"), schema=ITEMS_DDL, header=True)
    customers = spark.read.csv(csv_path("olist_customers_dataset.csv"), schema=CUSTOMERS_DDL, header=True)
    products = spark.read.csv(csv_path("olist_products_dataset.csv"), schema=PRODUCTS_DDL, header=True)
    translation = spark.read.csv(csv_path("product_category_name_translation.csv"), schema=TRANSLATION_DDL, header=True)

    return (
        items
        .join(orders, on="order_id", how="left")
        .join(customers, on="customer_id", how="left")
        .join(products, on="product_id", how="left")
        .join(translation, on="product_category_name", how="left")
        .select(
            F.col("order_id"),
            F.col("order_item_id"),
            F.col("customer_unique_id"),
            F.col("order_purchase_timestamp").alias("purchase_ts"),
            F.col("seller_id"),
            F.col("product_id"),
            F.coalesce(F.col("product_category_name_english"), F.lit("unknown")).alias("category"),
            F.col("price"),
            F.col("freight_value"),
            F.col("customer_state").alias("state"),
        )
    )


# ============================================================================ PART 2
def write_silver(sales, silver_path):
    """Write `sales` as Parquet, one folder per month, ONE tidy file per folder.

    Two ingredients, in this order:
      1. repartition("year_month")  -> memory: all rows of one month land in the same partition
      2. partitionBy("year_month")  -> disk:   one folder per month
    One memory partition per month = one file per folder. mode("overwrite") makes a re-run clean.
    """
    with_month = sales.withColumn("year_month", F.date_format(F.col("purchase_ts"), "yyyy-MM"))
    (
        with_month
        .repartition("year_month")
        .write
        .mode("overwrite")
        .partitionBy("year_month")
        .parquet(uri(silver_path))
    )


def compare_csv_parquet(sales, workdir):
    """Write `sales` as CSV (with header) and as plain Parquet; return sizes and file counts on disk."""
    csv_dir = Path(workdir) / "sales_csv"
    parquet_dir = Path(workdir) / "sales_parquet"
    fresh_dir(csv_dir)
    fresh_dir(parquet_dir)

    sales.coalesce(1).write.mode("overwrite").option("header", True).csv(uri(csv_dir))
    sales.coalesce(1).write.mode("overwrite").parquet(uri(parquet_dir))

    return {
        "csv_mb": folder_size_mb(csv_dir),
        "parquet_mb": folder_size_mb(parquet_dir),
        "csv_files": count_files(csv_dir, ".csv"),
        "parquet_files": count_files(parquet_dir, ".parquet"),
    }


# ============================================================================ PART 3
def latest_order_per_customer(sales):
    """One row per customer_unique_id: their MOST RECENT order.
    Columns: customer_unique_id, order_id, purchase_ts.
    Ties on purchase_ts are broken by order_id, larger first (so the answer is repeatable).

    Key is customer_unique_id, NOT customer_id: Olist makes a new customer_id for every order,
    so customer_id would treat one person as many people.
    """
    w = Window.partitionBy("customer_unique_id").orderBy(F.col("purchase_ts").desc(), F.col("order_id").desc())
    return (
        sales
        .withColumn("row_num", F.row_number().over(w))
        .filter(F.col("row_num") == 1)
        .select("customer_unique_id", "order_id", "purchase_ts")
    )


def top3_products_per_category(sales):
    """The 3 best-selling products (by revenue) inside each category.
    Columns: category, product_id, revenue, rank (1, 2, 3).
    groupBy first (one row per product), window second (rank inside the category).
    Ties on revenue are broken by product_id A to Z. row_number gives exactly 3 rows at most.
    """
    product_revenue = (
        sales.groupBy("category", "product_id").agg(F.round(F.sum("price"), 2).alias("revenue"))
    )
    w = Window.partitionBy("category").orderBy(F.col("revenue").desc(), F.col("product_id").asc())
    return (
        product_revenue
        .withColumn("rank", F.row_number().over(w))
        .filter(F.col("rank") <= 3)
        .select("category", "product_id", "revenue", "rank")
    )


def seller_monthly(sales):
    """Monthly scorecard per seller.
    Columns: seller_id, year_month, month_revenue, prev_month_revenue, mom_growth_pct, running_revenue.
    month_revenue = round(sum(price), 2); growth rounded to 1 decimal; running total over an
    explicit frame (unbounded preceding .. current row). First month of a seller has NULL
    prev_month_revenue and NULL growth, on purpose (there is no previous month to compare with).
    """
    if "year_month" not in sales.columns:
        sales = sales.withColumn("year_month", F.date_format(F.col("purchase_ts"), "yyyy-MM"))

    monthly = sales.groupBy("seller_id", "year_month").agg(F.round(F.sum("price"), 2).alias("month_revenue"))

    w = Window.partitionBy("seller_id").orderBy("year_month")
    running = w.rowsBetween(Window.unboundedPreceding, Window.currentRow)

    return (
        monthly
        .withColumn("prev_month_revenue", F.lag("month_revenue", 1).over(w))
        .withColumn(
            "mom_growth_pct",
            F.when(
                F.col("prev_month_revenue").isNotNull() & (F.col("prev_month_revenue") != 0),
                F.round((F.col("month_revenue") - F.col("prev_month_revenue")) / F.col("prev_month_revenue") * 100, 1),
            ),
        )
        .withColumn("running_revenue", F.round(F.sum("month_revenue").over(running), 2))
    )


# ============================================================================ PART 4
def read_month(spark, silver_path, year_month):
    """Read ONLY one month from the silver folder. No action here (lazy).
    Filter directly on the partition column with a plain comparison, so Spark can prune folders
    (plan shows: PartitionFilters: [isnotnull(year_month), (year_month = 2018-03)]).
    """
    return spark.read.parquet(uri(silver_path)).filter(F.col("year_month") == year_month)


# ============================================================================ PART 5
def add_price_band_builtin(df):
    """price_band: 'budget' if price < 20, 'mid' if price < 100, else 'premium'. Built-ins only."""
    return df.withColumn(
        "price_band",
        F.when(F.col("price") < 20, "budget").when(F.col("price") < 100, "mid").otherwise("premium"),
    )


def add_price_band_udf(df):
    """Same result as above, written as a Python UDF (on purpose: to measure the cost)."""

    def get_price_band(price):
        if price is None:  # a UDF must handle nulls itself; built-ins do it for free
            return None
        if price < 20:
            return "budget"
        if price < 100:
            return "mid"
        return "premium"

    return df.withColumn("price_band", F.udf(get_price_band, StringType())(F.col("price")))


# ============================================================================ PART 6
def write_gold(tables, gold_path):
    """`tables` is a dict {name: DataFrame}. Each goes to gold_path/<name>/ as exactly ONE parquet
    file, no partition folders. These tables are small and are read whole by analysts.
    """
    for name, df in tables.items():
        target = Path(gold_path) / name
        fresh_dir(target)
        df.coalesce(1).write.mode("overwrite").parquet(uri(target))


# ============================================================================ driver (given)
def main():
    spark = get_spark()

    sales = build_sales(spark)
    print(f"[1] sales rows: {sales.count():,}")

    silver = OUT_DIR / "silver" / "sales"
    write_silver(sales, silver)
    print(f"[2] silver: {count_files(silver)} parquet files, {folder_size_mb(silver):.1f} MB")
    sizes = compare_csv_parquet(sales, OUT_DIR / "compare")
    print(f"    CSV {sizes['csv_mb']:.1f} MB vs Parquet {sizes['parquet_mb']:.1f} MB")

    silver_df = spark.read.parquet(uri(silver))
    tables = {
        "latest_order": latest_order_per_customer(silver_df),
        "top3_products": top3_products_per_category(silver_df),
        "seller_monthly": seller_monthly(silver_df),
    }
    for name, df in tables.items():
        print(f"[3] {name}: {df.count():,} rows")

    march = read_month(spark, silver, "2018-03")
    print(f"[4] 2018-03 rows: {march.count():,}")

    _, t_builtin = timed(lambda: add_price_band_builtin(silver_df).groupBy("price_band").count().collect())
    _, t_udf = timed(lambda: add_price_band_udf(silver_df).groupBy("price_band").count().collect())
    print(f"[5] built-in {t_builtin:.2f}s | UDF {t_udf:.2f}s")

    gold = OUT_DIR / "gold"
    fresh_dir(gold)
    write_gold(tables, gold)
    print(f"[6] gold written: {count_files(gold)} parquet files")
    spark.stop()


if __name__ == "__main__":
    main()
