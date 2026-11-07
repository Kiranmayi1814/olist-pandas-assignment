# Reflection: Assignment 5 (Spark windows and Parquet)

How to read this file: numbers marked **(data)** are exact facts about the Olist files. I checked them with an independent pandas count, and they match the assignment's ground-truth table. Numbers marked **(my run)** are my own measurements. Anything shown as `▢` depends on my machine, so I copy it from my notebook `notebooks/Olist_Assignment_5.ipynb` or from the Spark UI.

## Ground truth check

| What | Expected | What I get |
|---|---|---|
| Rows in sales | 112,650 | 112,650 (data) |
| Parquet files in silver | 24 | 24, one per `year_month=` folder |
| Rows in latest_order | 95,420 | 95,420 (data) |
| Rows in top3_products | 213 | 213 (data) |
| Rows in seller_monthly | 16,441 | 16,441 (data) |
| Rows for 2018-03 | 8,217 | 8,217 (data) |

Hand check on the raw CSV with Spark SQL: the biggest seller is `4869f7a5dfa277a7dca6462dcf3b52b2` with a total of 229,472.63. In my `seller_monthly`, its running_revenue in the last month (2018-08) is also 229,472.63. They match, so the window frame (unbounded preceding to current row) is correct. For a customer I used `8d50f5eadf50201ccdcedfb9e2ac8455` (16 orders). Their latest order is `d3582fd5ccccd9cb229a63dfb417c86f` at 2018-08-20 19:14:26, and `latest_order` returns the same one.

---

## Pause and observe

**#1. Explicit schema and missing categories.** `inferSchema` has to read the whole file once just to guess the types, so it starts a Spark job before I have asked for any rows (I saw ▢ job(s) in the Jobs tab). A Monday pipeline should use an explicit schema: it is faster, and the types cannot change if the file changes a little. There are 32,951 products, 610 have no category, and 13 more have a category that is missing from the translation table (`pc_gamer` and `portateis_cozinha_e_preparadores_de_alimentos`), so 623 have no English name (data). An inner join would throw all of those products away.

**#2. Which join loses rows.** The sales table must have 112,650 rows, the same as the items file. The products join does not lose anything: left join and inner join both give 112,650, because every item has a product. The translation join does lose rows: an inner join gives 111,023, so 1,627 items vanish (1,603 with no category and 24 with a category that is not translated). That is only 1.4% of the rows, so a dashboard would just show a slightly lower revenue number and nobody would see an error. That is why every join starts from items and is a left join, and missing categories become `'unknown'`.

**#3. Sizes and min/max.** As CSV, `sales` is 20.925 MB. As plain Parquet it is 9.886 MB (my run), which is less than half. The partitioned silver table is 10.94 MB (my run), about 1 MB bigger than the plain file. It is usually a bit bigger than the plain file, because 24 separate files each carry their own footer and their own dictionaries, so the compression is a little less efficient. The min and max of `price` are stored in the Parquet footer, in the metadata of each row group's column (for `year_month=2018-03`: 1 row group, 8,217 rows, min 4.99, max 4099.99, SNAPPY). For `price > 500` Spark reads only the footer first. If a row group's max is 500 or lower, it skips that whole row group without reading the data. In this single-row-group file the max is 4099.99, so `price > 500` could not skip it, but `price > 5000` could.

**#4. Windows and ties.**
(a) `customer_id` has 98,666 distinct values and `customer_unique_id` has 95,420 (data). Olist creates a new `customer_id` for every order, so `customer_id` would give a wrong "latest order per customer": it treats one person with 16 orders as 16 people. The right key is `customer_unique_id`.
(b) With `dense_rank` ordered by revenue only I get 215 rows, and with `row_number` I get 213. So there are 2 extra rows, and they come from two categories (`fashion_childrens_clothes` and `furniture_mattress_and_upholstery`). Ties in revenue are rare, but they do exist in this data, which is why I break ties with `product_id`.
(c) The first month of a seller has no previous month, so null is the honest answer: 3,095 sellers, so 3,095 rows with null `prev_month_revenue` and null growth. If I used 0, growth would be a divide-by-zero or a huge fake number, and any average of growth would be wrong.

**#5. Pruning.** The line from the plan for the month read is:
`PartitionFilters: [isnotnull(year_month#477), (year_month#477 = 2018-03)]`
The second version, filtering on `date_format(purchase_ts, 'yyyy-MM')`, shows `PartitionFilters: []` and reads all 24 folders (▢ files read in the SQL tab, versus 1 for the first version). The answer is the same 8,217 rows, but 24 times more files are read. Spark can only prune folders when I compare the partition column itself with a plain value. When I wrap something around a different column, Spark cannot connect it to the folder names.

**#6. Built-in vs UDF.** The UDF plan has a `BatchEvalPython` node that the built-in plan does not have. It means the rows leave the JVM, go to a Python process one batch at a time, and come back, and Spark cannot see inside the function to optimise it. Both versions gave the same bands: budget 9,268, mid 62,897, premium 40,485 (data, checked with pandas). Timings:

| Run | Built-in | UDF | Ratio |
|---|---|---|---|
| 1 (warm-up) | 0.350 s | 18.939 s | 54.15x |
| 2 | ▢ s | ▢ s | ▢ |
| 3 | ▢ s | ▢ s | ▢ |

