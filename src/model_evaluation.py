import os
import json
from typing import Callable

from anthropic import Anthropic
from dotenv import load_dotenv


def generate_evaluation_set(
        client: Anthropic,
        task_description: str,
        model: str="claude-haiku-4-5",
        additional_instructions: list[str] | None=None,
        max_tokens: int=10000,
        num_samples: int=100) -> list[dict]:
    prompt = f"""Generate an evaluation dataset for a prompt evaluation.
    The dataset will be used to {task_description}. Generate an array of
    JSON objects, each representing a task. The array should contain
    {num_samples} tasks.

    Example output:
    ```json
    [
        {{"task": "<task description>", "expected output": "<the solution for the task>"}},
        ...
    ]
    ```

    Additional instructions
    * Focus on tasks that are relevant to the task description.
    * Ensure that the expected output is clear and unambiguous.
    * Avoid generating tasks that are too similar to each other.
    """
    if additional_instructions:
        prompt += "\n" + "\n".join(f"* {instruction}" for instruction in additional_instructions)

    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )

    flat_output = response.content[0].text
    flat_output = flat_output.replace("```json", "").replace("```", "")
    return json.loads(flat_output)


def save_as_jsonl(evaluation_set: list[dict], file_path: str):
    with open(file_path, "w") as f:
        for item in evaluation_set:
            json_line = json.dumps(item)
            f.write(json_line + "\n")


def load_jsonl(file_path: str) -> list[dict]:
    evaluation_set = []
    with open(file_path, "r") as f:
        for line in f:
            evaluation_set.append(json.loads(line))
    return evaluation_set


def run_single_test_case(
        client: Anthropic,
        evaluated_fn: Callable,
        test_case: dict) -> dict:

    return {
        "task": test_case["task"],
        "expected_output": test_case["expected_output"],
        "predicted_output": evaluated_fn(client, test_case["task"])
    }


def run_all_test_cases(client: Anthropic, evaluated_fn: Callable, dataset: list[dict]):
    return [
        run_single_test_case(client, evaluated_fn, test_case)
        for test_case in dataset
    ]


def run_prompt(
        client: Anthropic,
        prompt: str,
        model: str,
        stop_sequences: list[str] | None=None,
        assistant_prompt: str | None=None,
        max_tokens: int=10000,
        system_prompt: str | None=None) -> str:
    messages = [
        {"role": "user", "content": prompt}
    ]

    if assistant_prompt:
        messages.append({"role": "assistant", "content": assistant_prompt})

    args = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": messages
    }
    if system_prompt:
        args["system"] = system_prompt
    if stop_sequences:
        args["stop_sequences"] = stop_sequences

    response = client.messages.create(**args)
    return response.content[0].text


def grade_by_model(client: Anthropic, test_case: dict) -> dict:
    # Create evaluation prompt
    eval_prompt = f"""
    You are an expert code reviewer. Evaluate this AI-generated solution.

    Task: {test_case['task']}
    Generated solution: {test_case['predicted_output']}
    Ground truth solution: {test_case['expected_output']}

    Provide your evaluation as a structured JSON object with:
    - "strengths": An array of 1-3 key strengths
    - "weaknesses": An array of 1-3 key areas for improvement
    - "reasoning": A concise explanation of your assessment and why not maximum grade was given, if applicable.
    - "score": A number between 1-10

    The generated solution does not need to match perfectly the ground truth
    to receive a high score, as there can be multiple valid approaches.
    Focus on the correctness, efficiency, and clarity of the generated solution.
    """

    model_output = run_prompt(client, eval_prompt, model="claude-haiku-4-5", assistant_prompt="```json", stop_sequences=["```"])

    evaluation_report = json.loads(model_output)
    return evaluation_report | test_case


if __name__ == "__main__":
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

    if not os.path.exists(EVALUATION_SET_PATH):
        print("Generating evaluation set...")
        evaluation_set = generate_evaluation_set(
            client,
            "assess the quality of Python scripts for solving basic leetcode questions",
            additional_instructions=[
                "The task description should finish with the expected function signature, expected parameters, and return type. For example, def twoSum(nums: List[int], target: int) -> List[int]:",
                "Include examples of input and output for each task. For example, for the twoSum problem, you could include an example like: Input: nums = [2,7,11,15], target = 9; Output: [0,1]."
            ],
            num_samples=3)
        save_as_jsonl(evaluation_set, EVALUATION_SET_PATH)
    else:
        print("Evaluation set already exists, loading from file...")
        evaluation_set = load_jsonl(EVALUATION_SET_PATH)

    if not os.path.exists(ATTEMPTED_SOLUTIONS_PATH):
        print("Generating attempted solutions...")
        attempted_solutions = run_all_test_cases(client, leetcode_easy_solver, evaluation_set)
        save_as_jsonl(attempted_solutions, ATTEMPTED_SOLUTIONS_PATH)
    else:
        print("Attempted solutions already exist, loading from file...")
        attempted_solutions = load_jsonl(ATTEMPTED_SOLUTIONS_PATH)

    if not os.path.exists(GRADER_RESULTS_PATH):
        print("Grading attempted solutions...")
        grader_results = [
            grade_by_model(client, attempted_solution)
            for attempted_solution in attempted_solutions
        ]
        save_as_jsonl(grader_results, GRADER_RESULTS_PATH)
    else:
        print("Grader results already exist, loading from file...")
        grader_results = load_jsonl(GRADER_RESULTS_PATH)

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
