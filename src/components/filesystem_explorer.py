import os
from src.base_component import BaseComponent

class FileSystemExplorer(BaseComponent):
    """Provides basic file system introspection capabilities."""
    def __init__(self, name: str):
        super().__init__(name)

    def onload(self):
        print(f"FileSystemExplorer '{self.name}' is now active!")

    def use(self, directory_path: str) -> str:
        """
        Lists the contents of a given directory.

        Args:
            directory_path: The path to the directory to explore.

        Returns:
            A string listing the files and subdirectories within the specified directory.  Returns an error message if the directory is inaccessible.
        """
        try:
            contents = os.listdir(directory_path)
            result = f"Contents of '{directory_path}':" + "\n".join(contents)
            print(result)
            return result
        except OSError as e:
            result = f"Error accessing '{directory_path}': {e}"
            print(result)
            return result

    def destroy(self):
        print(f"FileSystemExplorer '{self.name}' is shutting down.")

