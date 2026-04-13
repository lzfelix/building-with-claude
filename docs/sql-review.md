# SQL Review

This demo evaluates the quality of an LLM-generated PostgreSQL query solver across tasks of increasing complexity. It reuses the same model-evaluation pipeline as the LeetCode evaluator — generate an evaluation dataset, run the solver, grade each solution, then aggregate and recommend improvements.

## Pipeline

```
generate_evaluation_set → run_all_test_cases → grade_by_model → recommend_prompt_improvements
```

Each stage is cached to disk as a JSONL file before moving to the next.

## Caching as an iterative development strategy

Each stage of the pipeline is expensive: it makes LLM calls that cost money and time, and the outputs are non-deterministic. Caching results to disk after the first run makes subsequent iterations faster, cheaper, and fully reproducible — the next stage always receives the exact same input.

The trade-off is the same as in the LeetCode evaluator: **caching pins a non-deterministic flow to a fixed snapshot**. The graded results will not change between runs unless the cache is deleted. This is desirable when reasoning about one stage in isolation, but the cached results may not reflect what the system would produce on a fresh run.

---

## Round 1

### Solver prompt

```
Write a PostgreSQL query that solves the given task.
Write only the SQL query — no explanations, no markdown, no surrounding text.
The query must be syntactically correct and directly executable.
Use the exact table and column names specified in the task description.
```

### Scores

| Problem | Complexity | Score |
|---|---|---|
| Retrieve all customer information | Simple SELECT | 9/10 |
| List product names and prices | Simple SELECT | 9/10 |
| Find orders by city, sorted by date | WHERE + JOIN + ORDER BY | 9/10 |
| Get employees with salary > 50000 | WHERE + ORDER BY | 9/10 |
| Total sales and order count per customer | GROUP BY + aggregation | 7/10 |
| Average salary by department (HAVING) | GROUP BY + HAVING + JOIN | 9/10 |
| Orders with customer full names | JOIN + CONCAT | 9/10 |
| Order items with extended price | JOIN + computed column | 8/10 |
| Rank employees by salary within department | ROW_NUMBER window | 8/10 |
| Running total of order amounts per customer | SUM OVER window | 7/10 |
| **Average** | | **8.4/10** |

### Observed strengths

- Correct SQL logic across all query types — filters, joins, aggregations, and window functions
- Proper JOIN syntax with appropriate table aliases (`o`, `c`, `e`, `d`)
- Correct use of PARTITION BY and ORDER BY inside window functions
- Correct aggregation functions (`SUM`, `AVG`, `COUNT`) and `HAVING` filtering
- Multi-line formatting improves readability on complex queries

### Observed weaknesses

- **Over-engineering** — several queries add `ORDER BY`, extra columns, or `LEFT JOIN` that were not requested by the task; adding `LEFT JOIN` when `INNER JOIN` is sufficient introduces unintended semantic differences
- **Missing explicit window frame** — running total query omitted `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`, which works by default in PostgreSQL but is less portable and less readable
- **Inconsistent column selection** — some queries use `SELECT *`, others list columns explicitly; neither is consistently applied based on task requirements
- **Redundant GROUP BY columns** — joining to get `first_name`/`last_name` required adding them to `GROUP BY`, adding complexity beyond what the task asked for
- **Extra tiebreaker in window ORDER BY** — the running total query added `ORDER BY order_date, order_id` when `order_date` alone was sufficient given the sample data

### Prompt improvement recommendations (from evaluator)

The grader recommended adding explicit guidance in six areas:

1. **Column selection** — name columns explicitly when the task specifies them; use `SELECT *` only when all columns are requested
2. **No unsolicited clauses** — add `ORDER BY` or `WHERE` only if the task requires it or if correctness depends on it
3. **JOIN type** — default to `INNER JOIN`; use `LEFT JOIN` only when the task explicitly requires preserving unmatched rows
4. **Window frame** — always include `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` for running totals; use the most direct column reference in `PARTITION BY`
5. **Formatting** — single line unless the query exceeds ~120 characters
6. **No defensive coding** — skip `NULL` checks and input validation unless the task mentions missing data

A follow-up round will incorporate these suggestions.
