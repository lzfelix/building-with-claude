import json

from anthropic import Anthropic

from helpers.prompt import run_prompt


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

    flat_output = run_prompt(client, prompt, model=model, max_tokens=max_tokens)
    flat_output = flat_output.replace("```json", "").replace("```", "")
    return json.loads(flat_output)
