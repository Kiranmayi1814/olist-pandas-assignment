# DataKern Pandas Data Exploration & Processing

**Name:** SANGOJU PAVANI DURGA KIRANMAYI

## Project Overview
This project explores and processes the Olist Brazilian E-Commerce Public Dataset using Python and Pandas.
The project is completed in three parts: exploration, processing, and validation.
Raw data is kept unchanged and processed data is stored separately.

## Dataset
The project uses five required Olist CSV files:
- orders
- customers
- order_items
- products
- order_reviews
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
Part B - Data Processing

Script: src/process_olist_data.py
Run from the project root:

python src/process_olist_data.py

The script reads data from data/raw/ and saves processed CSV files to data/processed/.
The raw files are not overwritten.

Part C - Data Validation

Notebook: notebooks/02_validate_processed_data.ipynb
The notebook compares raw and processed data.
It checks row counts, column counts, data types, missing values, and duplicates.
It also verifies expected columns and confirms that raw files remain unchanged.

Setup

Create and activate a virtual environment:

python -m venv .venv
.venv\Scripts\activate

Install dependencies:

python -m pip install -r requirements.txt

Start JupyterLab:

jupyter lab
Dataset Row Counts
Orders: 99,441
Customers: 99,441
Order Items: 112,650
Order Reviews: 99,224
Products: 32,951
Raw Data Safety

Files in data/raw/ are treated as original source data.
Processing creates separate files in data/processed/.
The raw dataset is not modified or overwritten.

Git
git status
git add .
git commit -m "Complete Pandas assignment"
git push
Requirements

The project dependencies are listed in requirements.txt.
The .gitignore excludes .venv/, __pycache__/, and .ipynb_checkpoints/.

Outcome
The project demonstrates Pandas-based data exploration, documented processing decisions, data processing, and validation.
