"""Tool definitions and execution for the AI agent."""
import os
import glob
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, List, Optional


def get_tool_definitions() -> List[Dict[str, Any]]:
    """Return tool definitions in Ollama format."""
    return [
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
                "name": "run_command",
                "description": "Run a shell command. Use for git operations, running scripts, building, testing, etc. Be careful with destructive commands.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "Shell command to execute"},
                        "cwd": {"type": "string", "description": "Working directory", "default": "."}
                    },
                    "required": ["command"]
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


def execute_tool(name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a tool by name with given parameters."""
    try:
        if name == "read_file":
            return _read_file(**parameters)
        elif name == "write_file":
            return _write_file(**parameters)
        elif name == "list_files":
            return _list_files(**parameters)
        elif name == "run_command":
            return _run_command(**parameters)
        elif name == "search_files":
            return _search_files(**parameters)
        elif name == "get_project_structure":
            return _get_project_structure(**parameters)
        elif name == "calculate":
            return _calculate(**parameters)
        else:
            return {"error": f"Unknown tool: {name}"}
    except Exception as e:
        return {"error": str(e)}


def _read_file(path: str) -> Dict[str, Any]:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return {"error": f"File not found: {path}"}
    if p.is_dir():
        return {"error": f"Path is a directory: {path}"}
    if p.stat().st_size > 5 * 1024 * 1024:
        return {"error": "File too large (>5MB)"}
    try:
        content = p.read_text(encoding="utf-8", errors="replace")
        return {"content": content, "path": str(p), "size": len(content)}
    except Exception as e:
        return {"error": f"Cannot read file: {e}"}


def _write_file(path: str, content: str) -> Dict[str, Any]:
    p = Path(path).expanduser().resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return {"success": True, "path": str(p), "bytes_written": len(content)}


def _list_files(path: str, recursive: bool = False) -> Dict[str, Any]:
    p = Path(path).expanduser().resolve()
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
    dangerous = ["rm -rf /", "mkfs.", ":(){ :|:& };:", "> /dev/sda", "dd if=/dev/zero"]
    for d in dangerous:
        if d in command.lower():
            return {"error": f"Blocked dangerous command containing: {d}"}

    try:
        result = subprocess.run(
            command, shell=True, cwd=cwd, capture_output=True,
            text=True, timeout=60
        )
        return {
            "stdout": result.stdout[:10000] if result.stdout else "",
            "stderr": result.stderr[:5000] if result.stderr else "",
            "returncode": result.returncode,
            "command": command
        }
    except subprocess.TimeoutExpired:
        return {"error": "Command timed out (60s)", "command": command}
    except Exception as e:
        return {"error": str(e), "command": command}


def _search_files(pattern: str, path: str = ".", content_search: bool = False) -> Dict[str, Any]:
    p = Path(path).expanduser().resolve()
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
    p = Path(path).expanduser().resolve()
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
            if entry.name.startswith(".") and entry.name not in [".gitignore", ".env", ".github"]:
                continue
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
