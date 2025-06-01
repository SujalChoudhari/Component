# src/logger.py
import sys

from src.colors import (
    BOLD,
    BRIGHT_BLACK,
    BRIGHT_BLUE,
    BRIGHT_CYAN,
    BRIGHT_RED,
    BRIGHT_YELLOW,
    CYAN,
    GREEN,
    MAGENTA,
    RED,
    RESET,
    WHITE,
    YELLOW,
)


def log_message(
    level: str,
    message: str,
    color: str = WHITE,
    symbol: str = "",
    end: str = "\n",
):
    """
    Custom logger function for color-coded, concise output.

    Args:
        level (str): The type of log (e.g., "USER", "AI", "ACTION", "SYSTEM", "WARNING", "ERROR").
        message (str): The message content.
        color (str): ANSI color code from src.colors.
        symbol (str): A symbol to prepend to the message.
        end (str): What to append after the message (defaults to newline).
    """
    # Define prefixes and colors based on level for less verbosity
    level_map = {
        "USER": (BRIGHT_BLUE, "👤 "),
        "AI_INTERNAL_PROMPT": (BRIGHT_CYAN, "💭 "),
        "AI_THOUGHT": (CYAN, "💡 "),
        "AI_ACTION": (MAGENTA, "🚀 "),
        "AI_TOOL_RESULT": (GREEN, "✅ "),
        "AI_API_ERROR": (BRIGHT_RED, "❌ "),
        "AI_UNEXPECTED_ERROR": (RED, "💥 "),
        "SYSTEM_INIT": (BOLD + GREEN, "✨ "),
        "SYSTEM_RELOAD": (BOLD + YELLOW, "🔄 "),
        "SYSTEM_TOOL_BUILD": (YELLOW, "🛠️ "),
        "SYSTEM_EXIT": (BRIGHT_BLACK, "👋 "),
        "RATE_LIMIT": (BRIGHT_YELLOW, "⏳ "),
        "WARNING": (YELLOW, "⚠️ "),
    }

    lvl_color, lvl_symbol = level_map.get(level, (color, symbol))

    # Construct the log string
    log_string = f"{lvl_color}{lvl_symbol}{message}{RESET}"

    # Use sys.stdout.write for finer control, especially with `end=""`
    sys.stdout.write(log_string + end)
    sys.stdout.flush()  # Ensure output is immediately visible
