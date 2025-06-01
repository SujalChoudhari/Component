
import subprocess
from src.base_component import BaseComponent
import shlex

class ShellCommandExecutor(BaseComponent):
    """Executes shell commands and returns the output."""

    def __init__(self, name: str):
        super().__init__(name)

    def onload(self):
        print(f"ShellCommandExecutor '{self.name}' is now active!")

    def use(self, command: str) -> str:
        """Executes a shell command and returns the output.

        Args:
            command: The shell command to execute.

        Returns:
            The output of the command as a string, or an error message if the command fails.
        """
        try:
            #Use shlex.split for safer command execution to handle spaces and special characters in arguments.
            process = subprocess.run(shlex.split(command), capture_output=True, text=True, check=True)
            return process.stdout
        except subprocess.CalledProcessError as e:
            return f"Error executing command: {e}"
        except FileNotFoundError:
            return "Error: Command not found."
        except Exception as e:
            return f"An unexpected error occurred: {e}"


    def destroy(self):
        print(f"ShellCommandExecutor '{self.name}' is shutting down.")

