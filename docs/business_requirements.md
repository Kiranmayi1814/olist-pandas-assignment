# Business Requirements

## Problem 1 - Finance

| Field | Answer |
|---|---|
| Business problem | Finance gets different sales numbers from different people |
| Business user | Finance team |
| Business question | How is item sales value changing across product categories over time? |
| Metric | Item sales value = `SUM(order_items.price)` |
| Other metric | Distinct orders = `COUNT(DISTINCT order_id)` per month + category |
| Extra metric (justified) | Items sold = `COUNT(*)` of order items (one order can have many items) |
| Time definition | Month of `order_purchase_timestamp` |
| Included records | Items of orders that are not `canceled` or `unavailable` |
| Excluded records | Items of `canceled` and `unavailable` orders (549 items) |
| Missing-value treatment | Missing category is kept and shown as `unknown` |
| Expected final grain | One row = one product category in one purchase month |
| Assumptions | One order item row = one item sold |
| | `price` = sales value |
| | Freight is a delivery charge, so it is NOT included |
| | Category names stay in the original language |
| | Distinct orders must NOT be added across categories (one order can be in many categories) |

### Finance thinking questions
1. **Grain of curated table?** One category for one month.
2. **What is sales_value?** Sum of item `price`. No freight.
3. **Which timestamp gives the month?** `order_purchase_timestamp`.
4. **Which records are excluded?** `canceled` and `unavailable` orders.
5. **Can one order give many rows in staging 1?** Yes. One order has many items.
6. **How to avoid counting an order many times?** Use `COUNT(DISTINCT order_id)`.
7. **Products with no category?** Keep them. Label = `unknown`. 1,589 items.
8. **How to prove curated total = CLEAN total?** Recalculate from CLEAN with the same rules. Compare totals and every row.

---

## Problem 2 - Operations

| Field | Answer |
|---|---|
| Business problem | Operations cannot see where deliveries are late |
| Business user | Operations team |
| Business question | How is delivery performance changing, and where are late deliveries occurring? |
| Metric - Total orders | All orders in the month + state |
| Metric - Delivered orders | Status `delivered` AND delivery date is not empty |
| Metric - Late orders | Delivery date is after estimated date |
| Metric - Late delivery rate | Late orders / delivered orders |
| Time definition | Month of `order_purchase_timestamp` |
| Location | `customer_state` |
| Included records | All orders (for total orders) |
| Excluded records | Orders without a delivery result are not used in delivered or late |
| Missing-value treatment | No delivery date = not delivered (never late, never on time) |
| | Delivered but date empty = `unknown` |
| | Rate is empty (NULL) when delivered orders = 0 |
| Expected final grain | One row = one customer state in one purchase month |
| Assumptions | One order = one row (not one item) |
| | Dates are compared as dates, not times |

### Delivery rules
| Case | Class |
|---|---|
| Status `canceled` or `unavailable` | `not_fulfilled` |
| Status `delivered`, delivery date empty | `unknown` |
| Delivered date > estimated date | `late` |
| Delivered date <= estimated date | `on_time` |
| Any other status (shipped, processing...) | `not_delivered` |

### Boundary rules
- Same day (actual = estimated) -> `on_time`
- Before estimated date -> `on_time`
- After estimated date -> `late`
- Delivery date empty -> never `late`
- Canceled orders are never `late`

### Why these choices
- The metric is about orders, so grain = order.
- Orders are not counted twice, because order items are not used.
- Late rate uses delivered orders only, so unfinished orders do not hide late ones.
