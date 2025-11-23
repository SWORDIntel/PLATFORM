#!/usr/bin/env python3
"""
Code Tools for Self-Coding Agent
Provides file operations, code search, and code modification capabilities.
"""

import os
import re
import ast
import subprocess
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import difflib


@dataclass
class FileInfo:
    """Information about a file."""
    path: str
    size: int
    lines: int
    language: str
    exists: bool


@dataclass
class SearchResult:
    """Code search result."""
    file_path: str
    line_number: int
    line_content: str
    match_type: str  # 'exact', 'regex', 'fuzzy'


class CodeTools:
    """
    Tools for autonomous code operations.
    Similar to Claude Code's file operations.
    """

    def __init__(self, workspace_root: str = None):
        self.workspace_root = workspace_root or os.getcwd()
        self.file_extensions = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.cpp': 'cpp',
            '.c': 'c',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust',
            '.sh': 'bash',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.json': 'json',
            '.md': 'markdown',
        }

    def _is_safe_path(self, path: str) -> bool:
        """Check if path is within workspace."""
        abs_path = os.path.abspath(path)
        abs_workspace = os.path.abspath(self.workspace_root)
        return abs_path.startswith(abs_workspace)

    def read_file(self, file_path: str, start_line: int = 0, end_line: int = None) -> Dict[str, Any]:
        """
        Read file contents with optional line range.

        Args:
            file_path: Path to file
            start_line: Starting line (0-indexed)
            end_line: Ending line (exclusive), None for EOF

        Returns:
            Dict with 'content', 'lines', 'path'
        """
        if not self._is_safe_path(file_path):
            return {"error": f"Path outside workspace: {file_path}"}

        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()

            if end_line is None:
                end_line = len(lines)

            selected_lines = lines[start_line:end_line]

            return {
                "content": ''.join(selected_lines),
                "lines": selected_lines,
                "total_lines": len(lines),
                "path": file_path,
                "range": (start_line, min(end_line, len(lines)))
            }
        except Exception as e:
            return {"error": str(e)}

    def write_file(self, file_path: str, content: str, create_dirs: bool = True) -> Dict[str, Any]:
        """
        Write content to file.

        Args:
            file_path: Path to file
            content: Content to write
            create_dirs: Create parent directories if needed

        Returns:
            Dict with 'success', 'path', 'size'
        """
        if not self._is_safe_path(file_path):
            return {"error": f"Path outside workspace: {file_path}"}

        try:
            if create_dirs:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return {
                "success": True,
                "path": file_path,
                "size": len(content),
                "lines": content.count('\n') + 1
            }
        except Exception as e:
            return {"error": str(e)}

    def edit_file(self, file_path: str, old_content: str, new_content: str) -> Dict[str, Any]:
        """
        Edit file by replacing old_content with new_content.
        Similar to Claude Code's Edit tool.

        Args:
            file_path: Path to file
            old_content: String to find and replace
            new_content: Replacement string

        Returns:
            Dict with 'success', 'changes', 'diff'
        """
        if not self._is_safe_path(file_path):
            return {"error": f"Path outside workspace: {file_path}"}

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original = f.read()

            if old_content not in original:
                return {"error": f"String not found in {file_path}"}

            modified = original.replace(old_content, new_content, 1)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified)

            # Generate diff
            diff = list(difflib.unified_diff(
                original.splitlines(keepends=True),
                modified.splitlines(keepends=True),
                fromfile=file_path,
                tofile=file_path,
                lineterm=''
            ))

            return {
                "success": True,
                "path": file_path,
                "changes": 1,
                "diff": ''.join(diff)
            }
        except Exception as e:
            return {"error": str(e)}

    def search_files(self, pattern: str, file_glob: str = "**/*",
                     regex: bool = False, max_results: int = 100) -> List[SearchResult]:
        """
        Search for pattern in files.
        Similar to Claude Code's Grep tool.

        Args:
            pattern: Search pattern
            file_glob: Glob pattern for files
            regex: Use regex matching
            max_results: Maximum results to return

        Returns:
            List of SearchResult objects
        """
        results = []
        workspace_path = Path(self.workspace_root)

        try:
            for file_path in workspace_path.glob(file_glob):
                if not file_path.is_file():
                    continue

                if not self._is_safe_path(str(file_path)):
                    continue

                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line_num, line in enumerate(f, 1):
                            if regex:
                                if re.search(pattern, line):
                                    results.append(SearchResult(
                                        file_path=str(file_path),
                                        line_number=line_num,
                                        line_content=line.rstrip(),
                                        match_type='regex'
                                    ))
                            else:
                                if pattern in line:
                                    results.append(SearchResult(
                                        file_path=str(file_path),
                                        line_number=line_num,
                                        line_content=line.rstrip(),
                                        match_type='exact'
                                    ))

                            if len(results) >= max_results:
                                return results
                except:
                    continue
        except Exception as e:
            pass

        return results

    def list_files(self, directory: str = ".", pattern: str = "*") -> List[FileInfo]:
        """
        List files in directory matching pattern.

        Args:
            directory: Directory to search
            pattern: Glob pattern

        Returns:
            List of FileInfo objects
        """
        dir_path = os.path.join(self.workspace_root, directory)

        if not self._is_safe_path(dir_path):
            return []

        files = []
        try:
            for file_path in Path(dir_path).glob(pattern):
                if file_path.is_file():
                    stat = file_path.stat()
                    ext = file_path.suffix

                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        line_count = sum(1 for _ in f)

                    files.append(FileInfo(
                        path=str(file_path.relative_to(self.workspace_root)),
                        size=stat.st_size,
                        lines=line_count,
                        language=self.file_extensions.get(ext, 'unknown'),
                        exists=True
                    ))
        except Exception as e:
            pass

        return files

    def run_command(self, command: str, cwd: str = None, timeout: int = 30) -> Dict[str, Any]:
        """
        Run shell command and capture output.

        Args:
            command: Command to run
            cwd: Working directory (relative to workspace)
            timeout: Timeout in seconds

        Returns:
            Dict with 'stdout', 'stderr', 'returncode'
        """
        work_dir = self.workspace_root
        if cwd:
            work_dir = os.path.join(self.workspace_root, cwd)

        if not self._is_safe_path(work_dir):
            return {"error": "Working directory outside workspace"}

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {"error": f"Command timed out after {timeout}s"}
        except Exception as e:
            return {"error": str(e)}

    def get_file_info(self, file_path: str) -> FileInfo:
        """Get information about a file."""
        if not self._is_safe_path(file_path):
            return FileInfo(file_path, 0, 0, 'unknown', False)

        try:
            stat = os.stat(file_path)
            ext = os.path.splitext(file_path)[1]

            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                line_count = sum(1 for _ in f)

            return FileInfo(
                path=file_path,
                size=stat.st_size,
                lines=line_count,
                language=self.file_extensions.get(ext, 'unknown'),
                exists=True
            )
        except:
            return FileInfo(file_path, 0, 0, 'unknown', False)

    def analyze_python_file(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze Python file structure.
        Extract classes, functions, imports.
        """
        if not self._is_safe_path(file_path):
            return {"error": "Path outside workspace"}

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=file_path)

            classes = []
            functions = []
            imports = []

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append({
                        "name": node.name,
                        "line": node.lineno,
                        "methods": [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
                    })
                elif isinstance(node, ast.FunctionDef):
                    if not any(node in cls.body for cls in ast.walk(tree) if isinstance(cls, ast.ClassDef)):
                        functions.append({
                            "name": node.name,
                            "line": node.lineno,
                            "args": [arg.arg for arg in node.args.args]
                        })
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        imports.extend([alias.name for alias in node.names])
                    else:
                        imports.append(node.module)

            return {
                "classes": classes,
                "functions": functions,
                "imports": list(set(imports)),
                "path": file_path
            }
        except Exception as e:
            return {"error": str(e)}
