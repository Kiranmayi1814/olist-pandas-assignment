# Data Model Document

## Schema Responsibilities

* **`raw`**: Stores the original CSV data without cleaning or changes.
* **`clean`**: Stores trusted business tables with proper data types and keys.
* **`staging`**: Stores intermediate tables used for business transformations.
* **`curated`**: Stores final tables prepared for business reporting.

## Data Flow

`data/raw/*.csv` → `raw.*` → source evidence

`data/processed/*.csv` → `clean.*` → trusted data

`clean.*` → `staging.*` → `curated.*`

## CLEAN Layer

### `clean.customers`

* **Purpose:** Stores customer and location details.
* **Grain:** One row = one customer record.
* **Primary Key:** `customer_id`

### `clean.orders`

* **Purpose:** Stores order status and order dates.
* **Grain:** One row = one order.
* **Primary Key:** `order_id`
* **Foreign Key:** `customer_id` → `clean.customers.customer_id`

### `clean.products`

* **Purpose:** Stores product and category information.
* **Grain:** One row = one product.
* **Primary Key:** `product_id`

### `clean.order_items`

* **Purpose:** Stores items sold in each order.
* **Grain:** One row = one order item.
* **Primary Key:** (`order_id`, `order_item_id`)
* **Foreign Keys:** `order_id` → `clean.orders`, `product_id` → `clean.products`

### `clean.reviews`

* **Purpose:** Stores customer reviews for orders.
* **Grain:** One row = one review for an order.
* **Primary Key:** (`review_id`, `order_id`)
* **Foreign Key:** `order_id` → `clean.orders`

## STAGING Layer

### `staging.finance_items_enriched`

* Combines order item, order, and product information.
* Keeps one row for each order item.

### `staging.finance_items_reportable`

* Applies Finance rules.
* Excludes canceled and unavailable orders.
* Creates reporting month and sales value.

### `staging.ops_orders_base`

* Combines order delivery details with customer location.
* Keeps one row for each order.

### `staging.ops_orders_classified`

* Classifies orders as late, on-time, not delivered, not fulfilled, or unknown.
* Creates reporting month and delivery comparison.

## CURATED Layer

### `curated.finance_monthly_category_sales`

* **Grain:** One category for one purchase month.
* Contains sales value, items sold, and distinct orders.
* Sales value uses `order_items.price`; freight is excluded.

### `curated.operations_monthly_state_delivery`

* **Grain:** One customer state for one purchase month.
* Contains total orders, delivered orders, late orders, and late delivery rate.

## Constraints

* Primary keys prevent duplicate business records.
* Foreign keys maintain relationships between tables.
* Missing values are kept when they represent valid source information.
