import json
from datetime import datetime
from collections import defaultdict

from anthropic.types import ToolParam


# This will store reminders in-memory for demonstration purposes
__reminders__ = defaultdict(list)


def get_current_datetime(date_format="%Y-%m-%d %H:%M:%S"):
    if not date_format:
        raise ValueError("date_format cannot be empty.")
    return datetime.now().strftime(date_format)


get_current_datetime_schema = ToolParam({
    "name": "get_current_datetime",
    "description": "Returns the current date and time formatted according to the specified format string.",
    "input_schema": {
        "type": "object",
        "properties": {
        "date_format": {
            "type": "string",
            "description": "A strftime-compatible format string used to format the current datetime.",
            "default": "%Y-%m-%d %H:%M:%S"
        }
        },                                                                      
            "required": ["date_format"]
    }
})


def add_duration_to_datetime(base_datetime: str, duration: str, output_format: str="%Y-%m-%d %H:%M:%S"):
    from datetime import datetime, timedelta
    import re

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


add_duration_to_datetime_schema = ToolParam({
    "name": "add_duration_to_datetime",
    "description": "Adds a duration to a base datetime and returns the result formatted according to the specified output format.",
    "input_schema": {
        "type": "object",
        "properties": {
            "base_datetime": {
                "type": "string",
                "description": "The base datetime in the format '%Y-%m-%d %H:%M:%S'."
            },
            "duration": {
                "type": "string",
                "description": "The duration to add, specified as a string like '10s', '5m', '2h', '1d' (for seconds, minutes, hours, days)."
            },
            "output_format": {
                "type": "string",
                "description": "A strftime-compatible format string used to format the resulting datetime.",
                "default": "%Y-%m-%d %H:%M:%S"
            }
        },
        "required": ["base_datetime", "duration"]
    }
})


def set_reminder(reminder_time: str, message: str):
    # This is a placeholder implementation. In a real application, you would integrate with a scheduling system.
    __reminders__[reminder_time].append(message)
    return f"Reminder set for {reminder_time} with message: '{message}'"


set_reminder_schema = ToolParam({
    "name": "set_reminder",
    "description": "Sets a reminder for a specific time with a message.",
    "input_schema": {
        "type": "object",
        "properties": {
            "reminder_time": {
                "type": "string",
                "description": "The time to set the reminder for, in the format '%Y-%m-%d %H:%M:%S'."
            },
            "message": {
                "type": "string",
                "description": "The message to be reminded of."
            }
        },
        "required": ["reminder_time", "message"]
    }
})


def get_reminders():
    return json.dumps(__reminders__)

get_reminders_schema = ToolParam({
    "name": "get_reminders",
    "description": "Retrieves all currently set reminders.",
    "input_schema": {
        "type": "object",
        "properties": {}
    }
})
