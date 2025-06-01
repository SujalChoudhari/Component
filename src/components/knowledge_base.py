from typing import Union
from src.base_component import BaseComponent


class KnowledgeBase(BaseComponent):
    """Provides an in-memory knowledge base for storing and retrieving data."""

    def __init__(self, name: str):
        super().__init__(name)
        self.data = {}

    def onload(self):
        print(f"KnowledgeBase '{self.name}' is now active!")

    def use(
        self, action: str, key: str = "", value=None
    ) -> Union[dict, str, None, bool, list]:
        """Performs actions on the knowledge base.

        Args:
            action (str): The action to perform. Can be 'add', 'get', 'update', 'delete', or 'list'.
            key (str, optional): The key for accessing data. Required for actions 'get', 'update', and 'delete'.
            value (any, optional): The value to add or update. Required for actions 'add' and 'update'.

        Returns:
            Union[dict, str, None]: The result of the action.  Returns the retrieved value for 'get', a dictionary of keys for 'list', True/False for 'add' and 'delete' and None otherwise.
        """
        if action == "add":
            if key is not None and value is not None:
                self.data[key] = value
                return True
            else:
                return "Error: 'add' requires both 'key' and 'value'"
        elif action == "get":
            if key is not None:
                return self.data.get(key)
            else:
                return "Error: 'get' requires a 'key'"
        elif action == "update":
            if key is not None and value is not None:
                self.data[key] = value
                return True
            else:
                return "Error: 'update' requires both 'key' and 'value'"
        elif action == "delete":
            if key is not None:
                if key in self.data:
                    del self.data[key]
                    return True
                else:
                    return False
            else:
                return "Error: 'delete' requires a 'key'"
        elif action == "list":
            return list(self.data.keys())
        else:
            return "Error: Invalid action.  Use 'add', 'get', 'update', 'delete', or 'list'."

    def destroy(self):
        print(f"KnowledgeBase '{self.name}' is shutting down.")
