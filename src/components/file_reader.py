import os
from src.base_component import BaseComponent

class FileReader(BaseComponent):
    """Reads the content of a specified file."""
    def __init__(self, name: str):
        super().__init__(name)

    def onload(self):
        print(f"FileReader '{self.name}' is now active!")

    def use(self, file_path: str) -> str:
        """
        Reads and returns the content of a file.

        Args:
            file_path: The path to the file to read.

        Returns:
            The content of the file as a string. Returns an error message if the file is not found or inaccessible.
        """
        try:
            with open(file_path, 'r') as file:
                content = file.read()
                print(f"File '{file_path}' content:\n{content}")
                return content
        except FileNotFoundError:
            print(f"Error: File '{file_path}' not found.")
            return f"Error: File '{file_path}' not found."
        except OSError as e:
            print(f"Error accessing '{file_path}': {e}")
            return f"Error accessing '{file_path}': {e}"

    def destroy(self):
        print(f"FileReader '{self.name}' is shutting down.")

