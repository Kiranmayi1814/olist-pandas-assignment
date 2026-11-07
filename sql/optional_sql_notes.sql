-- sql/optional_sql_notes.sql
-- Reference copy of the SQL used in notebooks/assignment_3_warehouse.ipynb
-- (the notebook is the source of truth; run it top to bottom).
-- Prerequisite: CREATE DATABASE olist_warehouse;

-- Create the four layers (schemas) inside ONE database
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS clean;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS curated;

-- CLEAN table contracts (types, keys, constraints)
DROP TABLE IF EXISTS clean.reviews CASCADE;
DROP TABLE IF EXISTS clean.order_items CASCADE;
DROP TABLE IF EXISTS clean.orders CASCADE;
DROP TABLE IF EXISTS clean.products CASCADE;
DROP TABLE IF EXISTS clean.customers CASCADE;

CREATE TABLE clean.customers (
    customer_id              TEXT PRIMARY KEY,
    customer_unique_id       TEXT NOT NULL,
    customer_zip_code_prefix INTEGER,
    customer_city            TEXT,
    customer_state           CHAR(2) NOT NULL
);

CREATE TABLE clean.products (
    product_id                 TEXT PRIMARY KEY,
    product_category_name      TEXT,
    product_name_lenght        INTEGER,
    product_description_lenght INTEGER,
    product_photos_qty         INTEGER,
    product_weight_g           INTEGER,
    product_length_cm          INTEGER,
    product_height_cm          INTEGER,
    product_width_cm           INTEGER
);

CREATE TABLE clean.orders (
    order_id                      TEXT PRIMARY KEY,
    customer_id                   TEXT NOT NULL REFERENCES clean.customers (customer_id),
    order_status                  TEXT NOT NULL,
    order_purchase_timestamp      TIMESTAMP NOT NULL,
    order_approved_at             TIMESTAMP,
    order_delivered_carrier_date  TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP NOT NULL
);

CREATE TABLE clean.order_items (
    order_id            TEXT NOT NULL REFERENCES clean.orders (order_id),
    order_item_id       INTEGER NOT NULL CHECK (order_item_id >= 1),
    product_id          TEXT NOT NULL REFERENCES clean.products (product_id),
    seller_id           TEXT NOT NULL,
    shipping_limit_date TIMESTAMP,
    price               NUMERIC(10,2) NOT NULL CHECK (price > 0),
    freight_value       NUMERIC(10,2) NOT NULL CHECK (freight_value >= 0),
    PRIMARY KEY (order_id, order_item_id)
);

CREATE TABLE clean.reviews (
    review_id               TEXT NOT NULL,
    order_id                TEXT NOT NULL REFERENCES clean.orders (order_id),
    review_score            SMALLINT NOT NULL CHECK (review_score BETWEEN 1 AND 5),
    review_comment_title    TEXT,
    review_comment_message  TEXT,
    review_creation_date    TIMESTAMP,
    review_answer_timestamp TIMESTAMP,
    PRIMARY KEY (review_id, order_id)
);

-- STAGING 1 (Finance): one row per order item, enriched with order + product info
DROP TABLE IF EXISTS staging.finance_items_enriched;

CREATE TABLE staging.finance_items_enriched AS
SELECT
    oi.order_id,
    oi.order_item_id,
    oi.product_id,
    o.order_status,
    o.order_purchase_timestamp,
    oi.price,
    oi.freight_value,
    p.product_category_name
FROM clean.order_items oi
JOIN clean.orders      o ON o.order_id   = oi.order_id
LEFT JOIN clean.products p ON p.product_id = oi.product_id;

ALTER TABLE staging.finance_items_enriched ADD PRIMARY KEY (order_id, order_item_id);

-- STAGING 2 (Finance): apply business rules, derive reporting month and category
DROP TABLE IF EXISTS staging.finance_items_reportable;

CREATE TABLE staging.finance_items_reportable AS
SELECT
    order_id,
    order_item_id,
    order_status,
    CAST(date_trunc('month', order_purchase_timestamp) AS date)        AS reporting_month,
    COALESCE(NULLIF(TRIM(product_category_name), ''), 'unknown')         AS product_category,
    price                                                                AS item_sales_value
FROM staging.finance_items_enriched
WHERE order_status NOT IN ('canceled', 'unavailable');

ALTER TABLE staging.finance_items_reportable ADD PRIMARY KEY (order_id, order_item_id);

-- CURATED (Finance): one row per category per purchase month
DROP TABLE IF EXISTS curated.finance_monthly_category_sales;

