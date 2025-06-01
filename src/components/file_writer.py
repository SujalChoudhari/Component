from src.base_component import BaseComponent

class FileWriterComponent(BaseComponent):
    """Writes data to a specified file."""

    def __init__(self, name: str):
        super().__init__(name)

    def onload(self):
        print(f"FileWriterComponent '{self.name}' is now active!")

    def use(self, file_path: str, content: str, mode: str = "a") -> str:
        """Writes content to a file.

        Args:
            file_path: The path to the file.
            content: The content to write.
            mode: The file open mode ("w" for write, "a" for append, etc.). Defaults to append.

        Returns:
            A message indicating success or failure.
        """
        try:
            with open(file_path, mode) as f:
                f.write(content)
            return f"Successfully wrote content to '{file_path}'"
        except Exception as e:
            return f"Error writing to file: {e}"

    def destroy(self):
        print(f"FileWriterComponent '{self.name}' is shutting down.")
