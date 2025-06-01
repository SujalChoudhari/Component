# src/manager.py
import importlib.util
import inspect
import os
import sys
from typing import Any, Dict, Optional, Type

from src.base_component import BaseComponent
from src.logger import log_message


class ComponentManager:
    """
    Manages the loading, lifecycle, and access of components.
    """

    def __init__(self, components_dir: str = "components"):
        self.components_dir = components_dir
        self._loaded_components: Dict[str, BaseComponent] = {}
        self._available_component_classes: Dict[str, Type[BaseComponent]] = {}

    def refresh_components(self):
        """
        Clears existing loaded/available components, re-scans the directory,
        and re-imports all modules, making them available. This also handles
        unloading modules from sys.modules to ensure fresh code is loaded.
        """
        self.unload_all_components()

        # Clear existing available component classes
        self._available_component_classes = {}

        # Reset sys.modules for affected component modules to force reload
        # This is crucial for picking up modifications to existing files.
        for filename in os.listdir(self.components_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                module_name = filename[:-3]
                if module_name in sys.modules:
                    log_message("SYSTEM_RELOAD", f"Unloading module from sys.modules: {module_name}")
                    del sys.modules[module_name]

        self._auto_import_components()

    def _auto_import_components(self):
        """
        Scans the `components_dir` for Python files, imports them,
        and identifies `BaseComponent` subclasses.
        """
        if not os.path.isdir(self.components_dir):
            log_message("WARNING", f"Components directory '{self.components_dir}' not found. No components will be loaded.")
            return

        # Add components dir to sys.path temporarily for module discovery
        sys.path.insert(0, self.components_dir)

        for filename in os.listdir(self.components_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                module_name = filename[:-3]
                file_path = os.path.join(self.components_dir, filename)

                try:
                    spec = importlib.util.spec_from_file_location(
                        module_name, file_path
                    )
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        sys.modules[module_name] = module
                        spec.loader.exec_module(module)
                        self._discover_component_classes(module)
                        log_message("SYSTEM_RELOAD", f"Imported module: {module_name}")
                    else:
                        log_message("WARNING", f"Could not load spec for module: {module_name}")
                except Exception as e:
                    log_message("AI_UNEXPECTED_ERROR", f"Error importing module {module_name}: {e}")

        sys.path.pop(0)

    def _discover_component_classes(self, module):
        """
        Discovers subclasses of BaseComponent within an imported module.
        """
        for name, obj in inspect.getmembers(module):
            if (
                inspect.isclass(obj)
                and issubclass(obj, BaseComponent)
                and obj is not BaseComponent
            ):
                component_name = obj.__name__
                if component_name in self._available_component_classes:
                    log_message("WARNING",
                        f"Duplicate component class name '{component_name}' found in {module.__name__}. Skipping."
                    )
                else:
                    self._available_component_classes[component_name] = obj
                    log_message("SYSTEM_RELOAD", f"Discovered component class: {component_name}")

    def load_component(self, component_class_name: str) -> Optional[BaseComponent]:
        """
        Loads and initializes a component by its class name.
        Calls the `onload` method of the component.
        """
        if component_class_name in self._loaded_components:
            log_message("SYSTEM_RELOAD", f"Component '{component_class_name}' is already loaded.")
            return self._loaded_components[component_class_name]

        component_class = self._available_component_classes.get(component_class_name)
        if not component_class:
            log_message("AI_UNEXPECTED_ERROR", f"Component class '{component_class_name}' not found.")
            return None

        try:
            component_instance = component_class(component_class_name)
            component_instance.onload()
            self._loaded_components[component_class_name] = component_instance
            log_message("SYSTEM_RELOAD", f"Component '{component_class_name}' loaded successfully.")
            return component_instance
        except Exception as e:
            log_message("AI_UNEXPECTED_ERROR", f"Error loading component '{component_class_name}': {e}")
            return None

    def load_all_components(self):
        """
        Loads and initializes all discovered component classes.
        """
        log_message("SYSTEM_RELOAD", "Attempting to load all available components...")
        if not self._available_component_classes:
            log_message("SYSTEM_RELOAD", "No component classes discovered to load.")
            return

        for component_class_name in list(self._available_component_classes.keys()):
            # Only load if not already loaded (useful if refresh was not complete or state needs checking)
            if component_class_name not in self._loaded_components:
                self.load_component(
                    component_class_name
                )
            else:
                log_message("SYSTEM_RELOAD", f"Component '{component_class_name}' already instantiated. Skipping.")


    def get_component(self, name: str) -> Optional[BaseComponent]:
        """
        Retrieves a loaded component by its name.
        """
        return self._loaded_components.get(name)

    def use_component(self, name: str, *args: Any, **kwargs: Any) -> Any:
        """
        Retrieves a loaded component by its name and calls its 'use' method
        with the provided arguments.
        """
        component = self._loaded_components.get(name)
        if component:
            try:
                log_message("AI_ACTION", f"Attempting to use component '{name}'...")
                return component.use(*args, **kwargs)
            except Exception as e:
                log_message("AI_UNEXPECTED_ERROR", f"Error using component '{name}': {e}")
                return None
        else:
            log_message("AI_UNEXPECTED_ERROR", f"Component '{name}' not found or not loaded.")
            return None

    def unload_component(self, name: str):
        """
        Unloads a component by its name.
        Calls the `destroy` method of the component.
        """
        component = self._loaded_components.pop(name, None)
        if component:
            try:
                component.destroy()
                log_message("SYSTEM_RELOAD", f"Component '{name}' unloaded successfully.")
            except Exception as e:
                log_message("AI_UNEXPECTED_ERROR", f"Error destroying component '{name}': {e}")
        else:
            log_message("SYSTEM_RELOAD", f"Component '{name}' not found or not loaded.")

    def unload_all_components(self):
        """
        Unloads all currently loaded components.
        """
        log_message("SYSTEM_RELOAD", "Attempting to unload all loaded components...")
        if not self._loaded_components:
            log_message("SYSTEM_RELOAD", "No components currently loaded to unload.")
            return

        # Iterate over a copy of keys to avoid RuntimeError due to dictionary size change during iteration
        for component_name in list(self._loaded_components.keys()):
            self.unload_component(component_name)

    @property
    def loaded_components(self) -> Dict[str, BaseComponent]:
        """
        Returns a dictionary of currently loaded components.
        """
        return self._loaded_components

    def list_available_components(self):
        """
        Lists all discovered component classes.
        """
        log_message("SYSTEM_TOOL_BUILD", "Available Component Classes:")
        if not self._available_component_classes:
            log_message("SYSTEM_TOOL_BUILD", "  No component classes found.")
            return
        for name in self._available_component_classes:
            log_message("SYSTEM_TOOL_BUILD", f"  - {name}")

    def list_loaded_components(self):
        """
        Lists all currently loaded components.
        """
        log_message("SYSTEM_TOOL_BUILD", "Loaded Components:")
        if not self._loaded_components:
            log_message("SYSTEM_TOOL_BUILD", "  No components currently loaded.")
            return
        for name, component in self._loaded_components.items():
            log_message("SYSTEM_TOOL_BUILD", f"  - {name} ({component.__class__.__name__})")