import pandas as pd
from pathlib import Path
raw_dir = Path("data/raw")
processed_dir = Path("data/processed")
processed_dir.mkdir(parents=True, exist_ok=True)
orders = pd.read_csv(raw_dir / "olist_orders_dataset.csv")
customers = pd.read_csv(raw_dir / "olist_customers_dataset.csv")
order_items = pd.read_csv(raw_dir / "olist_order_items_dataset.csv")
products = pd.read_csv(raw_dir / "olist_products_dataset.csv")
reviews = pd.read_csv(raw_dir / "olist_order_reviews_dataset.csv")
order_date_columns = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date"
]
for column in order_date_columns:
    orders[column] = pd.to_datetime(orders[column], errors="coerce")
order_items["shipping_limit_date"] = pd.to_datetime(
    order_items["shipping_limit_date"],
    errors="coerce"
)
reviews["review_creation_date"] = pd.to_datetime(
    reviews["review_creation_date"],
    errors="coerce"
)
reviews["review_answer_timestamp"] = pd.to_datetime(
    reviews["review_answer_timestamp"],
    errors="coerce"
)
orders.to_csv(processed_dir / "olist_orders_dataset.csv", index=False)
customers.to_csv(processed_dir / "olist_customers_dataset.csv", index=False)
order_items.to_csv(processed_dir / "olist_order_items_dataset.csv", index=False)
products.to_csv(processed_dir / "olist_products_dataset.csv", index=False)
reviews.to_csv(processed_dir / "olist_order_reviews_dataset.csv", index=False)
print("Processing completed.")
print("Orders:", processed_dir / "olist_orders_dataset.csv", orders.shape)
print("Customers:", processed_dir / "olist_customers_dataset.csv", customers.shape)
print("Order items:", processed_dir / "olist_order_items_dataset.csv", order_items.shape)
print("Products:", processed_dir / "olist_products_dataset.csv", products.shape)
print("Reviews:", processed_dir / "olist_order_reviews_dataset.csv", reviews.shape)