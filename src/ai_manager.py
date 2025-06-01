# src/ai_manager.py
import inspect
import os
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types

from src.base_component import BaseComponent
from src.manager import ComponentManager
from src.gemini_chat_agent import GeminiChatAgent
from src.logger import log_message


class AIComponentManager:
    """
    Manages AI interaction, converting loaded components into Gemini tools,
    and handling tool calls based on Gemini's responses.
    This version orchestrates between ComponentManager and GeminiChatAgent
    for autonomous operation with user interruption.
    """

    def __init__(
        self,
        components_dir: str = "components",
        model_name: str = "gemini-1.5-flash-latest",
        api_key: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ):
        self.components_dir = components_dir
        # Initialize ComponentManager here; its refresh_components will handle initial load
        self.component_manager = ComponentManager(self.components_dir)
        self.model_name = model_name

        self.available_tools: List[types.Tool] = [] # Will be built after components are loaded

        self.gemini_agent = GeminiChatAgent(
            model_name=self.model_name,
            api_key=api_key,
            initial_system_prompt=system_prompt,
        )
        self.gemini_agent.set_tool_executor_callback(self._call_tool)

        log_message("SYSTEM_INIT", f"AI Component Manager initialized for autonomous operation.")

    def _reload_components_and_tools(self):
        """
        Reloads all components from the components directory and rebuilds
        the list of available Gemini tools.
        """
        log_message("SYSTEM_RELOAD", "Reloading components and rebuilding tools...")
        # Tell the existing component_manager instance to refresh its components
        self.component_manager.refresh_components()
        self.component_manager.load_all_components()

        # Rebuild tools list from the newly loaded components
        self.available_tools = self._build_gemini_tools()
        log_message("SYSTEM_RELOAD", "Components and tools reloaded.")


    def _get_gemini_type(self, python_type: Any) -> types.Schema:
        """Converts Python types to Gemini's schema types."""
        if python_type is inspect.Parameter.empty or python_type is str:
            return types.Schema(type="string")
        if python_type is int or python_type is float:
            return types.Schema(type="number")
        if python_type is bool:
            return types.Schema(type="boolean")
        return types.Schema(type="string")

    def _component_to_tool_declaration(
        self, component_name: str, component_instance: BaseComponent
    ) -> Optional[types.Tool]:
        """
        Converts a component's 'use' method into a Gemini FunctionDeclaration.
        """
        method = getattr(component_instance, "use", None)
        if not method or not inspect.ismethod(method):
            log_message("WARNING",
                f"Component '{component_name}' does not have a usable 'use' method."
            )
            return None

        sig = inspect.signature(method)
        parameters_properties = {}
        required_params = []

        for name, param in list(sig.parameters.items()):
            if name == "self":
                continue

            param_schema = self._get_gemini_type(param.annotation)

            if param.default is inspect.Parameter.empty:
                required_params.append(name)

            parameters_properties[name] = param_schema

        description = inspect.getdoc(method) or f"Uses the {component_name} component."
        function_name = component_name

        parameters_schema = types.Schema(
            type="object",
            properties=parameters_properties,
            required=required_params,
        )

        function_declaration = types.FunctionDeclaration(
            name=function_name,
            description=description,
            parameters=parameters_schema,
        )

        return types.Tool(function_declarations=[function_declaration])

    def _build_gemini_tools(self) -> List[types.Tool]:
        """
        Builds a list of Gemini tools from all loaded components.
        """
        tools_list: List[types.Tool] = []
        if not self.component_manager: # Should not happen now that it's initialized in __init__
            log_message("WARNING", "ComponentManager not yet initialized. Cannot build tools.")
            return []

        for name, component in self.component_manager.loaded_components.items():
            tool_declaration = self._component_to_tool_declaration(name, component)
            if tool_declaration:
                tools_list.append(tool_declaration)
        log_message("SYSTEM_TOOL_BUILD", f"Built {len(tools_list)} tools for Gemini.")
        for tool_spec in tools_list:
            for fd in tool_spec.function_declarations:
                log_message("SYSTEM_TOOL_BUILD",
                    f"  - Tool: {fd.name} (Parameters: {list(fd.parameters.properties.keys())})"
                )
        return tools_list

    def _call_tool(self, function_call: types.FunctionCall) -> Any:
        """
        Calls the appropriate component's 'use' method based on Gemini's function call.
        This method is now a callback for GeminiChatAgent.
        """
        tool_name = function_call.name
        tool_args = function_call.args

        log_message("AI_ACTION", f"Executing {tool_name} with args: {tool_args}")

        component = self.component_manager.get_component(tool_name)
        if not component:
            return f"Error: Component '{tool_name}' not found."

        try:
            result = component.use(**tool_args)
            log_message("AI_TOOL_RESULT", f"Tool '{tool_name}' returned: {result}")
            return result
        except Exception as e:
            error_message = f"Error executing tool '{tool_name}': {e}"
            log_message("AI_UNEXPECTED_ERROR", error_message)
            return error_message

    def start_autonomous_loop(self):
        """
        Starts the continuous autonomous loop for the AI.
        Allows user to provide guidance or simply press Enter to continue.
        """
        log_message("SYSTEM_INIT", "--- Starting AI Autonomous Loop ---")
        log_message("SYSTEM_INIT", "AI will continuously generate thoughts/actions to achieve its goal.")
        log_message("SYSTEM_INIT", "Press Enter to let the AI continue, or type a message to interrupt/guide it.")
        log_message("SYSTEM_INIT", "Type 'exit' or 'quit' to end the session.")

        # Perform initial component load and tool building
        self._reload_components_and_tools()

        while True:
            user_input = input("\n[User (Press Enter to continue, or type a message)]:\n> ")

            if user_input.lower() in ["exit", "quit"]:
                log_message("SYSTEM_EXIT", "Exiting autonomous loop. Goodbye!")
                break
            
            # BEFORE each AI turn, reload components to reflect any changes made by CodeWriterComponent
            self._reload_components_and_tools()

            # Pass the interrupt message (or internal prompt) and the LATEST tools list
            self.gemini_agent.continue_autonomously(
                tools=self.available_tools, # Pass the newly built tools
                interrupt_message= f"Some hidden voice says: {user_input}" if user_input else "proceed"
            )