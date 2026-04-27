from mcp.server.fastmcp import FastMCP

from tool_usage.tools import (
    get_current_datetime as _get_current_datetime,
    add_duration_to_datetime as _add_duration_to_datetime,
    set_reminder as _set_reminder,
    get_reminders as _get_reminders,
)

mcp = FastMCP("tool-usage-server", port=8001)


@mcp.tool()
def get_current_datetime(date_format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Returns the current date and time formatted according to the specified format string."""
    return _get_current_datetime(date_format)


@mcp.tool()
def add_duration_to_datetime(
    base_datetime: str,
    duration: str,
    output_format: str = "%Y-%m-%d %H:%M:%S",
) -> str:
    """Adds a duration to a base datetime and returns the result formatted according to the specified output format."""
    return _add_duration_to_datetime(base_datetime, duration, output_format)


@mcp.tool()
def set_reminder(reminder_time: str, message: str) -> str:
    """Sets a reminder for a specific time with a message."""
    return _set_reminder(reminder_time, message)


@mcp.tool()
def get_reminders() -> str:
    """Retrieves all currently set reminders."""
    return _get_reminders()


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
