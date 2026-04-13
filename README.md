# Building with Claude

Just me following Skilljar's Claude [Building with Claude](https://anthropic.skilljar.com/claude-with-the-anthropic-api) while I add a bit of experimentation and personal touch along the way.

# How to use

1. Create a `config.env` file with your `ANTHROPIC_API_KEY`. Use the `config.env.example` as a guide
2. Install dependencies with `uv sync`
3. Now you can run the examples. More instructions to come later

## Available examples

Detailed write-ups for each example can be found in the [`docs/`](docs/) directory.

| Example | Description |
|---|---|
| [LeetCode Evaluator](docs/leetcode-evaluator.md) | Evaluates an LLM-generated Python solver across LeetCode-style problems using a multi-stage grading pipeline |
| [SQL Review](docs/sql-review.md) | Evaluates an LLM-generated PostgreSQL query solver across tasks from simple SELECT to window functions |
