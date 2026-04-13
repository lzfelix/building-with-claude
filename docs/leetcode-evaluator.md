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

In round 2, the evaluation set was reused (same 10 problems) and only the solver and its caches were replaced, making the comparison between rounds as controlled as possible.

---

## Round 1

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
| Two Sum | 8/10 |
| Longest Substring Without Repeating Characters | 9/10 |
| Palindrome Integer (no string conversion) | 8/10 |
| Search Range (sorted array) | 7/10 |
| Valid Parentheses | 9/10 |
| Reverse Linked List | 9/10 |
| Product of Array Except Self | 9/10 |
| Container With Most Water | 9/10 |
| Longest Palindromic Substring | 8/10 |
| Median of Two Sorted Arrays | 9/10 |
| **Average** | **8.5/10** |

### Observed strengths

- Correct algorithms with optimal time complexity across the board
- Proper logic flow in hash-map, sliding window, and two-pointer problems
- Clean, readable code with descriptive variable names
- Edge cases handled correctly even when not explicitly addressed

### Observed weaknesses

- Missing import statements — `List`, `Optional` from `typing` used but not imported
- Non-Pythonic iteration style — `range(len(s))` used instead of `enumerate()`
- Verbose inline comments in solutions where the logic is self-evident
- Redundant early returns and unreachable fallback return statements
- Less elegant binary search boundary logic compared to ground truth (Search Range)
- Index-based palindrome tracking instead of returning substrings directly

### Prompt improvement recommendations (from evaluator)

The grader recommended a more structured prompt with five explicit requirement sections:

1. **Format** — start with imports, then the function definition; no surrounding text or markdown
2. **Code quality** — include all necessary imports; comments only where logic is non-obvious
3. **Correctness** — handle all edge cases from the problem statement; remove unreachable dead code
4. **Style** — prefer `not stack` over `len(stack) == 0`; `enumerate()` over `range(len())`; consistent and descriptive naming
5. **Optimization** — implement the optimal algorithm for the problem

---

## Round 2

### Solver prompt (updated based on round 1 recommendations)

```
Write a Python function that solves the given task. Follow these requirements:

Format Requirements:
- Start with any necessary import statements, followed by the function definition, and end with the end of the function
- Include no text, explanations, or markdown before/after the code
- Use the exact function signature provided in the task description

Code Quality Requirements:
- Include all necessary import statements (e.g., from typing import List, Optional)
- Add brief comments only where the logic is non-obvious

Correctness Requirements:
- Handle all constraints and edge cases mentioned in the problem statement
- Ensure all code paths are reachable and meaningful (no unreachable dead code)

Code Style Requirements:
- Use idiomatic Python conventions (e.g., not stack instead of len(stack) == 0, enumerate() over range(len()))
- Use descriptive variable names and maintain consistent naming throughout
- Avoid redundant operations (e.g., unnecessary early returns, redundant variable initialization)

Optimization Requirements:
- Implement the optimal algorithm for the problem in terms of time complexity
```

### Scores

| Problem | R1 | R2 | Delta |
|---|---|---|---|
| Two Sum | 8 | 9 | +1 |
| Longest Substring Without Repeating Characters | 9 | 9 | 0 |
| Palindrome Integer (no string conversion) | 8 | 9 | +1 |
| Search Range (sorted array) | 7 | 7 | 0 |
| Valid Parentheses | 9 | 9 | 0 |
| Reverse Linked List | 9 | 9 | 0 |
| Product of Array Except Self | 9 | 9 | 0 |
| Container With Most Water | 9 | 9 | 0 |
| Longest Palindromic Substring | 8 | 8 | 0 |
| Median of Two Sorted Arrays | 9 | 8 | -1 |
| **Average** | **8.5** | **8.6** | **+0.1** |

### Observed strengths

- Correct algorithms with optimal time complexity maintained across all problems
- Import statements now consistently included (`from typing import List/Optional`)
- `enumerate()` adopted in place of `range(len())` for iteration
- Well-documented code with comments explaining algorithmic choices and greedy strategies
- Edge cases handled correctly in all solutions

### Observed weaknesses

- Unreachable return statements persist — `return []` when the problem guarantees a solution (Two Sum), `return -1.0` in Median of Two Sorted Arrays
- Unused variable introduced — `original = x` assigned but never referenced (Palindrome Integer)
- `len(stack) == 0` still used instead of `not stack` (Valid Parentheses)
- Index-tracking approach in Longest Palindromic Substring instead of returning the substring directly from the helper
- Duplicated binary search logic in Search Range instead of extracting a shared helper
- Explanation text leaked outside the code block in several solutions (Product Except Self, Container With Most Water, Median of Two Sorted Arrays)

### What improved

- **Import statements** — round 2 solutions consistently included `from typing import List/Optional`, directly addressing the top weakness from round 1
- **Pythonic style** — `enumerate()` adopted correctly in Longest Substring (round 1 used `range(len())`)
- **Palindrome Integer** — unnecessary `x < 10` early return removed; conditions tightened

### What didn't change

- **Search Range (7/7)** — the binary search boundary approach remains less elegant than ground truth; the prompt alone doesn't fix a pattern the model doesn't naturally reach
- **Longest Palindromic Substring (8/8)** — index-tracking vs. substring-returning design is a structural choice the prompt doesn't guide
- **Median of Two Sorted Arrays (9→8)** — slight regression: the `float()` cast and unreachable `-1.0` return persisted despite the dead code guidance; grader was stricter this round

### Round 2 improvement recommendations (from evaluator)

The grader identified further refinements to the prompt:

1. **Explicit dead code elimination** — require removing unreachable returns and unused variables, and add an assertion in their place if the algorithm guarantees a solution
2. **Semantic variable naming** — prefer names that express role (`odd`/`even`, `left_max`/`right_min`) over sequential labels (`left1`/`left2`)
3. **Helper function design** — helpers should return the final result (e.g., the substring), not intermediate indices the caller then has to post-process
4. **Code duplication** — when binary searches for left and right boundaries have near-identical logic, extract a shared helper
5. **Pythonic boolean checks** — reinforce `not stack`, `not array`, `if value` patterns with concrete examples

A follow-up round will incorporate these suggestions.
