import inspect
from typing import Any, Callable, get_type_hints
from anthropic.types import ToolParam


_PY_TO_JSON_TYPE: dict[type, str] = {
    str:   "string",
    int:   "integer",
    float: "number",
    bool:  "boolean",
}


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Callable] = {}
        self._schemas: list[ToolParam] = []

    def tool(
        self,
        description: str | None = None,
        param_descriptions: dict[str, str] | None = None,
    ):
        def decorator(fn: Callable) -> Callable:
            resolved_desc = description or _first_docstring_line(fn)
            schema = _build_schema(fn, resolved_desc, param_descriptions or {})
            self._tools[fn.__name__] = fn
            self._schemas.append(ToolParam(schema))
            return fn
        return decorator

    @property
    def schemas(self) -> list[ToolParam]:
        return self._schemas

    def dispatch(self, name: str, inputs: dict[str, Any]) -> Any:
        if name not in self._tools:
            raise ValueError(f"Unknown tool: {name}")
        return self._tools[name](**inputs)


def _first_docstring_line(fn: Callable) -> str:
    doc = inspect.getdoc(fn) or ""
    return doc.splitlines()[0] if doc else ""


def _build_schema(fn: Callable, description: str, param_descriptions: dict[str, str]) -> dict:
    sig = inspect.signature(fn)
    hints = get_type_hints(fn)
    properties: dict[str, Any] = {}
    required: list[str] = []

    for param_name, param in sig.parameters.items():
        py_type = hints.get(param_name, str)
        prop: dict[str, Any] = {"type": _PY_TO_JSON_TYPE.get(py_type, "string")}

        if param_name in param_descriptions:
            prop["description"] = param_descriptions[param_name]

        if param.default is inspect.Parameter.empty:
            required.append(param_name)
        else:
            prop["default"] = param.default

        properties[param_name] = prop

    schema: dict[str, Any] = {
        "name": fn.__name__,
        "description": description,
        "input_schema": {"type": "object", "properties": properties},
    }
    if required:
        schema["input_schema"]["required"] = required

    return schema
