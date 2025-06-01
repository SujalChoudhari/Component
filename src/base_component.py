# src/base_component.py
import abc


class BaseComponent(abc.ABC):
    """
    Abstract base class for all components.
    Defines the required methods for a component.
    """

    def __init__(self, name: str):
        self._name = name
        # print(f"Component '{self.name}' initialized.") # Commented for less noise

    @property
    def name(self) -> str:
        return self._name

    @abc.abstractmethod
    def onload(self):
        """
        Method called when the component is loaded by the manager.
        Use this for initial setup.
        """
        pass

    @abc.abstractmethod
    def use(self, *args, **kwargs):
        """
        Method for the primary functionality of the component.
        """
        pass

    @abc.abstractmethod
    def destroy(self):
        """
        Method called when the component is unloaded/destroyed by the manager.
        Use this for cleanup.
        """
        pass

    def __repr__(self) -> str:
        return f"<Component: {self.name}>"
