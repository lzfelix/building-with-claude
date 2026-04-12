from anthropic import Anthropic
from dotenv import load_dotenv

from model_evaluation import generate_evaluation_set, run_all_test_cases, grade_by_model
from helpers.cache import cached
from helpers.prompt import run_prompt

EVALUATION_SET_PATH = "./resources/evaluation_set.jsonl"
ATTEMPTED_SOLUTIONS_PATH = "./resources/attempted_solutions.jsonl"
GRADER_RESULTS_PATH = "./resources/grader_results.jsonl"

load_dotenv("config.env")
client = Anthropic()


def leetcode_easy_solver(client: Anthropic, problem_description: str) -> str:
    additional_instructions = """
    Just write the Python function, without any explanations. Your snippet should
    start with the function definition, and end with the end of the function.
    Do not include any text before or after the code snippet. The solution should
    use the function signature provided in the task description.
    """

    return run_prompt(
        client,
        problem_description,
        assistant_prompt="```python",
        system_prompt=additional_instructions,
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
        num_samples=3))

attempted_solutions = cached(ATTEMPTED_SOLUTIONS_PATH,
    lambda: run_all_test_cases(client, leetcode_easy_solver, evaluation_set))

grader_results = cached(GRADER_RESULTS_PATH,
    lambda: [grade_by_model(client, s) for s in attempted_solutions])

for evaluation in grader_results:
    print(f"Task: {evaluation['task']}\n")
    print(f"Expected Output: {evaluation['expected_output']}\n")
    print(f"Predicted Output: {evaluation['predicted_output']}\n")
    print("Evaluation Report:")
    print(f"Strengths: {evaluation['strengths']}\n")
    print(f"Weaknesses: {evaluation['weaknesses']}\n")
    print(f"Reasoning: {evaluation['reasoning']}\n")
    print(f"Score: {evaluation['score']}\n")
    print("-" * 50)
