#!/usr/bin/env python3
"""
Self-Coding Agent - Autonomous Code Generation System
A local Claude-like agent that can autonomously write, modify, and test code.
"""

import os
import json
import asyncio
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import re

# Support running as a module or as a script by allowing both relative and absolute imports.
try:
    from .code_tools import CodeTools, SearchResult, FileInfo
    from .mcp_router import MCPFilesystem
except ImportError:  # pragma: no cover - fallback for non-package execution
    from code_tools import CodeTools, SearchResult, FileInfo
    from mcp_router import MCPFilesystem


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class CodingTask:
    """Represents a coding task."""
    description: str
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 0
    dependencies: List[str] = field(default_factory=list)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None


@dataclass
class AgentAction:
    """Action taken by the agent."""
    action_type: str  # 'read', 'write', 'edit', 'search', 'run', 'plan'
    parameters: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    timestamp: float = field(default_factory=time.time)
    reasoning: str = ""


@dataclass
class ConversationMessage:
    """Message in agent conversation."""
    role: str  # 'system', 'user', 'assistant'
    content: str
    timestamp: float = field(default_factory=time.time)


class SelfCodingAgent:
    """
    Autonomous self-coding agent with Claude-like capabilities.

    Features:
    - Code reading and understanding
    - Autonomous code generation and modification
    - Multi-step planning and execution
    - Integration with MCP servers (context7, memlayer, filesystem)
    - Self-testing and validation
    """

    def __init__(self, workspace_root: str = None, model_name: str = "deepseek-coder-33b",
                 router_url: str = "http://localhost:8000"):
        self.workspace_root = workspace_root or os.getcwd()
        self.model_name = model_name
        self.router_url = router_url

        # Initialize tools
        self.code_tools = CodeTools(self.workspace_root)
        self.mcp_filesystem = MCPFilesystem([self.workspace_root])

        # State management
        self.tasks: List[CodingTask] = []
        self.action_history: List[AgentAction] = []
        self.conversation: List[ConversationMessage] = []
        self.context_memory: Dict[str, Any] = {}

        # Configuration
        self.max_context_lines = 500
        self.max_iterations = 10
        self.auto_test = True

        # System prompt
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """Build system prompt for the agent."""
        return f"""You are an autonomous coding agent with the following capabilities:

AVAILABLE TOOLS:
1. read_file(path, start_line, end_line) - Read file contents
2. write_file(path, content) - Write new file or overwrite existing
3. edit_file(path, old_content, new_content) - Edit file by replacing content
4. search_files(pattern, file_glob, regex) - Search for patterns in files
5. list_files(directory, pattern) - List files in directory
6. run_command(command, cwd) - Execute shell command
7. analyze_python(path) - Analyze Python file structure
8. get_context(topic) - Query context7 MCP for documentation
9. store_memory(key, value) - Store in memlayer MCP
10. recall_memory(key) - Retrieve from memlayer MCP

WORKSPACE: {self.workspace_root}

GUIDELINES:
- Always read files before modifying them
- Use edit_file for small changes, write_file for new files
- Test code after making changes
- Break complex tasks into smaller steps
- Document your reasoning before each action
- Use search_files to understand codebase structure
- Store important context in memlayer for future reference

OUTPUT FORMAT:
For each action, output JSON:
{{
    "reasoning": "Why you're taking this action",
    "action": "tool_name",
    "parameters": {{"param": "value"}},
    "next_steps": ["what to do after"]
}}
"""

    def add_task(self, description: str, priority: int = 0,
                 dependencies: List[str] = None) -> CodingTask:
        """Add a new coding task."""
        task = CodingTask(
            description=description,
            priority=priority,
            dependencies=dependencies or []
        )
        self.tasks.append(task)
        return task

    def plan_task(self, task: CodingTask) -> List[str]:
        """
        Break down task into actionable steps.
        Uses LLM to generate plan.
        """
        planning_prompt = f"""
Task: {task.description}

Break this down into specific, actionable steps.
Each step should be concrete and testable.

Output format:
1. Step one
2. Step two
3. Step three

Steps:"""

        # This would call the LLM router
        # For now, return a simple heuristic-based plan
        steps = []

        # Check if it's a code modification task
        if any(word in task.description.lower() for word in ['add', 'create', 'implement']):
            steps.extend([
                "Search codebase for similar implementations",
                "Identify relevant files to modify",
                "Read and understand existing code",
                "Plan the implementation approach",
                "Write the new code",
                "Test the implementation",
                "Update documentation if needed"
            ])
        elif any(word in task.description.lower() for word in ['fix', 'bug', 'error']):
            steps.extend([
                "Identify the error location",
                "Read surrounding code for context",
                "Understand the root cause",
                "Implement the fix",
                "Test the fix",
                "Verify no regressions"
            ])
        elif any(word in task.description.lower() for word in ['refactor', 'improve']):
            steps.extend([
                "Analyze current code structure",
                "Identify areas for improvement",
                "Plan refactoring strategy",
                "Refactor incrementally",
                "Test after each change",
                "Update tests if needed"
            ])
        else:
            steps = [
                "Understand the requirement",
                "Plan the approach",
                "Implement the solution",
                "Test and validate"
            ]

        return steps

    def execute_action(self, action: AgentAction) -> Dict[str, Any]:
        """Execute a single action."""
        action_type = action.action_type
        params = action.parameters

        try:
            if action_type == 'read_file':
                result = self.code_tools.read_file(
                    params['path'],
                    params.get('start_line', 0),
                    params.get('end_line')
                )
            elif action_type == 'write_file':
                result = self.code_tools.write_file(
                    params['path'],
                    params['content']
                )
            elif action_type == 'edit_file':
                result = self.code_tools.edit_file(
                    params['path'],
                    params['old_content'],
                    params['new_content']
                )
            elif action_type == 'search_files':
                results = self.code_tools.search_files(
                    params['pattern'],
                    params.get('file_glob', '**/*'),
                    params.get('regex', False)
                )
                result = {"results": [r.__dict__ for r in results]}
            elif action_type == 'list_files':
                files = self.code_tools.list_files(
                    params.get('directory', '.'),
                    params.get('pattern', '*')
                )
                result = {"files": [f.__dict__ for f in files]}
            elif action_type == 'run_command':
                result = self.code_tools.run_command(
                    params['command'],
                    params.get('cwd')
                )
            elif action_type == 'analyze_python':
                result = self.code_tools.analyze_python_file(params['path'])
            else:
                result = {"error": f"Unknown action type: {action_type}"}

            action.result = result
            self.action_history.append(action)
            return result

        except Exception as e:
            result = {"error": str(e)}
            action.result = result
            self.action_history.append(action)
            return result

    def autonomous_code(self, task_description: str, max_iterations: int = None) -> Dict[str, Any]:
        """
        Autonomously complete a coding task.

        This is the main entry point for autonomous operation.

        Args:
            task_description: Natural language description of the task
            max_iterations: Maximum planning/execution loops

        Returns:
            Dict with 'success', 'result', 'actions_taken'
        """
        max_iterations = max_iterations or self.max_iterations

        # Create task
        task = self.add_task(task_description)
        task.status = TaskStatus.IN_PROGRESS

        # Generate plan
        plan_steps = self.plan_task(task)

        print(f"\n=== AUTONOMOUS CODING TASK ===")
        print(f"Task: {task_description}")
        print(f"\nPlan ({len(plan_steps)} steps):")
        for i, step in enumerate(plan_steps, 1):
            print(f"  {i}. {step}")
        print()

        # Execute plan
        iteration = 0
        completed_steps = []

        while iteration < max_iterations and len(completed_steps) < len(plan_steps):
            iteration += 1
            current_step = plan_steps[len(completed_steps)]

            print(f"\n--- Iteration {iteration}: {current_step} ---")

            # Generate action for current step
            action = self._generate_action_for_step(current_step, task)

            if action:
                print(f"Action: {action.action_type}")
                print(f"Reasoning: {action.reasoning}")

                # Execute action
                result = self.execute_action(action)

                if "error" not in result:
                    completed_steps.append(current_step)
                    print(f"✓ Completed: {current_step}")
                else:
                    print(f"✗ Error: {result['error']}")
                    # Try to recover or adjust plan
                    if iteration >= max_iterations - 2:
                        break
            else:
                # No action could be generated, mark step as complete
                completed_steps.append(current_step)

        # Update task status
        if len(completed_steps) == len(plan_steps):
            task.status = TaskStatus.COMPLETED
            task.completed_at = time.time()
            success = True
        else:
            task.status = TaskStatus.FAILED
            success = False

        return {
            "success": success,
            "task": task.__dict__,
            "plan": plan_steps,
            "completed_steps": completed_steps,
            "actions_taken": len(self.action_history),
            "iterations": iteration
        }

    def _generate_action_for_step(self, step: str, task: CodingTask) -> Optional[AgentAction]:
        """
        Generate an action for a given step.
        This uses heuristics to map steps to actions.
        In production, this would call the LLM.
        """
        step_lower = step.lower()

        # Search-related steps
        if 'search' in step_lower or 'find' in step_lower:
            # Extract search pattern from step
            pattern = self._extract_pattern_from_step(step, task)
            return AgentAction(
                action_type='search_files',
                parameters={'pattern': pattern, 'file_glob': '**/*.py'},
                reasoning=f"Searching for: {pattern}"
            )

        # Read-related steps
        elif 'read' in step_lower or 'understand' in step_lower or 'analyze' in step_lower:
            # Find relevant file from previous actions or task description
            file_path = self._find_relevant_file(task)
            if file_path:
                return AgentAction(
                    action_type='read_file',
                    parameters={'path': file_path},
                    reasoning=f"Reading file to understand: {file_path}"
                )

        # Write/Create steps
        elif 'write' in step_lower or 'create' in step_lower or 'implement' in step_lower:
            # Determine file path and content
            file_path = self._determine_file_path(task)
            content = self._generate_code_content(task, step)

            if file_path and content:
                return AgentAction(
                    action_type='write_file',
                    parameters={'path': file_path, 'content': content},
                    reasoning=f"Creating new implementation in: {file_path}"
                )

        # Test steps
        elif 'test' in step_lower:
            return AgentAction(
                action_type='run_command',
                parameters={'command': 'python -m pytest -v'},
                reasoning="Running tests to validate changes"
            )

        # List/explore steps
        elif 'identify' in step_lower or 'list' in step_lower:
            return AgentAction(
                action_type='list_files',
                parameters={'directory': 'src', 'pattern': '*.py'},
                reasoning="Listing Python files in src/"
            )

        return None

    def _extract_pattern_from_step(self, step: str, task: CodingTask) -> str:
        """Extract search pattern from step description."""
        # Try to extract class/function names from task description
        task_words = re.findall(r'\b[A-Z][a-zA-Z]*\b', task.description)
        if task_words:
            return task_words[0]

        # Default to generic patterns
        if 'class' in step.lower():
            return 'class '
        elif 'function' in step.lower():
            return 'def '
        else:
            return 'import'

    def _find_relevant_file(self, task: CodingTask) -> Optional[str]:
        """Find relevant file from previous actions or task description."""
        # Check previous search results
        for action in reversed(self.action_history):
            if action.action_type == 'search_files' and action.result:
                results = action.result.get('results', [])
                if results:
                    return results[0]['file_path']

        # Extract file path from task description
        words = task.description.split()
        for word in words:
            if word.endswith('.py'):
                return word

        # Default to main files
        common_files = ['src/self_coder.py', 'src/generic_router.py', 'main.py']
        for f in common_files:
            if os.path.exists(os.path.join(self.workspace_root, f)):
                return f

        return None

    def _determine_file_path(self, task: CodingTask) -> Optional[str]:
        """Determine file path for new code."""
        # Extract from task description
        words = task.description.split()
        for word in words:
            if word.endswith('.py'):
                return word

        # Generate based on task type
        if 'test' in task.description.lower():
            return 'tests/test_new_feature.py'
        elif 'agent' in task.description.lower() or 'coder' in task.description.lower():
            return 'src/new_agent_feature.py'
        else:
            return 'src/new_module.py'

    def _generate_code_content(self, task: CodingTask, step: str) -> str:
        """Generate code content for task."""
        # This would call the LLM in production
        # For now, return a template
        return f'''#!/usr/bin/env python3
"""
{task.description}
"""

def main():
    """Main implementation."""
    pass


if __name__ == "__main__":
    main()
'''

    def interactive_session(self):
        """
        Start an interactive coding session.
        User can give commands and agent autonomously executes them.
        """
        print("=== Self-Coding Agent - Interactive Session ===")
        print(f"Workspace: {self.workspace_root}")
        print("Type 'help' for commands, 'exit' to quit\n")

        while True:
            try:
                user_input = input(">>> ").strip()

                if not user_input:
                    continue

                if user_input.lower() == 'exit':
                    break

                if user_input.lower() == 'help':
                    self._print_help()
                    continue

                if user_input.lower() == 'status':
                    self._print_status()
                    continue

                if user_input.lower() == 'history':
                    self._print_history()
                    continue

                # Treat as coding task
                result = self.autonomous_code(user_input)

                print(f"\n{'='*50}")
                if result['success']:
                    print(f"✓ Task completed successfully")
                else:
                    print(f"✗ Task failed or incomplete")
                print(f"Actions taken: {result['actions_taken']}")
                print(f"Iterations: {result['iterations']}")
                print(f"{'='*50}\n")

            except KeyboardInterrupt:
                print("\n\nInterrupted. Type 'exit' to quit.\n")
            except Exception as e:
                print(f"Error: {e}\n")

    def _print_help(self):
        """Print help message."""
        print("""
Available commands:
  help      - Show this help
  status    - Show current tasks and status
  history   - Show action history
  exit      - Exit the session

Or describe a coding task in natural language, e.g.:
  - "Add a new function to calculate fibonacci numbers"
  - "Fix the bug in the authentication module"
  - "Refactor the database connection code"
        """)

    def _print_status(self):
        """Print current status."""
        print(f"\nWorkspace: {self.workspace_root}")
        print(f"Total tasks: {len(self.tasks)}")
        print(f"Actions taken: {len(self.action_history)}")

        if self.tasks:
            print("\nRecent tasks:")
            for task in self.tasks[-5:]:
                status_symbol = {
                    TaskStatus.COMPLETED: "✓",
                    TaskStatus.IN_PROGRESS: "⋯",
                    TaskStatus.FAILED: "✗",
                    TaskStatus.PENDING: "○"
                }.get(task.status, "?")
                print(f"  {status_symbol} {task.description[:60]}")

    def _print_history(self):
        """Print action history."""
        if not self.action_history:
            print("No actions taken yet.")
            return

        print(f"\nAction history (last 10):")
        for action in self.action_history[-10:]:
            print(f"  {action.action_type}: {action.reasoning[:50]}")
            if action.result and "error" in action.result:
                print(f"    ✗ {action.result['error']}")
