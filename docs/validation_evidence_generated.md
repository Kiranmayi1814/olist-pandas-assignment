# Validation Evidence

Checks: 49 | Passed: 49 | Failed: 0

| Stage | Check | Result | Evidence |
|---|---|---|---|
| RAW | raw.customers rows match file | PASS | file=99441 db=99441 |
| RAW | raw.orders rows match file | PASS | file=99441 db=99441 |
| RAW | raw.order_items rows match file | PASS | file=112650 db=112650 |
| RAW | raw.products rows match file | PASS | file=32951 db=32951 |
| RAW | raw.reviews rows match file | PASS | file=99224 db=99224 |
| RAW | missing category kept as NULL | PASS | NULL categories=610 |
| RAW | all order statuses kept | PASS | statuses=8 |
| CLEAN | customers: key has no NULL and no duplicate | PASS | nulls=0 dups=0 |
| CLEAN | products: key has no NULL and no duplicate | PASS | nulls=0 dups=0 |
| CLEAN | orders: key has no NULL and no duplicate | PASS | nulls=0 dups=0 |
| CLEAN | order_items: key has no NULL and no duplicate | PASS | nulls=0 dups=0 |
| CLEAN | reviews: key has no NULL and no duplicate | PASS | nulls=0 dups=0 |
| CLEAN | no orphans: orders -> customers | PASS | orphans=0 |
| CLEAN | no orphans: order_items -> orders | PASS | orphans=0 |
| CLEAN | no orphans: order_items -> products | PASS | orphans=0 |
| CLEAN | no orphans: reviews -> orders | PASS | orphans=0 |
| CLEAN | customers: rows = processed file | PASS | clean=99441 file=99441 |
| CLEAN | customers: rows = raw table | PASS | clean=99441 raw=99441 |
| CLEAN | orders: rows = processed file | PASS | clean=99441 file=99441 |
| CLEAN | orders: rows = raw table | PASS | clean=99441 raw=99441 |
| CLEAN | order_items: rows = processed file | PASS | clean=112650 file=112650 |
| CLEAN | order_items: rows = raw table | PASS | clean=112650 raw=112650 |
| CLEAN | products: rows = processed file | PASS | clean=32951 file=32951 |
| CLEAN | products: rows = raw table | PASS | clean=32951 raw=32951 |
| CLEAN | reviews: rows = processed file | PASS | clean=99224 file=99224 |
| CLEAN | reviews: rows = raw table | PASS | clean=99224 raw=99224 |
| CLEAN | order dates are timestamps | PASS | found=5/5 wrong_type=[] |
| CLEAN | SUM(price) = processed file | PASS | db=13,591,643.70 file=13,591,643.70 |
| FIN-STG1 | rows = clean.order_items | PASS | rows=112650 |
| FIN-STG1 | no NULL price | PASS |  |
| FIN-STG1 | SUM(price) same as clean | PASS |  |
| FIN-STG2 | rows = eligible items from clean | PASS | expected=112101 actual=112101 removed=549 |
| FIN-STG2 | no NULL month / category | PASS |  |
| FIN-CUR | total sales = CLEAN | PASS | clean=13494400.74 curated=13494400.74 |
| FIN-CUR | items_sold = eligible items | PASS |  |
| FIN-CUR | rows = distinct month + category | PASS | rows=1282 |
| FIN-CUR | every row matches CLEAN recalculation | PASS | different rows=0 |
| OPS-STG1 | rows = clean.orders | PASS |  |
| OPS-STG1 | no NULL state / status / purchase date / estimate | PASS |  |
| OPS-STG2 | rows = staging 1 | PASS |  |
| OPS-STG2 | every order has a class | PASS |  |
| OPS-STG2 | late > 0 days, on_time <= 0 days | PASS |  |
| OPS-STG2 | canceled orders are never late | PASS |  |
| OPS-CUR | total orders = clean.orders | PASS |  |
| OPS-CUR | delivered = CLEAN | PASS | delivered=96470 |
| OPS-CUR | late = CLEAN | PASS | late=6534 |
| OPS-CUR | late <= delivered <= total on every row | PASS |  |
| OPS-CUR | rate between 0 and 1 (or NULL) | PASS |  |
| DIM | every purchase date exists in dim_date | PASS | missing=0 |