# Business Requirements Document

## Problem 1: Finance – Sales by Category

**Business need:**
The Finance team wants reliable sales figures to understand how product sales change over time.

**User:**
Finance Team

**Main question:**
How does the value of products sold change by category each month?

**Measures:**

* **Sales Value:** Sum of `order_items.price`.
* **Orders:** Count of unique orders.
* **Items Sold:** Number of order item records.
* Freight charges are not included in sales value.

**Time period:**
Sales are grouped by month using `order_purchase_timestamp`.

**Data included:**
Order items linked to orders that are not `canceled` or `unavailable`.

**Data excluded:**
Items from `canceled` and `unavailable` orders.

**Missing values:**
Products without a category are kept and shown as **Unknown** in the staging data.

**Final level of detail:**
One record represents one **product category for one purchase month**.

**Key assumptions:**

* Each order item row represents one item line.
* Product price is treated as the sales value.
* Freight is treated as a delivery charge, not product sales.
* Category names remain in their original language.

---

## Problem 2: Operations – Delivery Performance

**Business need:**
The Operations team wants to monitor delivery performance and identify areas with late deliveries.

**User:**
Operations Team

**Main question:**
How does delivery performance change over time, and which customer states have more late deliveries?

**Measures:**

* **Total Orders:** All orders in the period.
* **Delivered Orders:** Orders with a valid delivery result.
* **Late Orders:** Orders delivered after the estimated date.
* **Late Delivery Rate:** Late orders divided by delivered orders.

**Time period:**
Orders are grouped by month using `order_purchase_timestamp`.

**Delivery rule:**
An order is **Late** when `order_delivered_customer_date` is later than `order_estimated_delivery_date`.
If both dates are the same, the order is **On-time**.

**Data included:**
All orders are included for the total order count. Only orders with a reliable delivery outcome are used for delivered and late calculations.

**Data excluded from late calculation:**
Canceled, unavailable, in-progress, and orders without a valid delivery date are not counted as late.

**Missing values:**
A delivered order with no delivery date is treated as **Unknown**, not Late.

**Location:**
Customer state (`customer_state`).

**Final level of detail:**
One record represents one **customer state for one purchase month**.

**Key assumptions:**

* The estimated date represents the expected delivery date.
* Customer state represents the delivery destination.
* Purchase month is used to track the order cohort.
* Late delivery rate is calculated only from orders with a known delivery outcome.
