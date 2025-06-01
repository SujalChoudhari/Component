# ai_manager.py
import inspect
import os
import time  # Import the time module
from collections import deque  # For an efficient queue
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import (
    errors,  # Import errors module for ClientError (for potential rate limit errors)
    types,
)

from src.base_component import BaseComponent
from src.manager import ComponentManager


class AIComponentManager:
    """
    Manages AI interaction, converting loaded components into Gemini tools,
    and handling tool calls based on Gemini's responses.
    This version uses the `google-genai` library and includes rate limiting.
    """

    # Define rate limits
    RPM_LIMIT = 15  # Requests Per Minute
    # We'll use a window of 60 seconds. Max requests within this window.

    def __init__(
        self,
        components_dir: str = "components",
        model_name: str = "gemini-1.5-flash-latest",
        api_key: Optional[str] = None,
    ):
        self.component_manager = ComponentManager(components_dir)
        self.component_manager.load_all_components()

        self.model_name = model_name

        _api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not _api_key:
            raise ValueError(
                "GEMINI_API_KEY must be provided via `api_key` argument or "
                "set as an environment variable."
            )
        self.gemini_client = genai.Client(api_key=_api_key)

        self.available_tools: List[types.Tool] = self._build_gemini_tools()
        self.chat_history: List[types.Content] = []

        # Rate limiting variables
        # Stores timestamps of the last RPM_LIMIT requests
        self.request_timestamps = deque()

        print(f"\nAI Component Manager initialized with model: {self.model_name}")
        print(f"Rate limit set to {self.RPM_LIMIT} requests per minute.")

    def _apply_rate_limit(self):
        """
        Applies a rate limit by pausing execution if the RPM_LIMIT is approached.
        """
        current_time = time.time()

        # Remove timestamps older than 60 seconds
        while (
            self.request_timestamps and self.request_timestamps[0] <= current_time - 60
        ):
            self.request_timestamps.popleft()

        # Check if we are at the limit
        if len(self.request_timestamps) >= self.RPM_LIMIT:
            # Calculate time to wait until the oldest request in the window expires
            wait_time = self.request_timestamps[0] + 60 - current_time
            if wait_time > 0:
                print(f"Rate limit hit. Waiting for {wait_time:.2f} seconds...")
                time.sleep(wait_time)
                # After waiting, clear expired timestamps again
                current_time = time.time()
                while (
                    self.request_timestamps
                    and self.request_timestamps[0] <= current_time - 60
                ):
                    self.request_timestamps.popleft()

        # Add the current request's timestamp
        self.request_timestamps.append(time.time())

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
            print(
                f"Warning: Component '{component_name}' does not have a usable 'use' method."
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
        for name, component in self.component_manager.loaded_components.items():
            tool_declaration = self._component_to_tool_declaration(name, component)
            if tool_declaration:
                tools_list.append(tool_declaration)
        print(f"\nBuilt {len(tools_list)} tools for Gemini.")
        for tool_spec in tools_list:
            for fd in tool_spec.function_declarations:
                print(
                    f"  - Tool: {fd.name} (Parameters: {list(fd.parameters.properties.keys())})"
                )
        return tools_list

    def _call_tool(self, function_call: types.FunctionCall) -> Any:
        """
        Calls the appropriate component's 'use' method based on Gemini's function call.
        """
        tool_name = function_call.name
        tool_args = function_call.args

        print(f"\nAI requested tool call: {tool_name} with arguments: {tool_args}")

        component = self.component_manager.get_component(tool_name)
        if not component:
            return f"Error: Component '{tool_name}' not found."

        try:
            result = component.use(**tool_args)
            print(f"Tool '{tool_name}' returned: {result}")
            return result
        except Exception as e:
            error_message = f"Error executing tool '{tool_name}': {e}"
            print(error_message)
            return error_message

    def start_chat_interface(self):
        """
        Starts a CLI-based chat interface with the Gemini model and component tools.
        """
        print("\n--- Starting AI Component Manager Chat ---")
        print("Type 'exit' or 'quit' to end the session.")

        generate_content_config = types.GenerateContentConfig(
            tools=self.available_tools,
            response_mime_type="text/plain",
        )

        while True:
            user_input = input("\n[You]: ")
            if user_input.lower() in ["exit", "quit"]:
                print("Exiting chat. Goodbye!")
                break

            self.chat_history.append(
                types.Content(role="user", parts=[types.Part(text=user_input)])
            )

            try:
                # Apply rate limit before making a request to the model
                self._apply_rate_limit()

                # Send the entire chat history for context
                stream = self.gemini_client.models.generate_content_stream(
                    model=self.model_name,
                    contents=self.chat_history,
                    config=generate_content_config,
                )

                tool_execution_needed = False
                for chunk in stream:
                    if chunk.function_calls:
                        tool_execution_needed = True
                        for fc_item in chunk.function_calls:
                            # Add the model's function call part to history
                            self.chat_history.append(
                                types.Content(
                                    role="model",
                                    parts=[
                                        types.Part(
                                            function_call=types.FunctionCall(
                                                name=fc_item.name, args=fc_item.args
                                            )
                                        )
                                    ],
                                )
                            )
                            tool_result_value = self._call_tool(fc_item)
                            # Add the function's response part to history
                            self.chat_history.append(
                                types.Content(
                                    role="function",
                                    parts=[types.Part(text=str(tool_result_value))],
                                )
                            )

                            print(f"\nSending tool output to AI: {tool_result_value}")

                            # Apply rate limit before the follow-up request
                            self._apply_rate_limit()

                            # Continue the conversation with the updated history
                            follow_up_stream = (
                                self.gemini_client.models.generate_content_stream(
                                    model=self.model_name,
                                    contents=self.chat_history,
                                    config=generate_content_config,
                                )
                            )
                            final_ai_response_parts: List[types.Part] = []
                            for follow_up_chunk in follow_up_stream:
                                if follow_up_chunk.text:
                                    print(f"[AI]: {follow_up_chunk.text}", end="")
                                    final_ai_response_parts.append(
                                        types.Part(text=follow_up_chunk.text)
                                    )
                                elif follow_up_chunk.function_calls:
                                    print(
                                        f"\n[AI]: Gemini requested another tool call in response to tool output."
                                    )
                                    # For simplicity, we just print here. A real app might re-enter the tool loop.
                                    for next_fc_item in follow_up_chunk.function_calls:
                                        print(
                                            f"  (Further call: {next_fc_item.name} with {next_fc_item.args})"
                                        )
                                    # If a chain of calls is expected, this inner loop structure
                                    # would need a more sophisticated recursive or iterative approach.
                                    # For this example, we assume at most one follow-up tool call after a response.
                            print()
                            if final_ai_response_parts:
                                self.chat_history.append(
                                    types.Content(
                                        role="model", parts=final_ai_response_parts
                                    )
                                )
                        break  # Break from outer chunk loop after handling tool call and follow-up

                    elif chunk.text:
                        print(f"[AI]: {chunk.text}", end="")
                        # Append text to history only if it's not part of a tool call chain
                        # For simple text responses, we append it directly
                        self.chat_history.append(
                            types.Content(
                                role="model", parts=[types.Part(text=chunk.text)]
                            )
                        )
                print()  # Ensure a newline after the AI's initial text response

            except (
                errors.ClientError
            ) as e:  # Catch ClientError for API issues including rate limits
                # Gemini API often returns 429 (Too Many Requests) for rate limits.
                # However, this also catches other ClientErrors.
                print(f"[AI]: API Error (ClientError): {e}")
                # Attempt to remove the last user message and its immediate model response if error occurred
                if self.chat_history and self.chat_history[-1].role == "user":
                    self.chat_history.pop()  # Remove the user's message
                # If the error was a rate limit, the _apply_rate_limit should prevent it
                # but if an error slips through, this is a catch-all.
                time.sleep(
                    5
                )  # A small pause to prevent rapid re-attempts on generic errors
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                print("Please try again.")
                if self.chat_history and self.chat_history[-1].role == "user":
                    self.chat_history.pop()


# --- main.py remains the same ---
if __name__ == "__main__":
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print(
                "GEMINI_API_KEY environment variable not set. Please set it or hardcode in ai_manager.py for testing."
            )
            # DO NOT HARDCODE API KEY IN PRODUCTION CODE
            # For testing, you could uncomment the line below, but it's not recommended.
            # api_key = "YOUR_GEMINI_API_KEY_HERE"

        ai_manager = AIComponentManager(components_dir="components", api_key=api_key)
        ai_manager.start_chat_interface()
    except ValueError as e:
        print(f"Initialization error: {e}")
        print("Please ensure GEMINI_API_KEY is correctly set or passed.")
