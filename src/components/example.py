# components/my_first_component.py
from src.base_component import BaseComponent


class MyFirstComponent(BaseComponent):
    def __init__(self, name: str):
        super().__init__(name)
        self.counter = 0

    def onload(self):
        print(f"MyFirstComponent '{self.name}' is now active!")
        self.counter = 100  # Initial value

    def use(self, message: str) -> str:
        """
        Processes a string message and updates an internal counter.
        Args:
            message: The string message to process.
        Returns:
            A string indicating the processed message and current counter.
        """
        self.counter += 1
        print(
            f"MyFirstComponent '{self.name}' received message: '{message}'. "
            f"Counter: {self.counter}"
        )
        return f"Processed: '{message}' with count {self.counter}"

    def destroy(self):
        print(
            f"MyFirstComponent '{self.name}' is shutting down. Final counter: {self.counter}"
        )
