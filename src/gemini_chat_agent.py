# src/gemini_chat_agent.py
import os
import time
from collections import deque
from typing import Any, Callable, Dict, List, Optional

from google import genai
from google.genai import errors, types

from src.logger import log_message # Import logger


class GeminiChatAgent:
    """
    Encapsulates all direct interaction with the Google Gemini API.
    Handles chat history, tool execution callback, and rate limiting.
    Now supports continuous autonomous operation with user interruption.
    """

    RPM_LIMIT = 15

    def __init__(
        self,
        model_name: str = "gemini-1.5-flash-latest",
        api_key: Optional[str] = None,
        initial_system_prompt: Optional[str] = None,
    ):
        _api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not _api_key:
            raise ValueError(
                "GEMINI_API_KEY must be provided via `api_key` argument or "
                "set as an environment variable."
            )
        self.gemini_client = genai.Client(api_key=_api_key)
        self.model_name = model_name
        self.chat_history: List[types.Content] = []

        if initial_system_prompt:
            self.chat_history.append(
                types.Content(role="user", parts=[types.Part(text=initial_system_prompt)])
            )

        self.request_timestamps = deque()
        self._tool_executor_callback: Optional[Callable[[types.FunctionCall], Any]] = None

    def set_tool_executor_callback(self, callback: Callable[[types.FunctionCall], Any]):
        """
        Sets a callback function that the agent will use to execute tools.
        """
        self._tool_executor_callback = callback

    def _apply_rate_limit(self):
        """
        Applies a rate limit by pausing execution if the RPM_LIMIT is approached.
        """
        current_time = time.time()

        while (
            self.request_timestamps and self.request_timestamps[0] <= current_time - 60
        ):
            self.request_timestamps.popleft()

        if len(self.request_timestamps) >= self.RPM_LIMIT:
            wait_time = self.request_timestamps[0] + 60 - current_time
            if wait_time > 0:
                log_message("RATE_LIMIT", f"Waiting for {wait_time:.2f} seconds...")
                time.sleep(wait_time)
                current_time = time.time()
                while (
                    self.request_timestamps
                    and self.request_timestamps[0] <= current_time - 60
                ):
                    self.request_timestamps.popleft()

        self.request_timestamps.append(time.time())

    def continue_autonomously(self, tools: List[types.Tool], interrupt_message: Optional[str] = None) -> None:
        """
        Causes the Gemini model to continue its internal thought process or action.
        Allows for an optional interrupt message from the user.
        """
        effective_user_message = interrupt_message
        if not effective_user_message:
            effective_user_message = "Your Inner voice says you to proceed."
            log_message("AI_INTERNAL_PROMPT", effective_user_message)
        else:
            log_message("USER", effective_user_message)


        self.chat_history.append(
            types.Content(role="user", parts=[types.Part(text=effective_user_message)])
        )

        generate_content_config = types.GenerateContentConfig(
            tools=tools,
            response_mime_type="text/plain",
        )

        try:
            self._apply_rate_limit()

            stream = self.gemini_client.models.generate_content_stream(
                model=self.model_name,
                contents=self.chat_history,
                config=generate_content_config,
            )

            tool_execution_occurred_in_turn = False
            model_response_parts: List[types.Part] = []

            for chunk in stream:
                if chunk.function_calls:
                    tool_execution_occurred_in_turn = True
                    for fc_item in chunk.function_calls:
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
                        log_message("AI_ACTION", f"Calling tool: {fc_item.name}({fc_item.args})")

                        if self._tool_executor_callback:
                            tool_result_value = self._tool_executor_callback(fc_item)
                        else:
                            tool_result_value = f"Error: Tool executor callback not set for {fc_item.name}."
                            log_message("AI_UNEXPECTED_ERROR", tool_result_value)

                        self.chat_history.append(
                            types.Content(
                                role="user",
                                parts=[types.Part(text=str(tool_result_value))],
                            )
                        )
                        log_message("AI_TOOL_RESULT", tool_result_value)

                        self._apply_rate_limit()
                        follow_up_stream = self.gemini_client.models.generate_content_stream(
                            model=self.model_name,
                            contents=self.chat_history,
                            config=generate_content_config,
                        )
                        for follow_up_chunk in follow_up_stream:
                            if follow_up_chunk.text:
                                log_message("AI_THOUGHT", follow_up_chunk.text, end="")
                                model_response_parts.append(
                                    types.Part(text=follow_up_chunk.text)
                                )
                            elif follow_up_chunk.function_calls:
                                log_message("AI_ACTION", "Chained tool call detected.", symbol="⛓️ ")
                                for next_fc_item in follow_up_chunk.function_calls:
                                    log_message("AI_ACTION", f"Further call: {next_fc_item.name} with {next_fc_item.args}", symbol="🔗 ")
                                    if self._tool_executor_callback:
                                        next_tool_result = self._tool_executor_callback(next_fc_item)
                                        log_message("AI_TOOL_RESULT", next_tool_result, symbol="✅ ")
                                        self.chat_history.append(
                                            types.Content(
                                                role="model",
                                                parts=[types.Part(function_call=types.FunctionCall(name=next_fc_item.name, args=next_fc_item.args))]
                                            )
                                        )
                                        self.chat_history.append(
                                            types.Content(
                                                role="user",
                                                parts=[types.Part(text=str(next_tool_result))]
                                            )
                                        )
                                        self._apply_rate_limit()
                                        final_gen_stream = self.gemini_client.models.generate_content_stream(
                                            model=self.model_name,
                                            contents=self.chat_history,
                                            config=generate_content_config,
                                        )
                                        for final_chunk in final_gen_stream:
                                            if final_chunk.text:
                                                log_message("AI_THOUGHT", final_chunk.text, end="")
                                                model_response_parts.append(types.Part(text=final_chunk.text))
                                        
                        log_message("AI_THOUGHT", "", end="\n") # Ensure newline after stream
                        break

                elif chunk.text:
                    log_message("AI_THOUGHT", chunk.text, end="")
                    model_response_parts.append(types.Part(text=chunk.text))

            log_message("AI_THOUGHT", "", end="\n") # Ensure newline after AI's final text response


            if model_response_parts:
                self.chat_history.append(
                    types.Content(role="model", parts=model_response_parts)
                )

        except errors.ClientError as e:
            log_message("AI_API_ERROR", f"ClientError: {e}")
            if self.chat_history and \
               self.chat_history[-1].role == "user" and \
               self.chat_history[-1].parts and \
               self.chat_history[-1].parts[0].text == effective_user_message:
                self.chat_history.pop()
            time.sleep(5)
        except Exception as e:
            log_message("AI_UNEXPECTED_ERROR", f"Unexpected Error: {e}")
            log_message("AI_UNEXPECTED_ERROR", "Please try again or type an interrupt message.")
            if self.chat_history and \
               self.chat_history[-1].role == "user" and \
               self.chat_history[-1].parts and \
               self.chat_history[-1].parts[0].text == effective_user_message:
                self.chat_history.pop()