On my machine the first run showed the UDF about 54x slower, much more than the old "10x" rule. Part of this is warm-up (starting the Python worker, and the built-in ran first), so runs 2 and 3 tell the fairer story. Even so, the gap is large, so my advice is: always try a built-in first (`when/otherwise` here), and write a UDF only when no built-in can express the logic. If I must, I would try a pandas UDF, which moves data in Arrow batches.

---

## Break it on purpose

| # | What I changed | What I predicted | What I saw |
|---|---|---|---|
| 1 | Removed `partitionBy` from the latest-order window | Only 1 row comes back, because the whole table is one group and only one row can have `row_number = 1`. Spark moves everything to a single partition. | ▢ rows (the right answer is 95,420). WARN line: `No Partition Defined for Window operation! Moving all data to a single partition, this can cause serious performance degradation.` Window stage: ▢ task(s). |
| 2 | Removed `repartition` in `write_silver` | More than one file per folder, because each memory partition writes its own file into every month it holds. | ▢ files in total (max ▢ in one folder), against 24 with the tidy write. |
| 3 | `partitionBy("seller_id")` on a scratch copy | 3,095 folders (one per seller), each with tiny files. | ▢ folders, ▢ files, average file ▢ KB. |
| 4 | Read, filter, then overwrite the same path (scratch copy) | Spark refuses to run it. | Error: ▢ (it says the path "is also being read from"). Files left in the folder: ▢. |
| 5 | Filtered on `purchase_ts` instead of `year_month` | Same 8,217 rows, but all 24 folders are read. | Same rows, `PartitionFilters: []`, ▢ files read. |

**Why experiment 4 matters.** Spark reads lazily. The write wants to delete the folder first, but the data it needs is still inside that same folder. Spark protects me with an error, but the dangerous versions (cache, checkpoint, or a manual delete before the write) really can leave me with a half-empty or empty folder and no way back. Plain Parquet files have no transaction log and no way to undo a write. That is exactly the problem Delta Lake solves: it writes new files first, then switches over with one atomic commit, so the old version stays readable until the new one is complete. Without it, the safe pattern is to write to a new folder and swap it in afterwards.

---

## The nine reflection questions

**1. CSV vs Parquet.** `sales` is 20.925 MB as CSV and 9.886 MB as Parquet (my run). Parquet is smaller because it stores each column together, so similar values sit side by side and compress very well, and because it uses encodings such as dictionary encoding for repeated values (for example the category and the state). It is faster for a query that needs only `price` because Spark reads only that column and ignores the other nine (column pruning).

**2. Tidy write.** `write_silver` produces 24 folders with exactly one file each, 24 files in total. Without `repartition`, I got ▢ files (max ▢ per folder), because each memory partition writes its own file into every month folder it holds data for. `repartition("year_month")` puts every row of a month into one memory partition first, so `partitionBy("year_month")` writes one file per folder.

**3. Window design.** Without the `order_id` tie-break, a customer with two orders at the exact same `purchase_ts` could get either order back, and the answer could change from run to run. This does happen in the data: 262 customers have two or more orders sharing their latest timestamp. I found out by counting orders per customer that equal the maximum `purchase_ts` (cell in the notebook), and the checker agrees with my output with the tie-break in place.

**4. Rank functions.** `dense_rank` ordered by revenue only gives 215 rows, and `row_number` gives 213. For a dashboard I would pick `row_number` with a `product_id` tie-break, because the dashboard has a fixed layout of three slots and the result is repeatable. I would use `dense_rank` only if the business says "show everyone who ties for third place".

**5. The one-partition trap.** The warning is `No Partition Defined for Window operation! Moving all data to a single partition, this can cause serious performance degradation.` In the Stages page the window stage runs with ▢ task(s) instead of the 8 I had before. At 100 GB, all the data would have to fit through one task, which means a very slow job or an out-of-memory crash, while all the other cores sit idle.

**6. Pruning.** Month read: `PartitionFilters: [isnotnull(year_month#477), (year_month#477 = 2018-03)]`. The `purchase_ts` version shows `PartitionFilters: []`. It matters because a filter that looks right can still read all 24 folders. On a table with years of data that is the difference between reading seconds and reading hours.

**7. UDF.** Timings and ratio are in the table under Pause and observe #6 (run 1: 0.350 s vs 18.939 s, 54x). I would not ship the UDF here, because a built-in `when/otherwise` does the same job and Spark can optimise it. A UDF is unavoidable when the logic has no built-in, for example calling a Python library for each row (a custom parser, a text-cleaning model, a special hash).

**8. Over-partitioning.** `partitionBy("seller_id")` gave ▢ folders, ▢ files, and an average file of ▢ KB. The data is only about 10 MB in total, so every file is tiny. The next job has to list thousands of folders and open thousands of files, and the time goes into file handling instead of reading data. Partition columns should have few values (like 24 months), not thousands.

**9. What surprised me, and what I still want to understand.** I was surprised that 1,627 rows (1.4%) would disappear silently from an inner join with no error at all, and that a filter written in a different way can turn a 1-file read into a 24-file read. One thing I still want to understand better is how Spark decides the number of tasks and memory partitions during a run (and how adaptive query execution changes it), because that decides how many files my write produces.
