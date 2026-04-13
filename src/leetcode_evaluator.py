from anthropic import Anthropic
from dotenv import load_dotenv

from model_evaluation import generate_evaluation_set, run_all_test_cases, grade_by_model, average_score, recommend_prompt_improvements
from helpers.cache import cached
from helpers.prompt import run_prompt


if __name__ == "__main__":
    EVALUATION_SET_PATH      = "./resources/evaluation_set.jsonl"
    ATTEMPTED_SOLUTIONS_PATH = "./resources/r2_attempted_solutions.jsonl"
    GRADER_RESULTS_PATH      = "./resources/r2_grader_results.jsonl"
    NUM_TEST_CASES           = 10

    SOLVER_PROMPT = """
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
        """

    load_dotenv("config.env")
    client = Anthropic()

    def leetcode_easy_solver(client: Anthropic, problem_description: str) -> str:
        return run_prompt(
            client,
            problem_description,
            assistant_prompt="```python",
            system_prompt=SOLVER_PROMPT,
            model="claude-haiku-4-5"
        )


    evaluation_set = cached(EVALUATION_SET_PATH,
        lambda: generate_evaluation_set(
            client,
            "assess the quality of Python scripts for solving basic leetcode questions",
            additional_instructions=[
                "The task description should finish with the expected function signature, expected parameters,"
                    "and return type. For example, def twoSum(nums: List[int], target: int) -> List[int]:",
                "Include examples of input and output for each task. For example, for the twoSum problem, you could"
                    "include an example like: Input: nums = [2,7,11,15], target = 9; Output: [0,1]."
            ],
            num_samples=NUM_TEST_CASES))

    attempted_solutions = cached(ATTEMPTED_SOLUTIONS_PATH,
        lambda: run_all_test_cases(client, leetcode_easy_solver, evaluation_set))

    grader_results = cached(GRADER_RESULTS_PATH,
        lambda: [grade_by_model(client, s) for s in attempted_solutions])

    for evaluation in grader_results:
        print(f"Task: {evaluation['task']}\n")
        print(f"Expected Output:\n{evaluation['expected_output']}\n")
        print(f"Predicted Output: {evaluation['predicted_output']}\n")
        print("Evaluation Report:")
        print(f"Strengths: {evaluation['strengths']}\n")
        print(f"Weaknesses: {evaluation['weaknesses']}\n")
        print(f"Reasoning: {evaluation['reasoning']}\n")
        print(f"Score: {evaluation['score']}\n")
        print("-" * 50)

    print(f"Average score: {average_score(grader_results):.1f}\n")
    print("Prompt improvement recommendations:")
    print(recommend_prompt_improvements(client, SOLVER_PROMPT, grader_results))
