import os
import subprocess
import fnmatch
import re
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field

# ---------- Tool schemas ----------
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file relative to the workspace root.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path to the file."},
                    "start_line": {"type": "integer", "description": "1-based start line (optional)."},
                    "end_line": {"type": "integer", "description": "1-based end line (optional)."},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create or overwrite a file with the given content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path to the file."},
                    "content": {"type": "string", "description": "Full content to write."},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List files/directories at the given path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path. Defaults to '.'"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_bash",
            "description": (
                "Execute a Windows CMD command in the workspace. Use for builds, tests, git, etc. "
                "Output is truncated to ~4000 chars."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The CMD command to execute."},
                    "timeout": {"type": "integer", "description": "Seconds (default 30, max 120)."},
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_powershell",
            "description": (
                "Execute a PowerShell command in the workspace. Use this for advanced Windows operations, "
                "structured JSON parsing (ConvertTo-Json), and safe error handling (try/catch)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The PowerShell command to execute."},
                    "timeout": {"type": "integer", "description": "Seconds (default 30, max 120)."},
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "grep",
            "description": "Search for a regex pattern recursively in files under the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Regex pattern."},
                    "glob": {"type": "string", "description": "File glob filter, e.g. '*.py'. Optional."},
                    "max_results": {"type": "integer", "description": "Default 50."},
                },
                "required": ["pattern"],
            },
        },
    },
]

# ---------- Tool execution ----------
class ToolError(Exception):
    pass

def _safe_path(workspace: Path, rel: str) -> Path:
    workspace = workspace.resolve()
    target = (workspace / rel).resolve()
    try:
        target.relative_to(workspace)
    except ValueError:
        raise ToolError(f"Path '{rel}' is outside the workspace.")
    return target

def read_file(workspace: Path, path: str, start_line: int | None = None, end_line: int | None = None) -> str:
    p = _safe_path(workspace, path)
    if not p.is_file():
        raise ToolError(f"Not a file: {path}")
    text = p.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    if start_line or end_line:
        s = (start_line or 1) - 1
        e = end_line or len(lines)
        lines = lines[s:e]
        return "\n".join(f"{i+1}: {l}" for i, l in enumerate(lines, start=s + 1))
    return "\n".join(f"{i+1}: {l}" for i, l in enumerate(lines, start=1))[:8000]

def write_file(workspace: Path, path: str, content: str) -> str:
    p = _safe_path(workspace, path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"Wrote {len(content)} chars to {path}"

def list_directory(workspace: Path, path: str = ".") -> str:
    p = _safe_path(workspace, path)
    if not p.is_dir():
        raise ToolError(f"Not a directory: {path}")
    entries = []
    for entry in sorted(p.iterdir()):
        tag = "DIR " if entry.is_dir() else "FILE"
        size = entry.stat().st_size if entry.is_file() else ""
        entries.append(f"{tag}  {entry.name}{('  ('+str(size)+'B)') if size else ''}")
    return "\n".join(entries) or "(empty)"

def run_bash(workspace: Path, command: str, timeout: int = 30) -> str:
    timeout = min(max(int(timeout), 1), 120)
    try:
        proc = subprocess.run(
            command, shell=True, cwd=str(workspace), capture_output=True, text=True, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        raise ToolError(f"Command timed out after {timeout}s")
    
    result = ""
    if proc.stdout: result += f"[stdout]\n{proc.stdout}"
    if proc.stderr: result += f"\n[stderr]\n{proc.stderr}"
    result += f"\n[exit code: {proc.returncode}]"
    return result[:4000]

def run_powershell(workspace: Path, command: str, timeout: int = 30) -> str:
    timeout = min(max(int(timeout), 1), 120)
    try:
        # -NoProfile speeds up startup, -Command executes the string
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            cwd=str(workspace), capture_output=True, text=True, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        raise ToolError(f"PowerShell command timed out after {timeout}s")
    
    result = ""
    if proc.stdout: result += f"[stdout]\n{proc.stdout}"
    if proc.stderr: result += f"\n[stderr]\n{proc.stderr}"
    result += f"\n[exit code: {proc.returncode}]"
    return result[:4000]

def grep(workspace: Path, pattern: str, glob: str | None = None, max_results: int = 50) -> str:
    rx = re.compile(pattern)
    matches: list[str] = []
    for root, _dirs, files in os.walk(workspace):
        for name in files:
            if glob and not fnmatch.fnmatch(name, glob):
                continue
            fp = Path(root) / name
            try:
                for i, line in enumerate(fp.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                    if rx.search(line):
                        rel = fp.relative_to(workspace)
                        matches.append(f"{rel}:{i}: {line.strip()[:200]}")
                        if len(matches) >= max_results:
                            return "\n".join(matches) + f"\n...truncated at {max_results}"
            except Exception:
                continue
    return "\n".join(matches) if matches else "No matches."

def execute_tool(name: str, args: dict, workspace: Path) -> str:
    try:
        if name == "read_file": return read_file(workspace, **args)
        if name == "write_file": return write_file(workspace, **args)
        if name == "list_directory": return list_directory(workspace, **args)
        if name == "run_bash": return run_bash(workspace, **args)
        if name == "run_powershell": return run_powershell(workspace, **args)
        if name == "grep": return grep(workspace, **args)
        raise ToolError(f"Unknown tool: {name}")
    except ToolError as e:
        return f"[ERROR] {e}"
    except Exception as e:
        return f"[ERROR] {type(e).__name__}: {e}"