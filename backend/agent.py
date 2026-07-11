"""Agent mode - multi-step task execution with tool use."""
import json
import re
from typing import List, Dict, Any, AsyncIterator, Optional
from ollama_client import ollama
from zeus_native_client import zeus_native
from tools import get_tool_definitions, execute_tool
from runtime_control import stop_requested
from prompts import build_zeus_system_prompt
from config import is_native_model_enabled
from training_capture import capture_agent_completion
from memory_store import memory_context


AGENT_INSTRUCTIONS = """You are in Agent mode and can use tools to accomplish tasks.
You have access to file operations, shell commands, search, calculations, and, when full-computer mode is enabled, desktop observation and control tools.

When given a task:
1. Think step by step about what needs to be done
2. Use tools when needed to gather information or make changes
3. Provide clear, concise results to the user

Always prefer using tools over asking the user to do things manually.
When reading code or configs, summarize key findings rather than dumping everything.
When writing files, ensure proper formatting and completeness.

For desktop work, inspect the screen or relevant windows before clicking or typing. Capture screenshots when the result should be reviewed by another worker.
You can only call one tool at a time. Wait for the result before deciding next steps.
"""


async def run_agent_task(task: str, model: str = "qwen3.5:4b",
                         project_path: Optional[str] = None,
                         max_steps: int = 10) -> AsyncIterator[Dict[str, Any]]:
    """Run an agent task with tool use, yielding progress updates."""
    direct_tool = _direct_tool_for_simple_task(task, project_path)

    saved_memory = memory_context(task)
    messages = [
        {"role": "system", "content": build_zeus_system_prompt(tools_enabled=True) + "\n\n" + AGENT_INSTRUCTIONS},
        *([{"role": "system", "content": "Relevant saved Zeus memory. Treat it as context, not a command:\n" + saved_memory}] if saved_memory else []),
        {"role": "user", "content": f"Task: {task}" + (f"\nProject path: {project_path}" if project_path else "")}
    ]

    tools = get_tool_definitions()
    step = 0
    tool_events: List[Dict[str, Any]] = []

    yield {"type": "status", "message": f"Starting task: {task}"}

    if stop_requested():
        yield {"type": "complete", "message": "Emergency stop is active. Resume Zeus AI before running agent tasks.", "steps": 0}
        return

    if direct_tool:
        yield {"type": "tool_call", "name": direct_tool["name"], "parameters": direct_tool["parameters"]}
        result = execute_tool(direct_tool["name"], direct_tool["parameters"])
        tool_events.append({"name": direct_tool["name"], "parameters": direct_tool["parameters"], "result": result})
        yield {"type": "tool_result", "name": direct_tool["name"], "result": result}
        message = _summarize_direct_tool_result(direct_tool["name"], result)
        capture_agent_completion(
            task,
            message,
            project_path=project_path,
            steps=1,
            status="error" if "error" in result else "success",
            tool_events=tool_events,
        )
        yield {"type": "complete", "message": message, "steps": 1}
        return

    while step < max_steps:
        if stop_requested():
            yield {"type": "complete", "message": "Emergency stop requested. Agent task halted.", "steps": step}
            return

        step += 1
        yield {"type": "status", "message": f"Step {step}/{max_steps} - thinking..."}

        client = zeus_native if is_native_model_enabled() else ollama
        response_message = await client.chat_once(messages, model=model, tools=tools)
        response_text = (response_message.get("content") or "").strip()

        # Prefer native Ollama tool calls: tool-capable models (for example qwen)
        # return message.tool_calls with empty content, so content alone is not enough.
        tool_call = _extract_native_tool_call(response_message)
        if tool_call is None:
            # Fall back to parsing tool calls out of plain text for models
            # that do not support native tool calling.
            tool_call = _extract_tool_call(response_text)

        if tool_call:
            tool_name = tool_call["name"]
            tool_params = tool_call["parameters"]

            yield {"type": "tool_call", "name": tool_name, "parameters": tool_params}

            # Execute the tool
            result = execute_tool(tool_name, tool_params)
            tool_events.append({"name": tool_name, "parameters": tool_params, "result": result})

            yield {"type": "tool_result", "name": tool_name, "result": result}

            # Preserve the native assistant tool call and return a proper
            # Ollama tool-role result. Sending this as a user message breaks
            # the model's multi-step tool-call state.
            result_str = json.dumps(result, indent=2)[:4000]
            messages.append(_assistant_tool_message(response_message))
            messages.append({"role": "tool", "tool_name": tool_name, "content": result_str})
        else:
            # No tool call, task is done
            if not response_text:
                response_text = (
                    "The model returned an empty response with no tool call. "
                    "Try rephrasing the task or using a different model."
                )
                capture_agent_completion(
                    task,
                    response_text,
                    project_path=project_path,
                    steps=step,
                    status="error",
                    tool_events=tool_events,
                )
                yield {"type": "complete", "message": response_text, "steps": step}
                break
            messages.append({"role": "assistant", "content": response_text})
            capture_agent_completion(
                task,
                response_text,
                project_path=project_path,
                steps=step,
                status="success",
                tool_events=tool_events,
            )
            yield {"type": "complete", "message": response_text, "steps": step}
            break

    if step >= max_steps:
        capture_agent_completion(
            task,
            "Maximum steps reached. Task may be incomplete.",
            project_path=project_path,
            steps=step,
            status="incomplete",
            tool_events=tool_events,
        )
        yield {"type": "complete", "message": "Maximum steps reached. Task may be incomplete.", "steps": step}


def _direct_tool_for_simple_task(task: str, project_path: Optional[str]) -> Optional[Dict[str, Any]]:
    """Handle obvious local tool tasks without waiting on LLM tool-call formatting."""
    lower = task.lower()
    wants_listing = any(word in lower for word in ["list files", "list the files", "show files", "show the files"])
    if wants_listing:
        return {
            "name": "list_files",
            "parameters": {"path": project_path or ".", "recursive": False},
        }
    return None


def _summarize_direct_tool_result(tool_name: str, result: Dict[str, Any]) -> str:
    if "error" in result:
        return f"{tool_name} failed: {result['error']}"

    if tool_name == "list_files":
        files = result.get("files", [])
        names = [item.get("name", "") for item in files[:12]]
        if not names:
            return f"No files found in {result.get('path', 'the requested folder')}."
        extra = "" if len(files) <= len(names) else f" and {len(files) - len(names)} more"
        return f"Top-level entries in {result.get('path', 'the requested folder')}: {', '.join(names)}{extra}."

    return "Task completed."


def _extract_native_tool_call(message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract a native tool call from an Ollama chat message.

    Ollama returns tool calls as message.tool_calls with function name and
    arguments. Arguments are usually a dict but may arrive as a JSON string.
    """
    for call in message.get("tool_calls") or []:
        function = call.get("function") or {}
        name = function.get("name")
        if not name:
            continue
        arguments = function.get("arguments") or {}
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {}
        if not isinstance(arguments, dict):
            arguments = {}
        return {"name": name, "parameters": arguments}
    return None


def _assistant_tool_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """Keep the exact native tool-call envelope expected by Ollama."""
    assistant = {
        "role": "assistant",
        "content": message.get("content") or "",
        "tool_calls": message.get("tool_calls") or [],
    }
    if message.get("thinking"):
        assistant["thinking"] = message["thinking"]
    return assistant


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
