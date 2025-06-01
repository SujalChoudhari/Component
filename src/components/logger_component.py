# components/logger_component.py
from src.base_component import BaseComponent


class LoggerComponent(BaseComponent):
    def __init__(self, name: str):
        super().__init__(name)
        self.log_messages = []

    def onload(self):
        print(f"LoggerComponent '{self.name}' ready to log.")

    def use(self, message: str, level: str = "INFO") -> str:
        """
        Logs a message with a specified level.
        Args:
            message: The message string to log.
            level: The logging level (e.g., "INFO", "WARNING", "ERROR"). Defaults to "INFO".
        Returns:
            A string indicating what was logged.
        """
        log_entry = f"[{level}] {message}"
        self.log_messages.append(log_entry)
        print(f"Logged: {log_entry}")
        return f"Successfully logged: {log_entry}"

    def destroy(self):
        print(
            f"LoggerComponent '{self.name}' destroying. All logs: {self.log_messages}"
        )
        self.log_messages = []