CREATE TABLE curated.finance_monthly_category_sales (
    reporting_month   DATE          NOT NULL,
    product_category  TEXT          NOT NULL,
    item_sales_value  NUMERIC(14,2) NOT NULL,
    items_sold        INTEGER       NOT NULL,
    distinct_orders   INTEGER       NOT NULL,
    PRIMARY KEY (reporting_month, product_category)
);

INSERT INTO curated.finance_monthly_category_sales
SELECT
    reporting_month,
    product_category,
    SUM(item_sales_value),
    COUNT(*),
    COUNT(DISTINCT order_id)
FROM staging.finance_items_reportable
GROUP BY reporting_month, product_category;

COMMENT ON TABLE curated.finance_monthly_category_sales IS
  'Finance product. Grain: one product category per purchase month. item_sales_value = SUM(price), freight excluded, canceled/unavailable orders excluded, missing category = unknown. distinct_orders must not be summed across categories.';

-- STAGING 1 (Operations): one row per order with delivery evidence + customer location
DROP TABLE IF EXISTS staging.ops_orders_base;

CREATE TABLE staging.ops_orders_base AS
SELECT
    o.order_id,
    o.customer_id,
    c.customer_state,
    c.customer_city,
    o.order_status,
    o.order_purchase_timestamp,
    o.order_estimated_delivery_date,
    o.order_delivered_customer_date
FROM clean.orders o
JOIN clean.customers c ON c.customer_id = o.customer_id;

ALTER TABLE staging.ops_orders_base ADD PRIMARY KEY (order_id);

-- STAGING 2 (Operations): classify each order's delivery outcome
DROP TABLE IF EXISTS staging.ops_orders_classified;

CREATE TABLE staging.ops_orders_classified AS
SELECT
    b.order_id,
    b.customer_state,
    b.customer_city,
    b.order_status,
    CAST(date_trunc('month', b.order_purchase_timestamp) AS date) AS reporting_month,
    b.order_estimated_delivery_date,
    b.order_delivered_customer_date,
    CASE
        WHEN b.order_delivered_customer_date IS NOT NULL
         AND b.order_status = 'delivered'
        THEN CAST(b.order_delivered_customer_date AS date) - CAST(b.order_estimated_delivery_date AS date)
    END AS days_vs_estimate,
    CASE
        WHEN b.order_status IN ('canceled', 'unavailable')                                   THEN 'not_fulfilled'
        WHEN b.order_status = 'delivered' AND b.order_delivered_customer_date IS NULL         THEN 'unknown'
        WHEN b.order_status = 'delivered'
         AND CAST(b.order_delivered_customer_date AS date) > CAST(b.order_estimated_delivery_date AS date) THEN 'late'
        WHEN b.order_status = 'delivered'                                                    THEN 'on_time'
        ELSE 'not_delivered'
    END AS delivery_classification
FROM staging.ops_orders_base b;

ALTER TABLE staging.ops_orders_classified ADD PRIMARY KEY (order_id);

-- CURATED (Operations): one row per customer state per purchase month
DROP TABLE IF EXISTS curated.operations_monthly_state_delivery;

CREATE TABLE curated.operations_monthly_state_delivery (
    reporting_month     DATE         NOT NULL,
    customer_state      CHAR(2)      NOT NULL,
    total_orders        INTEGER      NOT NULL,
    delivered_orders    INTEGER      NOT NULL,
    late_orders         INTEGER      NOT NULL,
    late_delivery_rate  NUMERIC(6,4),
    PRIMARY KEY (reporting_month, customer_state)
);

INSERT INTO curated.operations_monthly_state_delivery
WITH counts AS (
    SELECT
        reporting_month,
        customer_state,
        COUNT(*)                                                                   AS total_orders,
        COUNT(*) FILTER (WHERE delivery_classification IN ('late', 'on_time'))     AS delivered_orders,
        COUNT(*) FILTER (WHERE delivery_classification = 'late')                   AS late_orders
    FROM staging.ops_orders_classified
    GROUP BY reporting_month, customer_state
)
SELECT
    reporting_month, customer_state, total_orders, delivered_orders, late_orders,
    ROUND(CAST(late_orders AS numeric) / NULLIF(delivered_orders, 0), 4)
FROM counts;

COMMENT ON TABLE curated.operations_monthly_state_delivery IS
  'Operations product. Grain: one customer state per purchase month. delivered = status delivered with a delivery date, late = delivery date > estimated date (date compare, same day = on time), late_delivery_rate = late_orders / delivered_orders.';
