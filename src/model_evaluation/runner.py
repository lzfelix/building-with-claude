from typing import Callable

from anthropic import Anthropic


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
