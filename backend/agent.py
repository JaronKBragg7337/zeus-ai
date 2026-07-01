"""Agent mode - multi-step task execution with tool use."""
import json
import re
from typing import List, Dict, Any, AsyncIterator, Optional
from ollama_client import ollama
from tools import get_tool_definitions, execute_tool


SYSTEM_PROMPT = """You are OmniLocal AI Agent, a helpful assistant that can use tools to accomplish tasks.
You have access to file operations, shell commands, search, and calculations.

When given a task:
1. Think step by step about what needs to be done
2. Use tools when needed to gather information or make changes
3. Provide clear, concise results to the user

Always prefer using tools over asking the user to do things manually.
When reading code or configs, summarize key findings rather than dumping everything.
When writing files, ensure proper formatting and completeness.

You can only call one tool at a time. Wait for the result before deciding next steps.
"""


async def run_agent_task(task: str, model: str = "qwen3.5:4b",
                         project_path: Optional[str] = None,
                         max_steps: int = 10) -> AsyncIterator[Dict[str, Any]]:
    """Run an agent task with tool use, yielding progress updates."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Task: {task}" + (f"\nProject path: {project_path}" if project_path else "")}
    ]

    tools = get_tool_definitions()
    step = 0

    yield {"type": "status", "message": f"Starting task: {task}"}

    while step < max_steps:
        step += 1
        yield {"type": "status", "message": f"Step {step}/{max_steps} - thinking..."}

        response_text = ""
        tool_calls = None

        # Stream the response to collect it
        async for chunk in ollama.chat(messages, model=model, stream=False, tools=tools):
            response_text += chunk

        # Check if model wants to use tools (parse from response for models that don't natively support tool calling)
        tool_call = _extract_tool_call(response_text)

        if tool_call:
            tool_name = tool_call["name"]
            tool_params = tool_call["parameters"]

            yield {"type": "tool_call", "name": tool_name, "parameters": tool_params}

            # Execute the tool
            result = execute_tool(tool_name, tool_params)

            yield {"type": "tool_result", "name": tool_name, "result": result}

            # Add to conversation
            result_str = json.dumps(result, indent=2)[:4000]
            messages.append({"role": "assistant", "content": response_text})
            messages.append({"role": "user", "content": f"Tool '{tool_name}' result:\n{result_str}\n\nContinue with the task."})
        else:
            # No tool call, task is done
            messages.append({"role": "assistant", "content": response_text})
            yield {"type": "complete", "message": response_text, "steps": step}
            break

    if step >= max_steps:
        yield {"type": "complete", "message": "Maximum steps reached. Task may be incomplete.", "steps": step}


def _extract_tool_call(text: str) -> Optional[Dict[str, Any]]:
    """Extract tool call from model response. Handles various formats."""
    # Try to find JSON tool call in the text
    text = text.strip()

    # Look for ```json blocks with tool calls
    if "```json" in text:
        json_parts = text.split("```json")
        for part in json_parts[1:]:
            json_str = part.split("```")[0].strip()
            try:
                data = json.loads(json_str)
                if "name" in data and "parameters" in data:
                    return data
            except json.JSONDecodeError:
                continue

    # Look for explicit tool call format: TOOL: name(params)
    tool_pattern = r'(?:TOOL|tool|function)\s*[:\(]\s*["\']?(\w+)["\']?\s*[:\(]\s*(\{[^}]*\})'
    match = re.search(tool_pattern, text, re.IGNORECASE)
    if match:
        try:
            return {"name": match.group(1), "parameters": json.loads(match.group(2))}
        except json.JSONDecodeError:
            pass

    # Check if the model is indicating it wants to use a tool naturally
    lower = text.lower()
    if any(x in lower for x in ["i'll use", "let me use", "i will use", "using tool", "calling tool"]):
        # Try to extract from natural language
        for tool in get_tool_definitions():
            name = tool["function"]["name"]
            if name.lower() in lower:
                # Try to extract parameters
                params = {}
                for param_name in tool["function"]["parameters"].get("properties", {}).keys():
                    # Look for param=value patterns
                    param_pattern = rf'{param_name}["\']?\s*[:=]\s*["\']?([^"\'\n,)]+)'
                    pm = re.search(param_pattern, text, re.IGNORECASE)
                    if pm:
                        params[param_name] = pm.group(1).strip()
                if params:
                    return {"name": name, "parameters": params}

    return None
