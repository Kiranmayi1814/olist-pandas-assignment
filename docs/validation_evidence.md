# Validation Evidence

Source: `notebooks/assignment_3_warehouse.ipynb` (section 07). Run the notebook again to refresh.

**Result: 49 validation checks are defined in the notebook. The documented run shows 49 passed and 0 failed.**

## What was checked at every stage
| Check | Meaning |
|---|---|
| Row count | Same as the source or the previous stage |
| Grain | Declared key is unique |
| Nulls | Key and measure columns are not empty |
| Relationships | No orphan rows (FK finds a parent) |
| Sample rows | A few rows looked at by hand |
| Totals | Totals agree with the previous stage |

## RAW
| Table | File rows | DB rows | Result |
|---|---|---|---|
| customers | 99,441 | 99,441 | PASS |
| orders | 99,441 | 99,441 | PASS |
| order_items | 112,650 | 112,650 | PASS |
| products | 32,951 | 32,951 | PASS |
| reviews | 99,224 | 99,224 | PASS |

- Missing categories kept as NULL (610), not changed to `unknown`: PASS
- All 8 order statuses kept: PASS

## CLEAN
- Primary keys not NULL and unique (all 5 tables): PASS
- Foreign keys, orphans = 0 (4 relationships): PASS
- Dates are timestamps, money is numeric: PASS
- Row counts equal processed files and RAW: PASS
- `SUM(price)` = 13,591,643.70 (file = DB): PASS

## Finance
| Stage | Expected | Actual | Result |
|---|---|---|---|
| staging 1 rows | 112,650 | 112,650 | PASS |
| staging 2 rows | 112,101 | 112,101 | PASS |
| `unknown` category items | - | 1,589 | none lost |
| curated rows | 1,282 | 1,282 | PASS |
| curated total sales | 13,494,400.74 | 13,494,400.74 | PASS |
| every month + category row vs CLEAN | 0 different | 0 different | PASS |

- Distinct orders must not be added across categories: PASS (checked for 24 months)

## Operations
| Stage | Expected | Actual | Result |
|---|---|---|---|
| staging 1 rows | 99,441 | 99,441 | PASS |
| staging 2 rows | 99,441 | 99,441 | PASS |
| curated total orders | 99,441 | 99,441 | PASS |
| delivered orders | 96,470 | 96,470 | PASS |
| late orders | 6,534 | 6,534 | PASS |
| curated rows | 565 | 565 | PASS |
| every month + state row vs CLEAN | 0 different | 0 different | PASS |

- Late rule: same day = on time: PASS
- Canceled/unavailable never late: PASS
- late <= delivered <= total on every row: PASS
- Rate between 0 and 1 (or NULL): PASS

## Table sizes
| Layer | Table | Rows |
|---|---|---|
| raw | customers / orders / order_items / products / reviews | 99,441 / 99,441 / 112,650 / 32,951 / 99,224 |
| clean | customers / orders / order_items / products / reviews | 99,441 / 99,441 / 112,650 / 32,951 / 99,224 |
| staging | finance_items_enriched | 112,650 |
| staging | finance_items_reportable | 112,101 |
| staging | ops_orders_base | 99,441 |
| staging | ops_orders_classified | 99,441 |
| curated | finance_monthly_category_sales | 1,282 |
| curated | operations_monthly_state_delivery | 565 |
