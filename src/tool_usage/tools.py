import json
from datetime import datetime
from collections import defaultdict

from helpers.tool_registry import ToolRegistry


__reminders__ = defaultdict(list)

registry = ToolRegistry()


@registry.tool(
    description="Returns the current date and time formatted according to the specified format string.",
    param_descriptions={
        "date_format": "A strftime-compatible format string used to format the current datetime."
    }
)
def get_current_datetime(date_format: str = "%Y-%m-%d %H:%M:%S"):
    if not date_format:
        raise ValueError("date_format cannot be empty.")
    return datetime.now().strftime(date_format)


@registry.tool(
    description="Adds a duration to a base datetime and returns the result formatted according to the specified output format.",
    param_descriptions={
        "base_datetime": "The base datetime in the format '%Y-%m-%d %H:%M:%S'.",
        "duration": "The duration to add, specified as a string like '10s', '5m', '2h', '1d' (for seconds, minutes, hours, days).",
        "output_format": "A strftime-compatible format string used to format the resulting datetime."
    }
)
def add_duration_to_datetime(base_datetime: str, duration: str, output_format: str = "%Y-%m-%d %H:%M:%S"):
    import re
    from datetime import timedelta

    dt = datetime.strptime(base_datetime, "%Y-%m-%d %H:%M:%S")

    pattern = r'(\d+)([smhd])'
    matches = re.findall(pattern, duration)
    if not matches:
        raise ValueError("Invalid duration format. Use formats like '10s', '5m', '2h', '1d'.")

    for value, unit in matches:
        value = int(value)
        if unit == 's':
            dt += timedelta(seconds=value)
        elif unit == 'm':
            dt += timedelta(minutes=value)
        elif unit == 'h':
            dt += timedelta(hours=value)
        elif unit == 'd':
            dt += timedelta(days=value)

    return dt.strftime(output_format)


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


@registry.tool(description="Retrieves all currently set reminders.")
def get_reminders():
    return json.dumps(__reminders__)
