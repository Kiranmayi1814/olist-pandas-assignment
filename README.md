# DataKern Pandas Data Exploration & Processing

**Name:** SANGOJU PAVANI DURGA KIRANMAYI

## Project Overview

This project explores and processes the Olist Brazilian E-Commerce Public Dataset using Python and Pandas.

The project is completed in three parts: exploration, processing, and validation.

Raw data is kept unchanged and processed data is stored separately.

## Dataset

The project uses five required Olist CSV files:

* orders
* customers
* order_items
* products
* order_reviews

Raw files are stored in `data/raw/`.

Processed files are stored in `data/processed/`.

## Project Structure

```text
olist-pandas-assignment/

├── data/raw/
├── data/processed/
├── src/process_olist_data.py
├── notebooks/01_data_exploration.ipynb
├── notebooks/02_validate_processed_data.ipynb
├── docs/observations.md
├── README.md
├── requirements.txt
└── .gitignore
```

## Part B - Data Processing

Script: `src/process_olist_data.py`

Run from the project root:

```text
python src/process_olist_data.py
```

The script reads data from `data/raw/` and saves processed CSV files to `data/processed/`.

The raw files are not overwritten.

## Part C - Data Validation

Notebook: `notebooks/02_validate_processed_data.ipynb`

The notebook compares raw and processed data.

It checks row counts, column counts, data types, missing values, and duplicates.

It also verifies expected columns and confirms that raw files remain unchanged.

## Setup

Create and activate a virtual environment:

```text
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```text
python -m pip install -r requirements.txt
```

Start JupyterLab:

```text
jupyter lab
```

## Dataset Row Counts

Orders: 99,441

Customers: 99,441

Order Items: 112,650

Order Reviews: 99,224

Products: 32,951

## Raw Data Safety

Files in `data/raw/` are treated as original source data.

Processing creates separate files in `data/processed/`.

The raw dataset is not modified or overwritten.

## Git

```text
git status
git add .
git commit -m "Complete Pandas assignment"
git push
```

## Requirements

The project dependencies are listed in `requirements.txt`.

The `.gitignore` excludes `.venv/`, `__pycache__/`, and `.ipynb_checkpoints/`.

## Outcome

The project demonstrates Pandas-based data exploration, documented processing decisions, data processing, and validation.

# Assignment 3 - Warehouse: RAW -> CLEAN -> STAGING -> CURATED

Continuation of the Pandas assignment. The validated files are loaded into PostgreSQL (`olist_warehouse`) and turned into two business data products.

| Schema    | Purpose                                                                                    |
| --------- | ------------------------------------------------------------------------------------------ |
| `raw`     | Source evidence (all TEXT, nothing interpreted)                                            |
| `clean`   | Typed, keyed, reusable business entities                                                   |
| `staging` | Intermediate transformation tables (2 per business problem)                                |
| `curated` | Final data products: `finance_monthly_category_sales`, `operations_monthly_state_delivery` |

Main notebook: `notebooks/assignment_3_warehouse.ipynb`

Docs: `docs/business_requirements.md`, `docs/data_model.md`, `docs/validation_evidence.md`

SQL reference copy: `sql/optional_sql_notes.sql`

## How to run

1. Create the database once: `CREATE DATABASE olist_warehouse;`
2. Copy `.env.example` to `.env` and fill in your PostgreSQL credentials (`.env` is git-ignored).
3. `python -m pip install -r requirements.txt`
4. Open the notebook and run all cells top to bottom (safe to re-run: tables are dropped and rebuilt).

## ERD

```text
                    ┌─────────────────────┐
                    │   clean.customers   │
                    │─────────────────────│
                    │ PK customer_id      │
                    │ customer_unique_id  │
                    │ customer_state      │
                    │ customer_city       │
                    └──────────┬──────────┘
                               │
                               │ customer_id
                               ▼
                    ┌─────────────────────┐
                    │     clean.orders    │
                    │─────────────────────│
                    │ PK order_id         │
                    │ FK customer_id      │
                    │ order_status        │
                    │ order_purchase_...  │
                    └───────┬───────┬─────┘
                            │       │
                   order_id │       │ order_id
                            ▼       ▼
             ┌─────────────────┐  ┌─────────────────┐
             │ clean.order_items│  │ clean.reviews  │
             │─────────────────│  │─────────────────│
             │ PK order_id     │  │ PK review_id    │
             │ PK item_id      │  │ FK order_id     │
             │ FK product_id   │  │ review_score    │
             │ FK seller_id    │  └─────────────────┘
             └────────┬────────┘
                      │
                      │ product_id
                      ▼
             ┌─────────────────────┐
             │   clean.products    │
             │─────────────────────│
             │ PK product_id       │
             │ product_category   │
             └─────────────────────┘
```

### Main Relationships

* `orders.customer_id` → `customers.customer_id`
* `order_items.order_id` → `orders.order_id`
* `order_items.product_id` → `products.product_id`
* `reviews.order_id` → `orders.order_id`

The CLEAN layer uses these relationships to support the Finance and Operations pipelines.
