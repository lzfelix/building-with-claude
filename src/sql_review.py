from anthropic import Anthropic
from dotenv import load_dotenv

from model_evaluation import generate_evaluation_set, run_all_test_cases, grade_by_model, average_score, recommend_prompt_improvements
from helpers.cache import cached
from helpers.prompt import run_prompt


if __name__ == "__main__":
    EVALUATION_SET_PATH      = "./resources/mdoel_evaluation/sql_evaluation_set.jsonl"
    ATTEMPTED_SOLUTIONS_PATH = "./resources/mdoel_evaluation/sql_attempted_solutions.jsonl"
    GRADER_RESULTS_PATH      = "./resources/mdoel_evaluation/sql_grader_results.jsonl"
    NUM_TEST_CASES           = 10

    SOLVER_PROMPT = """
    Write a PostgreSQL query that solves the given task.
    Write only the SQL query — no explanations, no markdown, no surrounding text.
    The query must be syntactically correct and directly executable.
    Use the exact table and column names specified in the task description.
    """

    load_dotenv("config.env")
    client = Anthropic()

    def sql_solver(client: Anthropic, task_description: str) -> str:
        return run_prompt(
            client,
            task_description,
            assistant_prompt="```sql",
            stop_sequences=["```"],
            system_prompt=SOLVER_PROMPT,
            model="claude-haiku-4-5"
        )

    evaluation_set = cached(EVALUATION_SET_PATH,
        lambda: generate_evaluation_set(
            client,
            "assess the quality of PostgreSQL queries for solving database tasks",
            additional_instructions=[
                "Each task must include a table schema describing column names and their types.",
                "Distribute the 10 tasks by complexity: 2 simple SELECT queries, 2 WHERE/ORDER BY queries,"
                    " 2 GROUP BY with aggregation, 2 JOIN queries across multiple tables,"
                    " 2 window function queries (e.g. ROW_NUMBER, RANK, LAG, running totals).",
                "The expected output must be a correct, complete PostgreSQL query.",
                "Use realistic table and column names such as orders, customers, employees, products,"
                    " order_items, departments, salaries.",
                "Include a concrete example of what the query should return given sample data.",
            ],
            num_samples=NUM_TEST_CASES))

    attempted_solutions = cached(ATTEMPTED_SOLUTIONS_PATH,
        lambda: run_all_test_cases(client, sql_solver, evaluation_set))

    grader_results = cached(GRADER_RESULTS_PATH,
        lambda: [grade_by_model(client, s) for s in attempted_solutions])

    for evaluation in grader_results:
        print(f"Task: {evaluation['task']}\n")
        print(f"Expected Output:\n{evaluation['expected_output']}\n")
        print(f"Predicted Output:\n{evaluation['predicted_output']}\n")
        print("Evaluation Report:")
        print(f"Strengths: {evaluation['strengths']}\n")
        print(f"Weaknesses: {evaluation['weaknesses']}\n")
        print(f"Reasoning: {evaluation['reasoning']}\n")
        print(f"Score: {evaluation['score']}\n")
        print("-" * 50)

    print(f"Average score: {average_score(grader_results):.1f}\n")
    print("Prompt improvement recommendations:")
    print(recommend_prompt_improvements(client, SOLVER_PROMPT, grader_results))
