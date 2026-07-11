"""Tool definitions and execution for the AI agent."""
import os
import glob
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from audit_log import append_action
from config import (
    PROJECT_ROOT,
    get_allowed_roots,
    get_command_risk_policy,
    is_full_computer_access_enabled,
    is_shell_enabled,
)
from desktop_control import (
    capture_screen,
    click_mouse,
    focus_window,
    get_screen_info,
    list_windows,
    move_mouse,
    press_keys,
    read_screen_text,
    type_text,
    wait_for,
)
from runtime_control import stop_requested
from training_capture import capture_tool_call


MAX_TEXT_FILE_SIZE = 5 * 1024 * 1024


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _resolve_allowed_path(path: str, *, for_write: bool = False) -> Path:
    """Resolve a path inside configured allowed roots."""
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate

    resolved = candidate.resolve()
    check_path = resolved.parent if for_write and not resolved.exists() else resolved
    roots = get_allowed_roots()

    if not any(_is_relative_to(check_path, root) for root in roots):
        allowed = ", ".join(str(root) for root in roots)
        raise ValueError(f"Path is outside allowed roots. Allowed roots: {allowed}")
    return resolved


def get_tool_definitions() -> List[Dict[str, Any]]:
    """Return tool definitions in Ollama format."""
    tools = [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read the contents of a file at the given path. Use for viewing code, docs, or any text file.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Absolute or relative path to the file"
                        }
                    },
                    "required": ["path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "write_file",
                "description": "Write content to a file. Creates the file if it doesn't exist. Overwrites existing content.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to the file"},
                        "content": {"type": "string", "description": "Content to write"}
                    },
                    "required": ["path", "content"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "list_files",
                "description": "List files in a directory. Shows files and subdirectories.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Directory path"},
                        "recursive": {"type": "boolean", "description": "List recursively", "default": False}
                    },
                    "required": ["path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_files",
                "description": "Search for files matching a glob pattern, or search file contents with grep-like functionality.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pattern": {"type": "string", "description": "Glob pattern or search term"},
                        "path": {"type": "string", "description": "Directory to search in", "default": "."},
                        "content_search": {"type": "boolean", "description": "If true, search inside file contents instead of filenames", "default": False}
                    },
                    "required": ["pattern"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_project_structure",
                "description": "Get a tree view of the project structure starting from a root path. Great for understanding codebases.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Root project path"},
                        "max_depth": {"type": "integer", "description": "Maximum depth to traverse", "default": 4}
                    },
                    "required": ["path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "calculate",
                "description": "Perform calculations using Python eval. Use for math, data processing, etc.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string", "description": "Python expression to evaluate"}
                    },
                    "required": ["expression"]
                }
            }
        }
    ]
    if is_shell_enabled():
        tools.append({
            "type": "function",
            "function": {
                "name": "run_command",
                "description": "Run a shell command in an allowed project directory. Disabled unless ZEUSAI_ENABLE_SHELL=1.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "Shell command to execute"},
                        "cwd": {"type": "string", "description": "Working directory", "default": "."}
                    },
                    "required": ["command"]
                }
            }
        })
    if is_full_computer_access_enabled():
        tools.extend([
            {
                "type": "function",
                "function": {
                    "name": "get_screen_info",
                    "description": "Get screen dimensions and current mouse position before interacting with the desktop.",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "list_windows",
                    "description": "List visible top-level desktop windows with titles, handles, process IDs, and screen bounds.",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "focus_window",
                    "description": "Restore and focus a desktop window using a handle returned by list_windows.",
                    "parameters": {
                        "type": "object",
                        "properties": {"handle": {"type": "integer", "description": "Window handle from list_windows."}},
                        "required": ["handle"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "capture_screen",
                    "description": "Capture the desktop or a screen region to a timestamped local PNG for review by Zeus or other AI workers.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Optional destination PNG path."},
                            "left": {"type": "integer"}, "top": {"type": "integer"},
                            "width": {"type": "integer"}, "height": {"type": "integer"},
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "read_screen_text",
                    "description": "Use local OCR to read the desktop or a screen region.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "left": {"type": "integer"}, "top": {"type": "integer"},
                            "width": {"type": "integer"}, "height": {"type": "integer"},
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "move_mouse",
                    "description": "Move the mouse cursor to absolute desktop coordinates.",
                    "parameters": {
                        "type": "object",
                        "properties": {"x": {"type": "integer"}, "y": {"type": "integer"}, "duration_ms": {"type": "integer", "default": 0}},
                        "required": ["x", "y"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "click_mouse",
                    "description": "Click at absolute desktop coordinates.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "x": {"type": "integer"}, "y": {"type": "integer"},
                            "button": {"type": "string", "default": "left"},
                            "clicks": {"type": "integer", "default": 1},
                            "interval_ms": {"type": "integer", "default": 0},
                        },
                        "required": ["x", "y"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "type_text",
                    "description": "Type literal text into the currently focused desktop application.",
                    "parameters": {
                        "type": "object",
                        "properties": {"text": {"type": "string"}, "interval_ms": {"type": "integer", "default": 0}},
                        "required": ["text"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "press_keys",
                    "description": "Press a keyboard combination in the currently focused desktop application, such as [\"ctrl\", \"s\"].",
                    "parameters": {
                        "type": "object",
                        "properties": {"keys": {"type": "array", "items": {"type": "string"}}, "interval_ms": {"type": "integer", "default": 0}},
                        "required": ["keys"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "wait_for",
                    "description": "Wait for a specified duration between desktop actions.",
                    "parameters": {
                        "type": "object",
                        "properties": {"milliseconds": {"type": "integer"}},
                        "required": ["milliseconds"],
                    },
                },
            },
        ])
    return tools


def execute_tool(name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a tool by name with given parameters."""
    if stop_requested():
        result = {"error": "Emergency stop is active. Resume Zeus AI before running tools."}
        append_action({
            "type": "tool",
            "name": name,
            "parameters": parameters,
            "status": "blocked_by_kill",
            "result": result,
        })
        capture_tool_call(name, parameters, result, "blocked_by_kill")
        return result

    try:
        if name == "read_file":
            result = _read_file(**parameters)
        elif name == "write_file":
            result = _write_file(**parameters)
        elif name == "list_files":
            result = _list_files(**parameters)
        elif name == "run_command":
            result = _run_command(**parameters)
        elif name == "search_files":
            result = _search_files(**parameters)
        elif name == "get_project_structure":
            result = _get_project_structure(**parameters)
        elif name == "calculate":
            result = _calculate(**parameters)
        elif name == "get_screen_info":
            result = get_screen_info()
        elif name == "list_windows":
            result = list_windows()
        elif name == "focus_window":
            result = focus_window(**parameters)
        elif name == "capture_screen":
            result = capture_screen(**parameters)
        elif name == "read_screen_text":
            result = read_screen_text(**parameters)
        elif name == "move_mouse":
            result = move_mouse(**parameters)
        elif name == "click_mouse":
            result = click_mouse(**parameters)
        elif name == "type_text":
            result = type_text(**parameters)
        elif name == "press_keys":
            result = press_keys(**parameters)
        elif name == "wait_for":
            result = wait_for(**parameters)
        else:
            result = {"error": f"Unknown tool: {name}"}
    except Exception as e:
        result = {"error": str(e)}

    status = "error" if "error" in result else "ok"
    append_action({
        "type": "tool",
        "name": name,
        "parameters": parameters,
        "status": status,
        "result": _summarize_result(result),
    })
    capture_tool_call(name, parameters, result, status)
    return result


def _summarize_result(result: Dict[str, Any]) -> Dict[str, Any]:
    if "content" in result:
        return {**result, "content": f"[{len(result.get('content', ''))} chars]"}
    if "files" in result:
        return {**result, "files": result["files"][:20], "file_count": len(result["files"])}
    if "matches" in result:
        return {**result, "matches": result["matches"][:20], "match_count": len(result["matches"])}
    return result


def _read_file(path: str) -> Dict[str, Any]:
    p = _resolve_allowed_path(path)
    if not p.exists():
        return {"error": f"File not found: {path}"}
    if p.is_dir():
        return {"error": f"Path is a directory: {path}"}
    if p.stat().st_size > MAX_TEXT_FILE_SIZE:
        return {"error": "File too large (>5MB)"}
    try:
        content = p.read_text(encoding="utf-8", errors="replace")
        return {"content": content, "path": str(p), "size": len(content)}
    except Exception as e:
        return {"error": f"Cannot read file: {e}"}


def _write_file(path: str, content: str) -> Dict[str, Any]:
    p = _resolve_allowed_path(path, for_write=True)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return {"success": True, "path": str(p), "bytes_written": len(content)}


def _list_files(path: str, recursive: bool = False) -> Dict[str, Any]:
    p = _resolve_allowed_path(path)
    if not p.exists():
        return {"error": f"Path not found: {path}"}
    if not p.is_dir():
        return {"error": f"Not a directory: {path}"}

    files = []
    iterator = p.rglob("*") if recursive else p.iterdir()
    for item in iterator:
        try:
            files.append({
                "name": item.name,
                "path": str(item),
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None
            })
        except (PermissionError, OSError):
            continue
    return {"files": sorted(files, key=lambda x: (x["type"] != "directory", x["name"])), "path": str(p)}


def _run_command(command: str, cwd: str = ".") -> Dict[str, Any]:
    """Run a shell command safely."""
    if not is_shell_enabled():
        return {"error": "Shell command execution is disabled. Set ZEUSAI_ENABLE_SHELL=1 to enable it for allowed project roots."}

    dangerous = [
        "rm -rf /", "mkfs.", ":(){ :|:& };:", "> /dev/sda", "dd if=/dev/zero",
        "format ", "shutdown", "restart-computer", "remove-item -recurse -force c:",
        "del /s /q c:", "rmdir /s /q c:",
    ]
    risk_matches = [d for d in dangerous if d in command.lower()]
    risk_policy = get_command_risk_policy()
    if risk_matches and risk_policy == "block":
        for d in risk_matches:
            return {"error": f"Blocked dangerous command containing: {d}"}

    try:
        safe_cwd = _resolve_allowed_path(cwd)
        if not safe_cwd.is_dir():
            return {"error": f"Working directory is not a directory: {cwd}"}
        result = subprocess.run(
            command, shell=True, cwd=safe_cwd, capture_output=True,
            text=True, timeout=60
        )
        return {
            "stdout": result.stdout[:10000] if result.stdout else "",
            "stderr": result.stderr[:5000] if result.stderr else "",
            "returncode": result.returncode,
            "command": command,
            "risk_policy": risk_policy,
            "risk_matches": risk_matches,
        }
    except subprocess.TimeoutExpired:
        return {"error": "Command timed out (60s)", "command": command}
    except Exception as e:
        return {"error": str(e), "command": command}


def _search_files(pattern: str, path: str = ".", content_search: bool = False) -> Dict[str, Any]:
    p = _resolve_allowed_path(path)
    if not p.exists():
        return {"error": f"Path not found: {path}"}

    if content_search:
        matches = []
        for file_path in p.rglob("*"):
            if file_path.is_file() and file_path.stat().st_size < 1024 * 1024:
                try:
                    text = file_path.read_text(encoding="utf-8", errors="replace")
                    if pattern.lower() in text.lower():
                        lines = [i + 1 for i, line in enumerate(text.split("\n"))
                                 if pattern.lower() in line.lower()]
                        matches.append({"file": str(file_path), "lines": lines})
                except Exception:
                    continue
        return {"matches": matches[:50], "pattern": pattern, "path": str(p)}
    else:
        matches = list(p.rglob(pattern))
        return {"matches": [{"path": str(m), "type": "directory" if m.is_dir() else "file"}
                            for m in matches[:100]], "pattern": pattern}


def _get_project_structure(path: str, max_depth: int = 4) -> Dict[str, Any]:
    p = _resolve_allowed_path(path)
    if not p.exists():
        return {"error": f"Path not found: {path}"}

    lines = []
    def walk(current: Path, depth: int, prefix: str = ""):
        if depth > max_depth:
            return
        try:
            entries = sorted(current.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        except PermissionError:
            return
        for i, entry in enumerate(entries):
            is_last = i == len(entries) - 1
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{entry.name}{'/' if entry.is_dir() else ''}")
            if entry.is_dir():
                extension = "    " if is_last else "│   "
                walk(entry, depth + 1, prefix + extension)

    lines.append(f"{p.name}/")
    walk(p, 1)
    return {"structure": "\n".join(lines), "path": str(p)}


def _calculate(expression: str) -> Dict[str, Any]:
    safe_dict = {
        "__builtins__": {},
        "abs": abs, "round": round, "max": max, "min": min,
        "sum": sum, "len": len, "pow": pow, "divmod": divmod,
        "int": int, "float": float, "str": str, "bool": bool,
        "list": list, "dict": dict, "set": set, "tuple": tuple,
        "sorted": sorted, "enumerate": enumerate, "zip": zip,
        "map": map, "filter": filter, "range": range,
    }
    import math
    safe_dict.update({k: getattr(math, k) for k in dir(math) if not k.startswith("_")})

    try:
        result = eval(expression, {"__builtins__": {}}, safe_dict)
        return {"result": str(result), "expression": expression}
    except Exception as e:
        return {"error": f"Calculation error: {e}", "expression": expression}
