# LeetCode Evaluator

This demo evaluates the quality of an LLM-generated Python solver for LeetCode-style problems. It is structured as a three-stage pipeline: generate an evaluation dataset, run the solver against it, then grade each solution and aggregate the results.

## Pipeline

```
generate_evaluation_set → run_all_test_cases → grade_by_model → recommend_prompt_improvements
```

Each stage is cached to disk as a JSONL file before moving to the next.

## Caching as an iterative development strategy

Each stage of the pipeline is expensive: it makes LLM calls that cost money and time, and the outputs are non-deterministic. To make iterative development faster, cheaper, and more predictable, results are cached to disk after the first run. Subsequent runs skip the LLM calls entirely and load from the cached files.

This has an important trade-off: **caching pins a non-deterministic flow to a fixed snapshot**. The evaluation set, the solutions, and the grades will not change between runs unless the cache is deleted. This is a feature when building and reasoning about the next stage — you know exactly what input the next component will receive — but it means the cached results may not reflect how the system would behave on a fresh run.

## Round 1 results

### Solver prompt

```
Just write the Python function, without any explanations. Your snippet should
start with the function definition, and end with the end of the function.
Do not include any text before or after the code snippet. The solution should
use the function signature provided in the task description.
```

### Scores

| Problem | Score |
|---|---|
| Two Sum | 9/10 |
| Longest Substring Without Repeating Characters | 9/10 |
| Reverse Linked List | 9/10 |
| **Average** | **9.0/10** |

### Observed strengths

- Correct algorithms with optimal time complexity (hash map, sliding window, iterative pointer reversal)
- Proper logic flow — e.g., checking for the complement before inserting prevents reuse of the same element
- Clean, readable code with descriptive variable names
- Edge cases handled implicitly and correctly (empty lists, single-node lists)

### Observed weaknesses

- Missing import statements — `List`, `Optional` from `typing` are used in type hints but not imported
- Non-Pythonic iteration style — `range(len(s))` used instead of `enumerate()`
- Verbose inline comments in some solutions where the logic is self-evident
- No explicit input validation, though the problem constraints make this unnecessary

### Prompt improvement recommendations

The grader identified the following concrete changes to the solver prompt:

1. **Require necessary imports** — explicitly ask for `from typing import List, Optional` (or equivalent) at the top of each snippet
2. **Encourage idiomatic Python** — prefer `enumerate()` over `range(len())` for iteration
3. **Constrain comment verbosity** — specify that comments should only be included where logic is non-obvious
4. **Preserve existing constraints** — the instruction to use the provided function signature is working well and should be kept

A follow-up round will incorporate these suggestions into the solver prompt and re-run the full evaluation to measure whether the scores improve.
