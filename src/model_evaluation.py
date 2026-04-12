import os
import json
from typing import Callable

from anthropic import Anthropic
from dotenv import load_dotenv


def generate_evaluation_set(
        client: Anthropic,
        task_description: str,
        model: str="claude-haiku-4-5",
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
    * Avoid generating tasks that are too difficult or too easy. Aim for a range of difficulty levels.
    """

    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )

    flat_output = response.content[0].text
    flat_output = flat_output.replace("```json", "").replace("```", "")
    return json.loads(flat_output)


def persist_evaluation_set_as_jsonl(evaluation_set: list[dict], file_path: str):
    with open(file_path, "w") as f:
        for item in evaluation_set:
            json_line = json.dumps(item)
            f.write(json_line + "\n")


def load_evaluation_set_from_jsonl(file_path: str) -> list[dict]:
    evaluation_set = []
    with open(file_path, "r") as f:
        for line in f:
            evaluation_set.append(json.loads(line))
    return evaluation_set


def run_test_case(
        client: Anthropic,
        evaluated_fn: Callable,
        test_case: dict) -> dict:
    
    predicted_response = evaluated_fn(client, test_case["task"])
    score = 10

    return {
        "task": test_case["task"],
        "expected_output": test_case["expected_output"],
        "predicted_output": predicted_response,
        "score": score
    }


def run_eval(client: Anthropic, evaluated_fn: Callable, dataset: list[dict]):
    return [
        run_test_case(client, evaluated_fn, test_case)
        for test_case in dataset
    ]


def run_prompt(
        client: Anthropic,
        prompt: str,
        model: str,
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
        "messages": messages,
        "stop_sequences": ["```"]
    }
    if system_prompt:
        args["system"] = system_prompt

    response = client.messages.create(**args)
    return response.content[0].text


if __name__ == "__main__":
    EVALUATION_SET_PATH = "evaluation_set.jsonl"

    load_dotenv("config.env")
    client = Anthropic()

    def leetcode_easy_solver(client: Anthropic, problem_description: str) -> str:
        additional_instructions = """
        Just write the Python function, without any explanations. Your snippet should
        start with the function definition, and end with the end of the function.
        Do not include any text before or after the code snippet. The function should
        always be named "solution".
        """

        return run_prompt(
            client,
            problem_description,
            assistant_prompt="```python",
            system_prompt=additional_instructions,
            model="claude-haiku-4-5"
        )

    if not os.path.exists(EVALUATION_SET_PATH):
        evaluation_set = generate_evaluation_set(client, "assess the quality of Python scripts for solving basic leetcode questions", num_samples=3)
        persist_evaluation_set_as_jsonl(evaluation_set, EVALUATION_SET_PATH)
    else:
        evaluation_set = load_evaluation_set_from_jsonl(EVALUATION_SET_PATH)

    evaluation_report = run_eval(client, leetcode_easy_solver, evaluation_set)
    print(json.dumps(evaluation_report, indent=2))
