# src/components/code_writer_component.py
import os

from src.base_component import BaseComponent


class CodeWriterComponent(BaseComponent):
    """
    Allows the AI to write new Python code files (components)
    into the 'src/components/' directory.
    """

    def __init__(self, name: str):
        super().__init__(name)
        # Define the target directory for new components.
        # This path should be relative to where your main script is run.
        # Assuming components are sibling to src, and the target is src/components
        # Adjust this path based on your exact project structure if needed.
        self.target_component_dir = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),  # current file's directory (src/components)
                "..",  # go up one level (to src)
            )
        )
        # To be extra clear, ensure the target is "src/components" relative to root
        # if ai_manager or main.py are in the root.
        # For our current structure: your_project/src/components
        self.target_component_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
        )

    def onload(self):
        print(
            f"CodeWriterComponent '{self.name}' is ready to write new component files to: {self.target_component_dir}"
        )

    def use(self, file_name: str, code_content: str) -> str:
        """
        Writes the given Python code content to a new file in the components directory.

        Args:
            file_name (str): The name of the Python file to create (e.g., "my_new_tool.py").
                             Must end with '.py'.
            code_content (str): The complete Python code for the new component.
                                This should be a valid BaseComponent subclass.

        Returns:
            str: A message indicating success or failure.


      
        """
        if not file_name.endswith(".py"):
            return f"Error: File name '{file_name}' must end with '.py'."

        file_path = os.path.join(self.target_component_dir, file_name)

        if os.path.exists(file_path):
            return f"Error: File '{file_name}' already exists. Please choose a different name or modify existing file manually."

        try:
            with open(file_path, "w") as f:
                f.write(code_content)
            print(f"Successfully wrote new component to: {file_path}")
            return f"Success: Component '{file_name}' created. It will be loaded on manager restart."
        except Exception as e:
            error_msg = f"Error writing component '{file_name}': {e}"
            print(error_msg)
            return (
                f"Error: Failed to create component '{file_name}'. Details: {error_msg}"
            )

    def destroy(self):
        print(f"CodeWriterComponent '{self.name}' destroyed.")
