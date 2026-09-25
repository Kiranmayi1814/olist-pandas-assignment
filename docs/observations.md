# Data Observations

## File: olist_orders_dataset.csv

* Size: 99,441 rows and 8 columns.
* Important columns: order_id, customer_id, order_status, and date columns.
* Data types: Date columns were initially stored as object/text.
* Missing values: order_approved_at has 160 missing values.
* Missing values: order_delivered_carrier_date has 1,783 missing values.
* Missing values: order_delivered_customer_date has 2,965 missing values.
* Evidence: Missing values were checked using `orders.isna().sum()`.
* Order status: There are 8 different status categories.
* Status distribution: delivered is the most common status.
* Evidence: Order status values were checked using `nunique()` and `value_counts()`.
* Duplicate check: No complete duplicate rows were found.
* Risk: Missing date values may affect analysis that uses these dates.
* Decision: Keep missing values and all order statuses.
* Processing: Convert order date columns to datetime.

## File: olist_customers_dataset.csv

* Size: 99,441 rows and 5 columns.
* Important columns: customer_id, customer_unique_id, city, state, and ZIP prefix.
* customer_id has 99,441 unique values.
* customer_unique_id has 96,096 unique values.
* Location: There are 27 unique states.
* Location: There are 946 unique ZIP-code prefixes.
* State distribution: SP is the most common state with 41,746 records.
* Evidence: Unique values were checked using `nunique()` and `value_counts()`.
* Missing values: No missing values were found.
* Duplicate check: No complete duplicate rows were found.
* Risk: Repeated customer_unique_id values are not automatically duplicates.
* Decision: Keep both customer ID columns.
* Decision: Keep customer location values unchanged.
* Processing: No missing-value or duplicate removal is required.

## File: olist_order_items_dataset.csv

* Size: 112,650 rows and 7 columns.
* Important columns: order_id, order_item_id, product_id, seller_id, price, freight_value, and shipping_limit_date.
* There are 98,666 unique orders.
* There are 32,951 unique products.
* There are 3,095 unique sellers.
* order_item_id has values from 1 to 21.
* Evidence: Unique IDs and item values were checked using `nunique()` and `value_counts()`.
* This data contains multiple items for some orders.
* Missing values: No missing values were found.
* Duplicate check: No complete duplicate rows were found.
* Price: Values range from 0.85 to 6,735.00.
* Freight: Values range from 0.00 to 409.68.
* There are 383 records with zero freight.
* No price values are less than or equal to zero.
* Risk: Repeated IDs are expected because orders can contain multiple items.
* Decision: Keep all order-item records and values.
* Decision: Keep zero freight values.
* Processing: Convert shipping_limit_date to datetime.

## File: olist_products_dataset.csv

* Size: 32,951 rows and 9 columns.
* Important columns: product_id, product_category_name, and product measurement fields.
* product_id has 32,951 unique values.
* Missing values: product_category_name has 610 missing values.
* Missing values: product_name_lenght has 610 missing values.
* Missing values: product_description_lenght has 610 missing values.
* Missing values: product_photos_qty has 610 missing values.
* Missing values: Weight and dimension fields have 2 missing values each.
* Evidence: Missing values were checked using `products.isna().sum()`.
* Categories: There are 73 unique product categories.
* Category distribution: cama_mesa_banho has 3,029 records.
* Product weight ranges from 0 to 40,425 g.
* Duplicate check: No complete duplicate rows were found.
* Risk: Missing and unusual product values may affect analysis.
* Decision: Keep missing values and existing categories.
* Decision: Do not remove unusual weight values automatically.
* Processing: No product values are changed without a documented reason.

## File: olist_order_reviews_dataset.csv

* Size: 99,224 rows and 7 columns.
* Important columns: review_id, order_id, review_score, review comments, and review dates.
* There are 98,410 unique review IDs.
* There are 98,673 unique order IDs.
* Review scores range from 1 to 5.
* Score 5 is the most common with 57,328 records.
* Score 4 has 19,142 records.
* Score 1 has 11,424 records.
* Evidence: Review scores were checked using `value_counts()` and `describe()`.
* Missing values: review_comment_title has 87,656 missing values.
* Missing values: review_comment_message has 58,247 missing values.
* Duplicate check: No complete duplicate rows were found.
* Risk: Missing comments can affect text analysis.
* Decision: Keep missing review titles and messages.
* Decision: Keep all review scores and review records.
* Processing: Convert review_creation_date to datetime.
* Processing: Convert review_answer_timestamp to datetime.

## Overall Decision

* Keep all raw CSV files unchanged.
* Process a separate copy of the raw data.
* Do not remove rows only because they contain missing values.
* Do not remove repeated IDs without clear evidence.
* Keep unusual values unless there is evidence that they are invalid.
* Apply only the documented date conversions during processing.
* Validate the processed files against the raw files.
