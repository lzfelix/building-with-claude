# Tool Usage with Prompt Caching

This example extends `src/tool_usage.py` with a prompt caching layer. The agent logic and tool registry are unchanged; the only additions are two `cache_control` markers and a few lines that print cache usage after each API call.

## What prompt caching does

When the same prefix is sent repeatedly, the API can serve it from a cache instead of reprocessing it from scratch. A cached token costs roughly one-tenth of a normal input token to read. For prefixes that are stable across requests — a system prompt, a tool list, a large document — this compounds quickly over a long conversation.

Caching is a prefix match: `tools → system → messages`, in that order. A `cache_control` marker on a block tells the API to cache everything up to and including that block. Any byte change anywhere before the marker invalidates the cache entry.

## Cache thresholds vary by model

Not every prefix qualifies for caching. Each model enforces a minimum token count before it will create a cache entry. If the prefix is too short, the API silently skips caching — no error, just `cache_creation_input_tokens: 0` in the response.

| Model | Minimum tokens to cache |
|---|---|
| Sonnet 4.5, Sonnet 4.1, Sonnet 4 | 1 024 |
| Opus 4.7, Opus 4.6, Haiku 4.5 | 4 096 |

This is a non-obvious footgun. Haiku is cheaper per token, which makes it an attractive default — but its 4 096-token threshold means a modest system prompt will never cache at all, quietly negating the saving. Sonnet costs more per token but starts caching at 1 024 tokens, making it the better choice whenever the cacheable prefix is small.

This example uses `claude-sonnet-4-5` for exactly this reason.

## Why the tools alone are not enough

The four tools registered in `src/tool_usage/tools.py` — `get_current_datetime`, `add_duration_to_datetime`, `set_reminder`, `get_reminders` — together produce roughly 350 tokens of schema. That is comfortably below the 1 024-token threshold, so placing a `cache_control` marker on the last tool schema (via `registry.schemas_as_cacheable`) would have no effect on its own.

To actually trigger caching, the prefix must reach the threshold. Rather than artificially inflating the tool definitions, the example adds a verbose system prompt that brings the total (tools + system) above 1 024 tokens. The constant is named `UNNECESSARILY_LONG_INSTRUCTIONS` to make this intent explicit — in a real application the system prompt would carry its weight through genuine instructions, documentation, or few-shot examples.

## What changed from `tool_usage.py`

**`ToolRegistry.run_tools()`** was moved from the standalone `run_tools()` function in `tool_usage.py` into the registry itself. This keeps dispatch and result formatting in one place and makes the call site in `chat_with_report()` cleaner.

**`registry.schemas_as_cacheable`** replaces `registry.schemas` at the call site. The property deep-copies the schema list and attaches `cache_control: {type: "ephemeral"}` to the last entry, marking the entire tool prefix as cacheable without modifying the underlying registry.

**`send_cached_message()`** is the equivalent of `chat()` in `tool_usage.py`. The difference is the system prompt is passed as a content block list rather than a plain string, which is required to attach `cache_control` to it.

**`chat_with_report()`** is the equivalent of `run_conversation()`. It wraps the same tool loop and adds three print lines after each API call:

```
cache_creation: <tokens written to cache>
cache_read:     <tokens served from cache>
input_tokens:   <tokens billed at full price>
```

On the first request `cache_creation` is non-zero and `cache_read` is zero. From the second request onward, the stable prefix (tools + system prompt) is served from cache: `cache_read` jumps to reflect those tokens and `input_tokens` drops to cover only the new conversation turns.

## Verifying a cache hit

Running the script produces two exchanges. The first message ("What time is it right now?") writes the cache entry. The second message ("What day will it be three days from now?") reads it:

```
Turn 1
    cache_creation: 1341
    cache_read:     0
    input_tokens:   18
...
--------------------------------------------------
Turn 1
    cache_creation: 0
    cache_read:     1341
    input_tokens:   52
```

The `cache_read` value on the second exchange matches the `cache_creation` value from the first. The `input_tokens` on the second exchange covers only the new user message and the accumulated conversation history — everything before the last `cache_control` breakpoint is free.
