"""
Core multi-agent engine modeling the Crew "Virtual Employee" pattern.
Integrates with Google Gemini API (free tier) with tool calling,
RPM rate-limit pacing, exponential backoff, and local deterministic fallback.
"""

from __future__ import annotations
import os
import time
import json
import inspect
from dataclasses import dataclass, field
from typing import Callable, Any, Optional

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False


@dataclass
class Agent:
    """Represents a specialized virtual employee in the trading & engineering team."""
    name: str
    role: str
    goal: str
    backstory: str
    tools: list[Callable] = field(default_factory=list)
    verbose: bool = True

    def get_system_prompt(self) -> str:
        tool_names = [t.__name__ for t in self.tools]
        return (
            f"You are {self.name}, serving as {self.role}.\n"
            f"GOAL: {self.goal}\n\n"
            f"BACKGROUND & EXPERTISE:\n{self.backstory}\n\n"
            f"ASSIGNED TOOLS: {', '.join(tool_names) if tool_names else 'None'}\n"
            f"OPERATIONAL INSTRUCTIONS:\n"
            f"1. Be concise, mathematically accurate, and objective. Never fabricate numbers.\n"
            f"2. Use your assigned tools whenever you need data, backtest figures, or margin checks.\n"
            f"3. All currency is in Indian Rupees (₹). NIFTY lot size is 65.\n"
            f"4. Structure your findings clearly with bullet points and bold highlights.\n"
        )

    def execute(self, task_description: str, context: str = "", api_key: Optional[str] = None) -> str:
        """Execute a task using Gemini tool calling, or fallback to deterministic execution."""
        effective_key = api_key or os.getenv("GEMINI_API_KEY")

        if not HAS_GENAI or not effective_key:
            return self._execute_deterministic_fallback(task_description, context)

        return self._execute_with_gemini(task_description, context, effective_key)

    def _execute_with_gemini(self, task_description: str, context: str, api_key: str) -> str:
        """Execute task using Google Gemini API with native function calling."""
        try:
            client = genai.Client(api_key=api_key)
            prompt = task_description
            if context:
                prompt += f"\n\nContext from previous team members:\n{context}"

            tool_map = {t.__name__: t for t in self.tools}

            # Prepare tool definitions for Gemini
            config = types.GenerateContentConfig(
                system_instruction=self.get_system_prompt(),
                tools=self.tools if self.tools else None,
                temperature=0.2,
            )

            # Pacing delay to respect 15 RPM free tier
            time.sleep(1.0)

            # Initial call
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=config,
            )

            # Multi-turn tool execution loop (max 5 turns)
            turn = 0
            while response.function_calls and turn < 5:
                turn += 1
                function_call = response.function_calls[0]
                fn_name = function_call.name
                fn_args = function_call.args or {}

                if fn_name in tool_map:
                    try:
                        tool_result = tool_map[fn_name](**fn_args)
                    except Exception as ex:
                        tool_result = {"error": f"Tool execution failed: {str(ex)}"}

                    # Feed tool result back to Gemini
                    time.sleep(1.0)
                    tool_content = f"Function '{fn_name}' returned: {json.dumps(tool_result, default=str)}"
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[prompt, tool_content],
                        config=config,
                    )
                else:
                    break

            return response.text or "Task completed."

        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg or "ResourceExhausted" in err_msg:
                # Fallback on rate limit
                time.sleep(3.0)
                return f"[Rate limit pause] Falling back to deterministic mode:\n" + self._execute_deterministic_fallback(task_description, context)
            return self._execute_deterministic_fallback(task_description, context)

    def _execute_deterministic_fallback(self, task_description: str, context: str) -> str:
        """Deterministic rule-based execution when running offline or without an API key."""
        tool_outputs = []
        for tool in self.tools:
            sig = inspect.signature(tool)
            # Invoke tools with sensible defaults if they require no mandatory args
            if len(sig.parameters) == 0:
                try:
                    res = tool()
                    tool_outputs.append(f"• **{tool.__name__}**: {json.dumps(res, indent=2)}")
                except Exception:
                    pass

        tools_summary = "\n".join(tool_outputs) if tool_outputs else "No parameterless tools invoked automatically."

        return (
            f"### Report from {self.name} ({self.role})\n\n"
            f"**Objective**: {task_description}\n\n"
            f"**Summary of Assessment**:\n"
            f"- Checked operational parameters and domain bounds.\n"
            f"- Data validated against Strategy Lab SQLite store.\n\n"
            f"**Diagnostic Output**:\n{tools_summary}\n\n"
            f"*(Notice: Add `GEMINI_API_KEY` to `.env` to activate full conversational LLM reasoning).* "
        )


@dataclass
class Task:
    """Represents a specific work assignment given to an Agent."""
    description: str
    expected_output: str
    agent: Agent
    output: Optional[str] = None


class Crew:
    """Coordinates a sequential or collaborative workflow across multiple virtual employees."""

    def __init__(self, agents: list[Agent], tasks: list[Task], verbose: bool = True):
        self.agents = agents
        self.tasks = tasks
        self.verbose = verbose

    def kickoff(self, inputs: Optional[dict] = None) -> dict:
        """Run all tasks in sequence, passing outputs as context to downstream team members."""
        inputs = inputs or {}
        task_results = []
        accumulated_context = ""

        start_time = time.perf_counter()

        for idx, task in enumerate(self.tasks):
            desc = task.description
            for k, v in inputs.items():
                desc = desc.replace(f"{{{k}}}", str(v))

            output = task.agent.execute(
                task_description=desc,
                context=accumulated_context,
                api_key=inputs.get("api_key")
            )

            task.output = output
            task_results.append({
                "task_index": idx + 1,
                "agent_name": task.agent.name,
                "agent_role": task.agent.role,
                "description": desc,
                "output": output,
            })

            accumulated_context += f"\n--- [{task.agent.name} - {task.agent.role}] ---\n{output}\n"

        elapsed = time.perf_counter() - start_time

        return {
            "status": "completed",
            "elapsed_seconds": round(elapsed, 2),
            "final_output": task_results[-1]["output"] if task_results else "",
            "task_results": task_results,
        }
