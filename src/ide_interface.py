#!/usr/bin/env python3
"""
IDE Interface for Self-Coding Agent
Textual-based TUI providing an IDE-like experience.
"""

import os
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import (
    Header, Footer, Static, Button, Input, TextArea,
    DirectoryTree, Label, ListView, ListItem, TabbedContent,
    TabPane, DataTable, Log, RichLog
)
from textual.binding import Binding
from textual.reactive import reactive
from textual import events
from textual.screen import Screen
from rich.syntax import Syntax
from rich.text import Text
from rich.panel import Panel

from .self_coder import SelfCodingAgent, TaskStatus, AgentAction


class FileExplorer(DirectoryTree):
    """File explorer tree view."""

    def __init__(self, root_path: str, **kwargs):
        super().__init__(root_path, **kwargs)
        self.root_path = root_path


class CodeEditor(VerticalScroll):
    """Code editor panel with syntax highlighting."""

    current_file = reactive(None)
    content = reactive("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text_area = None

    def compose(self) -> ComposeResult:
        yield Static("", id="editor-header")
        yield Static("", id="editor-content")

    def load_file(self, file_path: str):
        """Load file into editor."""
        self.current_file = file_path
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.content = f.read()

            # Get file extension for syntax highlighting
            ext = os.path.splitext(file_path)[1]
            lexer_map = {
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
            lexer = lexer_map.get(ext, 'text')

            # Update header
            header = self.query_one("#editor-header", Static)
            header.update(f"📄 {file_path}")

            # Update content with syntax highlighting
            content_widget = self.query_one("#editor-content", Static)
            syntax = Syntax(self.content, lexer, theme="monokai", line_numbers=True)
            content_widget.update(syntax)

        except Exception as e:
            self.notify(f"Error loading file: {e}", severity="error")

    def save_file(self):
        """Save current file."""
        if self.current_file:
            try:
                with open(self.current_file, 'w', encoding='utf-8') as f:
                    f.write(self.content)
                self.notify(f"Saved: {self.current_file}", severity="information")
            except Exception as e:
                self.notify(f"Error saving: {e}", severity="error")


class TaskPanel(VerticalScroll):
    """Panel displaying coding tasks."""

    def __init__(self, agent: SelfCodingAgent, **kwargs):
        super().__init__(**kwargs)
        self.agent = agent

    def compose(self) -> ComposeResult:
        yield Label("📋 Coding Tasks")
        yield ListView(id="task-list")

    def refresh_tasks(self):
        """Refresh task list."""
        task_list = self.query_one("#task-list", ListView)
        task_list.clear()

        for task in self.agent.tasks:
            status_symbol = {
                TaskStatus.COMPLETED: "✓",
                TaskStatus.IN_PROGRESS: "⋯",
                TaskStatus.FAILED: "✗",
                TaskStatus.PENDING: "○",
                TaskStatus.BLOCKED: "⊗"
            }.get(task.status, "?")

            item_text = f"{status_symbol} {task.description[:50]}"
            task_list.append(ListItem(Label(item_text)))


class TerminalPanel(VerticalScroll):
    """Terminal output panel."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.log = None

    def compose(self) -> ComposeResult:
        yield Label("💻 Terminal")
        yield RichLog(id="terminal-log", highlight=True, markup=True)

    def write(self, text: str, style: str = ""):
        """Write to terminal."""
        log = self.query_one("#terminal-log", RichLog)
        if style:
            log.write(Text(text, style=style))
        else:
            log.write(text)

    def clear(self):
        """Clear terminal."""
        log = self.query_one("#terminal-log", RichLog)
        log.clear()


class ActionHistoryPanel(VerticalScroll):
    """Panel showing agent action history."""

    def __init__(self, agent: SelfCodingAgent, **kwargs):
        super().__init__(**kwargs)
        self.agent = agent

    def compose(self) -> ComposeResult:
        yield Label("📊 Action History")
        yield DataTable(id="action-table")

    def on_mount(self):
        """Initialize table when mounted."""
        table = self.query_one("#action-table", DataTable)
        table.add_columns("Time", "Action", "Status")

    def refresh_actions(self):
        """Refresh action history."""
        table = self.query_one("#action-table", DataTable)
        table.clear()

        for action in self.agent.action_history[-20:]:  # Last 20 actions
            import time
            time_str = time.strftime("%H:%M:%S", time.localtime(action.timestamp))
            status = "✓" if action.result and "error" not in action.result else "✗"
            table.add_row(time_str, action.action_type, status)


class CommandInput(Container):
    """Command input area."""

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Type a coding task or command...", id="command-input")
        yield Button("Execute", variant="primary", id="execute-btn")


class IDEInterface(App):
    """
    Main IDE interface for the self-coding agent.

    Layout:
    ┌─────────────────────────────────────────┐
    │ Header                                  │
    ├─────────┬──────────────────┬───────────┤
    │  File   │   Code Editor    │  Tasks    │
    │  Tree   │                  │           │
    │         │                  │  Actions  │
    ├─────────┴──────────────────┴───────────┤
    │  Terminal                               │
    ├─────────────────────────────────────────┤
    │  Command Input                          │
    ├─────────────────────────────────────────┤
    │ Footer                                  │
    └─────────────────────────────────────────┘
    """

    CSS = """
    Screen {
        layout: grid;
        grid-size: 3 5;
        grid-rows: auto 2fr 1fr auto auto;
    }

    Header {
        column-span: 3;
        background: $primary;
    }

    #file-explorer {
        row-span: 2;
        border: solid $primary;
        width: 30;
    }

    #code-editor {
        row-span: 2;
        border: solid $secondary;
        padding: 1;
    }

    #side-panel {
        row-span: 2;
        layout: vertical;
        width: 40;
    }

    #task-panel {
        height: 50%;
        border: solid $accent;
    }

    #action-panel {
        height: 50%;
        border: solid $accent;
    }

    #terminal-panel {
        column-span: 3;
        border: solid $warning;
        height: 15;
    }

    #command-area {
        column-span: 3;
        layout: horizontal;
        height: auto;
        padding: 1;
        background: $panel;
    }

    #command-input {
        width: 1fr;
    }

    #execute-btn {
        width: auto;
        margin-left: 1;
    }

    Footer {
        column-span: 3;
        background: $primary;
    }

    Label {
        padding: 1;
        background: $boost;
        text-style: bold;
    }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+o", "open_file", "Open"),
        Binding("ctrl+s", "save_file", "Save"),
        Binding("ctrl+r", "run_task", "Run"),
        Binding("ctrl+l", "clear_terminal", "Clear"),
        Binding("f1", "show_help", "Help"),
    ]

    def __init__(self, workspace_root: str = None, **kwargs):
        super().__init__(**kwargs)
        self.workspace_root = workspace_root or os.getcwd()
        self.agent = SelfCodingAgent(self.workspace_root)

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header(show_clock=True)

        # File explorer
        yield FileExplorer(self.workspace_root, id="file-explorer")

        # Code editor
        yield CodeEditor(id="code-editor")

        # Side panel with tasks and actions
        with Vertical(id="side-panel"):
            yield TaskPanel(self.agent, id="task-panel")
            yield ActionHistoryPanel(self.agent, id="action-panel")

        # Terminal
        yield TerminalPanel(id="terminal-panel")

        # Command input
        with Container(id="command-area"):
            yield Input(placeholder="Type a coding task or command...", id="command-input")
            yield Button("Execute", variant="primary", id="execute-btn")

        yield Footer()

    def on_mount(self):
        """Initialize when app mounts."""
        self.title = "SWORD Self-Coding IDE"
        self.sub_title = f"Workspace: {self.workspace_root}"

        # Welcome message
        terminal = self.query_one("#terminal-panel", TerminalPanel)
        terminal.write("=== SWORD Self-Coding IDE ===", style="bold blue")
        terminal.write(f"Workspace: {self.workspace_root}")
        terminal.write("Type a coding task or command below")
        terminal.write("Press F1 for help\n")

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected):
        """Handle file selection in tree."""
        editor = self.query_one("#code-editor", CodeEditor)
        editor.load_file(str(event.path))

    def on_button_pressed(self, event: Button.Pressed):
        """Handle button presses."""
        if event.button.id == "execute-btn":
            self.execute_command()

    def on_input_submitted(self, event: Input.Submitted):
        """Handle input submission."""
        if event.input.id == "command-input":
            self.execute_command()

    def execute_command(self):
        """Execute command from input."""
        input_widget = self.query_one("#command-input", Input)
        command = input_widget.value.strip()

        if not command:
            return

        input_widget.value = ""

        terminal = self.query_one("#terminal-panel", TerminalPanel)
        terminal.write(f"\n>>> {command}", style="bold cyan")

        # Handle special commands
        if command.lower() == "help":
            self.action_show_help()
            return
        elif command.lower() == "clear":
            self.action_clear_terminal()
            return
        elif command.lower() == "status":
            self.show_status()
            return

        # Execute as coding task
        terminal.write("🤖 Agent is working...", style="yellow")

        # Run agent in background
        asyncio.create_task(self.run_agent_task(command))

    async def run_agent_task(self, task_description: str):
        """Run agent task asynchronously."""
        terminal = self.query_one("#terminal-panel", TerminalPanel)

        try:
            # Run in executor to avoid blocking
            result = await asyncio.to_thread(
                self.agent.autonomous_code,
                task_description
            )

            if result['success']:
                terminal.write("✓ Task completed successfully", style="bold green")
            else:
                terminal.write("✗ Task failed or incomplete", style="bold red")

            terminal.write(f"Actions taken: {result['actions_taken']}")
            terminal.write(f"Iterations: {result['iterations']}")

            # Refresh panels
            self.refresh_panels()

        except Exception as e:
            terminal.write(f"Error: {e}", style="bold red")

    def refresh_panels(self):
        """Refresh all panels."""
        task_panel = self.query_one("#task-panel", TaskPanel)
        task_panel.refresh_tasks()

        action_panel = self.query_one("#action-panel", ActionHistoryPanel)
        action_panel.refresh_actions()

    def show_status(self):
        """Show agent status."""
        terminal = self.query_one("#terminal-panel", TerminalPanel)
        terminal.write(f"\n📊 Status:")
        terminal.write(f"  Workspace: {self.workspace_root}")
        terminal.write(f"  Total tasks: {len(self.agent.tasks)}")
        terminal.write(f"  Actions taken: {len(self.agent.action_history)}")

    def action_quit(self):
        """Quit the application."""
        self.exit()

    def action_open_file(self):
        """Open file dialog."""
        self.notify("Open file dialog (not implemented)", severity="information")

    def action_save_file(self):
        """Save current file."""
        editor = self.query_one("#code-editor", CodeEditor)
        editor.save_file()

    def action_run_task(self):
        """Focus command input."""
        input_widget = self.query_one("#command-input", Input)
        input_widget.focus()

    def action_clear_terminal(self):
        """Clear terminal."""
        terminal = self.query_one("#terminal-panel", TerminalPanel)
        terminal.clear()

    def action_show_help(self):
        """Show help."""
        terminal = self.query_one("#terminal-panel", TerminalPanel)
        terminal.write("\n📖 Help:", style="bold blue")
        terminal.write("  Ctrl+Q - Quit")
        terminal.write("  Ctrl+O - Open file")
        terminal.write("  Ctrl+S - Save file")
        terminal.write("  Ctrl+R - Run task")
        terminal.write("  Ctrl+L - Clear terminal")
        terminal.write("  F1 - Show help")
        terminal.write("\nCommands:")
        terminal.write("  help - Show this help")
        terminal.write("  status - Show agent status")
        terminal.write("  clear - Clear terminal")
        terminal.write("\nOr describe a coding task:")
        terminal.write("  'Add a function to calculate fibonacci'")
        terminal.write("  'Fix the bug in authentication module'")


def run_ide(workspace_root: str = None):
    """Run the IDE interface."""
    app = IDEInterface(workspace_root)
    app.run()


if __name__ == "__main__":
    import sys
    workspace = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    run_ide(workspace)
