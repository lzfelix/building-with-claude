# Tool Usage

This example follows the Anthropic Skilljar course on tool use and extends it with a lightweight abstraction that resembles how [FastMCP](https://github.com/jlowin/fastmcp) works at its core.

## What the course covers

The course introduces Claude's tool use feature: you define a set of tools as JSON schemas, pass them to the API, and Claude decides when to call them. When the model returns a `tool_use` stop reason, your code executes the requested tool, appends the result to the message history, and loops back to the model. This cycle repeats until the model produces a final text response.

The example implements a reminder assistant that can fetch the current date and time, perform date arithmetic, set reminders, and list existing appointments.

## The problem with raw tool use

The Anthropic SDK represents each tool as a `ToolParam` object containing a hand-written JSON Schema. Every tool therefore requires two things: the Python function that implements it, and a separate schema object that describes it to the model. Adding a new tool means touching two places, and the schema can silently diverge from the function signature.

## A poor man's FastMCP

FastMCP solves this by letting you decorate a Python function with `@mcp.tool()` and deriving the schema automatically from the function signature. The same idea applies here, within the Claude API, without any MCP transport layer.

`src/helpers/tool_registry.py` introduces `ToolRegistry`, a small class that does three things.

**Schema generation.** When you decorate a function with `@registry.tool()`, the registry inspects the function signature using `inspect.signature()` and `typing.get_type_hints()`. It maps Python types to JSON Schema types (`str` to `"string"`, `int` to `"integer"`, and so on), derives required fields from parameters that have no default, and wraps the result in a `ToolParam`. The tool description comes from a `description` argument on the decorator, falling back to the first line of the function docstring.

**Tool registration.** The registry keeps a `dict` mapping each tool name to its callable, and a `list` of the generated schemas.

**Dispatch.** `registry.dispatch(name, inputs)` looks up the callable by name and calls it with the provided inputs. This replaces an `if/elif` chain that had to be updated every time a tool was added or removed.

From the call site in `src/tool_usage.py`, the change is minimal: `tools.registry.schemas` replaces the manual list of schema objects, and `tools.registry.dispatch(name, inputs)` replaces the branching dispatcher. Because the agent reads `registry.schemas` and routes through `registry.dispatch` at runtime, a newly decorated function is immediately available to the model with no changes to the agent code.

## Registering a tool

```python
@registry.tool(
    description="Sets a reminder for a specific time with a message.",
    param_descriptions={
        "reminder_time": "The time to set the reminder for, in the format '%Y-%m-%d %H:%M:%S'.",
        "message": "The message to be reminded of."
    }
)
def set_reminder(reminder_time: str, message: str):
    __reminders__[reminder_time].append(message)
    return f"Reminder set for {reminder_time} with message: '{message}'"
```

No schema object is written by hand. The `required` list is inferred from the absence of default values, and the property types are inferred from the type annotations.

## Extending the example: listing appointments

Because adding a tool no longer requires a parallel schema definition, a new dispatcher branch, or any change to the agent loop, extending the assistant is straightforward. The `get_reminders` tool, which lists all existing appointments, requires nothing more than a decorated function:

```python
@registry.tool(description="Retrieves all currently set reminders.")
def get_reminders():
    return json.dumps(__reminders__)
```

The registry detects that there are no parameters, generates an empty `properties` object, omits `required`, and makes the tool available to the model immediately. The agent picks it up automatically on the next run.

## The agentic loop

```
user message
    → Claude API (with registry.schemas)
    → stop_reason == "tool_use"
        → registry.dispatch(name, inputs) for each tool_use block
        → append tool_result blocks to history
    → loop
    → stop_reason != "tool_use"
        → return final text response
```

This loop lives in `run_conversation()` in `src/tool_usage.py` and is unchanged from the course material. The registry abstraction sits entirely below it.

## Limitations

The registry intentionally stays small. It does not parse parameter descriptions from docstrings, does not support complex types such as `list` or `dict` in the schema, and does not provide an MCP transport layer. It is a demonstration of how schema generation and dispatch can be unified, not a production framework.
