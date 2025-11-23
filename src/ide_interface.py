#!/usr/bin/env python3
"""
IDE Interface for Self-Coding Agent
Enhanced Textual-based TUI providing a full IDE experience.
"""

import os
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll, ScrollableContainer
from textual.widgets import (
    Header, Footer, Static, Button, Input, TextArea,
    DirectoryTree, Label, Tree, TabbedContent,
    TabPane, DataTable, RichLog, Placeholder, ProgressBar
)
from textual.binding import Binding
from textual.reactive import reactive
from textual import events, on
from textual.screen import ModalScreen
from rich.syntax import Syntax
from rich.text import Text
from rich.panel import Panel
from rich.table import Table as RichTable

from .self_coder import SelfCodingAgent, TaskStatus, AgentAction
from .codebreaker import (
    ascii_preview,
    compute_ai_power,
    decode_base64_payload,
    format_ai_devices,
    hex_preview,
    load_ai_devices,
    benchmark_simon_speck,
    guess_encryption_profile,
    optimize_for_devices,
    select_devices,
    DEFAULT_HARDWARE_CONFIG,
    DEFAULT_PAYLOAD,
    DEFAULT_SUPERCOP_PATH,
)


class StatusBar(Static):
    """Enhanced status bar showing file info, position, etc."""

    current_file = reactive("")
    file_size = reactive(0)
    line_count = reactive(0)
    cursor_line = reactive(1)
    cursor_col = reactive(1)
    language = reactive("")
    modified = reactive(False)

    def render(self) -> Text:
        """Render status bar."""
        text = Text()

        # File info
        if self.current_file:
            filename = os.path.basename(self.current_file)
            text.append(f" {filename}", style="bold cyan")
            if self.modified:
                text.append(" [Modified]", style="yellow")
            text.append(f" | {self.language}", style="dim")
        else:
            text.append(" No file open", style="dim")

        # Separator
        text.append(" " * 10)

        # Position info
        text.append(f"Ln {self.cursor_line}, Col {self.cursor_col}", style="green")
        text.append(f" | {self.line_count} lines", style="dim")

        # Size info
        if self.file_size > 0:
            if self.file_size < 1024:
                size_str = f"{self.file_size} B"
            elif self.file_size < 1024 * 1024:
                size_str = f"{self.file_size / 1024:.1f} KB"
            else:
                size_str = f"{self.file_size / (1024 * 1024):.1f} MB"
            text.append(f" | {size_str}", style="dim")

        return text


class EditableCodeEditor(Container):
    """Enhanced code editor with editing capabilities."""

    current_file = reactive(None)
    modified = reactive(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.content = ""
        self.language = "text"

    def compose(self) -> ComposeResult:
        """Create editor components."""
        yield Static("", id="editor-header", classes="editor-header")
        yield TextArea("", language="python", theme="monokai", id="text-editor", show_line_numbers=True)

    def on_mount(self):
        """Setup editor on mount."""
        editor = self.query_one("#text-editor", TextArea)
        editor.focus()

    def load_file(self, file_path: str):
        """Load file into editor."""
        self.current_file = file_path
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.content = f.read()

            # Get file extension for syntax highlighting
            ext = os.path.splitext(file_path)[1]
            language_map = {
                '.py': 'python',
                '.js': 'javascript',
                '.ts': 'typescript',
                '.tsx': 'tsx',
                '.jsx': 'jsx',
                '.cpp': 'cpp',
                '.c': 'c',
                '.h': 'c',
                '.hpp': 'cpp',
                '.java': 'java',
                '.go': 'go',
                '.rs': 'rust',
                '.sh': 'bash',
                '.yaml': 'yaml',
                '.yml': 'yaml',
                '.json': 'json',
                '.md': 'markdown',
                '.html': 'html',
                '.css': 'css',
                '.sql': 'sql',
                '.toml': 'toml',
            }
            self.language = language_map.get(ext, 'text')

            # Update header
            header = self.query_one("#editor-header", Static)
            rel_path = os.path.relpath(file_path)
            header.update(f"📄 {rel_path}")

            # Update editor
            editor = self.query_one("#text-editor", TextArea)
            editor.language = self.language
            editor.load_text(self.content)
            editor.focus()

            self.modified = False

        except Exception as e:
            self.app.notify(f"Error loading file: {e}", severity="error")

    def save_file(self) -> bool:
        """Save current file."""
        if not self.current_file:
            self.app.notify("No file to save", severity="warning")
            return False

        try:
            editor = self.query_one("#text-editor", TextArea)
            content = editor.text

            with open(self.current_file, 'w', encoding='utf-8') as f:
                f.write(content)

            self.content = content
            self.modified = False
            self.app.notify(f"Saved: {os.path.basename(self.current_file)}", severity="information")
            return True
        except Exception as e:
            self.app.notify(f"Error saving: {e}", severity="error")
            return False

    def on_text_area_changed(self, event: TextArea.Changed):
        """Track modifications."""
        if self.current_file:
            editor = self.query_one("#text-editor", TextArea)
            self.modified = (editor.text != self.content)


class FileTabPane(TabPane):
    """Tab pane for an open file."""

    def __init__(self, title: str, file_path: str, **kwargs):
        super().__init__(title, **kwargs)
        self.file_path = file_path


class TabbedEditor(Container):
    """Tabbed interface for multiple open files."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.open_files: Dict[str, EditableCodeEditor] = {}
        self.active_file = None

    def compose(self) -> ComposeResult:
        """Create tabbed content."""
        with TabbedContent(id="editor-tabs"):
            with TabPane("Welcome", id="welcome-tab"):
                yield Label("📝 SWORD Self-Coding IDE", classes="welcome-title")
                yield Label("\nPress Ctrl+O to open a file or click a file in the tree", classes="welcome-text")
                yield Label("Press Ctrl+N for new file", classes="welcome-text")
                yield Label("Press F1 for help", classes="welcome-text")

    def open_file(self, file_path: str):
        """Open file in new tab."""
        # Check if already open
        if file_path in self.open_files:
            # Switch to that tab
            tabs = self.query_one("#editor-tabs", TabbedContent)
            tabs.active = f"tab-{file_path}"
            return

        # Create new editor
        editor = EditableCodeEditor()
        editor.load_file(file_path)

        # Create tab
        tabs = self.query_one("#editor-tabs", TabbedContent)
        filename = os.path.basename(file_path)

        # Add tab pane
        tab_pane = FileTabPane(filename, file_path, id=f"tab-{file_path}")
        tab_pane.mount(editor)
        tabs.add_pane(tab_pane)

        # Store reference
        self.open_files[file_path] = editor
        self.active_file = file_path

        # Switch to new tab
        tabs.active = f"tab-{file_path}"

    def save_current(self) -> bool:
        """Save currently active file."""
        if self.active_file and self.active_file in self.open_files:
            return self.open_files[self.active_file].save_file()
        return False

    def close_current(self):
        """Close currently active tab."""
        if self.active_file and self.active_file in self.open_files:
            # Check if modified
            editor = self.open_files[self.active_file]
            if editor.modified:
                # TODO: Show confirmation dialog
                pass

            # Remove tab
            tabs = self.query_one("#editor-tabs", TabbedContent)
            tabs.remove_pane(f"tab-{self.active_file}")

            # Remove from open files
            del self.open_files[self.active_file]
            self.active_file = None


class SearchModal(ModalScreen):
    """Modal for search/replace functionality."""

    CSS = """
    SearchModal {
        align: center middle;
    }

    #search-dialog {
        width: 60;
        height: 15;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    #search-input, #replace-input {
        margin: 1 0;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="search-dialog"):
            yield Label("🔍 Search and Replace", classes="dialog-title")
            yield Input(placeholder="Search for...", id="search-input")
            yield Input(placeholder="Replace with...", id="replace-input")
            with Horizontal():
                yield Button("Find", variant="primary", id="find-btn")
                yield Button("Replace", variant="default", id="replace-btn")
                yield Button("Replace All", variant="default", id="replace-all-btn")
                yield Button("Cancel", variant="default", id="cancel-btn")

    @on(Button.Pressed, "#find-btn")
    def find(self):
        search_input = self.query_one("#search-input", Input)
        self.dismiss({"action": "find", "text": search_input.value})

    @on(Button.Pressed, "#replace-btn")
    def replace(self):
        search_input = self.query_one("#search-input", Input)
        replace_input = self.query_one("#replace-input", Input)
        self.dismiss({
            "action": "replace",
            "search": search_input.value,
            "replace": replace_input.value
        })

    @on(Button.Pressed, "#replace-all-btn")
    def replace_all(self):
        search_input = self.query_one("#search-input", Input)
        replace_input = self.query_one("#replace-input", Input)
        self.dismiss({
            "action": "replace_all",
            "search": search_input.value,
            "replace": replace_input.value
        })

    @on(Button.Pressed, "#cancel-btn")
    def cancel(self):
        self.dismiss(None)


class CommandPalette(ModalScreen):
    """Command palette for quick actions."""

    CSS = """
    CommandPalette {
        align: center top;
    }

    #palette-dialog {
        width: 80;
        height: 25;
        border: thick $accent;
        background: $surface;
        padding: 1;
        margin-top: 3;
    }
    """

    COMMANDS = [
        ("Open File", "open_file", "Ctrl+O"),
        ("Save File", "save_file", "Ctrl+S"),
        ("Close File", "close_file", "Ctrl+W"),
        ("New File", "new_file", "Ctrl+N"),
        ("Search", "search", "Ctrl+F"),
        ("Run Task", "run_task", "Ctrl+R"),
        ("Clear Terminal", "clear_terminal", "Ctrl+L"),
        ("Show Tasks", "show_tasks", "F2"),
        ("Show Actions", "show_actions", "F3"),
        ("Agent Status", "agent_status", "F4"),
        ("Git Status", "git_status", "F5"),
        ("Codebreaker", "codebreaker", "F6"),
        ("Help", "help", "F1"),
        ("Quit", "quit", "Ctrl+Q"),
    ]

    def compose(self) -> ComposeResult:
        with Container(id="palette-dialog"):
            yield Label("⌨️  Command Palette", classes="dialog-title")
            yield Input(placeholder="Type to filter commands...", id="palette-input")
            yield DataTable(id="command-table", cursor_type="row")

    def on_mount(self):
        """Setup command table."""
        table = self.query_one("#command-table", DataTable)
        table.add_columns("Command", "Shortcut")

        for cmd, action, shortcut in self.COMMANDS:
            table.add_row(cmd, shortcut)

        table.focus()

    def on_input_changed(self, event: Input.Changed):
        """Filter commands."""
        filter_text = event.value.lower()
        table = self.query_one("#command-table", DataTable)
        table.clear()

        for cmd, action, shortcut in self.COMMANDS:
            if filter_text in cmd.lower():
                table.add_row(cmd, shortcut)

    def on_data_table_row_selected(self, event: DataTable.RowSelected):
        """Execute selected command."""
        row_index = event.cursor_row
        if 0 <= row_index < len(self.COMMANDS):
            _, action, _ = self.COMMANDS[row_index]
            self.dismiss(action)


class CodebreakerModal(ModalScreen):
    """Modal that runs codebreaker analysis with progress feedback."""

    CSS = """
    CodebreakerModal {
        align: center middle;
    }

    #codebreaker-dialog {
        width: 90;
        height: 30;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }

    #codebreaker-progress {
        margin: 1 0;
    }
    """

    def __init__(
        self,
        payload: str,
        hardware_path: Path,
        selected_devices: list[str] | None = None,
        benchmark_crypto: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.payload = payload or DEFAULT_PAYLOAD
        self.hardware_path = hardware_path
        self.selected_devices = selected_devices or []
        self.benchmark_crypto = benchmark_crypto

    def compose(self) -> ComposeResult:
        with Container(id="codebreaker-dialog"):
            yield Label("🧨 Codebreaker Analysis", classes="dialog-title")
            yield ProgressBar(total=100, id="codebreaker-progress")
            yield RichLog(id="codebreaker-log", highlight=True, markup=True)
            with Horizontal():
                yield Button("Close", variant="primary", id="close-codebreaker")

    async def on_mount(self):
        self.call_later(self.run_analysis)

    async def run_analysis(self):
        progress = self.query_one("#codebreaker-progress", ProgressBar)
        log = self.query_one("#codebreaker-log", RichLog)

        def update_progress(value: int, message: str, style: str = "cyan"):
            progress.update(value=min(value, 100))
            log.write(f"[{style}]{message}[/]")

        update_progress(5, "Initializing codebreaker stack…")
        await asyncio.sleep(0.05)

        decoded, warnings = decode_base64_payload(self.payload)
        enc_profile, sentence_like = guess_encryption_profile(decoded)
        update_progress(30, f"Decoded payload: {len(decoded)} bytes (input {len(self.payload)} chars)")
        for warning in warnings:
            log.write(f"[yellow]Warning:[/] {warning}")

        if decoded:
            update_progress(45, "Generating previews…")
            log.write(f"[green]Hex:[/] {hex_preview(decoded)}")
            log.write(f"[green]ASCII:[/] {ascii_preview(decoded)}")
        else:
            log.write("[red]No decoded bytes available.[/]")

        update_progress(55, "Loading AI device inventory…")
        accelerators = load_ai_devices(self.hardware_path)
        if not accelerators:
            log.write(f"[red]No accelerators found at {self.hardware_path}.[/]")
            progress.update(value=100)
            return

        normalized_keys = [key.strip() for key in self.selected_devices if key and key.strip()]
        use_all_devices = any(k.lower() in {"all", "*"} for k in normalized_keys)
        scoped_accelerators, missing = select_devices(
            accelerators, normalized_keys if not use_all_devices else []
        )
        selection_label = ", ".join(normalized_keys) if normalized_keys else "all"
        log.write(f"[cyan]Selection:[/] {selection_label}")
        if missing:
            log.write(f"[yellow]Missing requested devices:[/] {', '.join(missing)}")

        if not scoped_accelerators:
            log.write("[red]No accelerators match the provided selection.[/]")
            progress.update(value=100)
            return

        power = compute_ai_power(scoped_accelerators)
        if power.get("total_tops"):
            log.write(
                f"[magenta]Aggregate:[/] {power['total_tops']:.1f} TOPS across {power['device_count']} entries"
            )
        if power.get("strongest_device"):
            log.write(f"[magenta]Lead device:[/] {power['strongest_device']}")

        update_progress(70, "Enumerating accelerators…")
        for line in format_ai_devices(scoped_accelerators):
            log.write(line)

        if self.benchmark_crypto:
            update_progress(85, "Running Simon/Speck SUPERCOP benchmark…")
            bench_log, bench_warn = await asyncio.to_thread(
                benchmark_simon_speck, scoped_accelerators, DEFAULT_SUPERCOP_PATH
            )
            for entry in bench_log:
                log.write(f"[cyan]- {entry}[/]")
            for warn in bench_warn:
                log.write(f"[yellow]Warning:[/] {warn}")
        else:
            update_progress(80, "Optimizing selection…")
        for line in optimize_for_devices(scoped_accelerators):
            log.write(f"[cyan]- {line}[/]")

        update_progress(95, "Final classification…")
        sentence_flag = "yes" if sentence_like else "no"
        tops_msg = (
            f"{power['total_tops']:.1f} TOPS engaged" if power.get("total_tops") else "TOPS unavailable"
        )
        log.write(f"[green]Encryption type guess:[/] {enc_profile}")
        log.write(f"[green]Sentence-like payload:[/] {sentence_flag}")
        log.write(f"[green]TOPS utilization estimate:[/] {tops_msg}")

        update_progress(100, "Codebreaker complete — all AI power accounted for.", style="green")
        log.write("[dim]Press Close or Esc to return.[/dim]")

    @on(Button.Pressed, "#close-codebreaker")
    def close_modal(self):
        self.dismiss()


class TaskPanel(ScrollableContainer):
    """Panel displaying coding tasks."""

    def __init__(self, agent: SelfCodingAgent, **kwargs):
        super().__init__(**kwargs)
        self.agent = agent

    def compose(self) -> ComposeResult:
        yield Label("📋 Tasks", classes="panel-title")
        yield DataTable(id="task-table", show_cursor=False)

    def on_mount(self):
        """Initialize task table."""
        table = self.query_one("#task-table", DataTable)
        table.add_columns("Status", "Task", "Priority")
        self.refresh_tasks()

    def refresh_tasks(self):
        """Refresh task list."""
        table = self.query_one("#task-table", DataTable)
        table.clear()

        for task in self.agent.tasks:
            status_symbol = {
                TaskStatus.COMPLETED: "✓",
                TaskStatus.IN_PROGRESS: "⋯",
                TaskStatus.FAILED: "✗",
                TaskStatus.PENDING: "○",
                TaskStatus.BLOCKED: "⊗"
            }.get(task.status, "?")

            task_desc = task.description[:40] + "..." if len(task.description) > 40 else task.description
            table.add_row(status_symbol, task_desc, str(task.priority))


class ActionHistoryPanel(ScrollableContainer):
    """Panel showing agent action history."""

    def __init__(self, agent: SelfCodingAgent, **kwargs):
        super().__init__(**kwargs)
        self.agent = agent

    def compose(self) -> ComposeResult:
        yield Label("📊 Actions", classes="panel-title")
        yield DataTable(id="action-table", show_cursor=False)

    def on_mount(self):
        """Initialize action table."""
        table = self.query_one("#action-table", DataTable)
        table.add_columns("Time", "Action", "Status")
        self.refresh_actions()

    def refresh_actions(self):
        """Refresh action history."""
        table = self.query_one("#action-table", DataTable)
        table.clear()

        for action in self.agent.action_history[-20:]:  # Last 20 actions
            time_str = datetime.fromtimestamp(action.timestamp).strftime("%H:%M:%S")
            status = "✓" if action.result and "error" not in action.result else "✗"
            action_type = action.action_type[:15]
            table.add_row(time_str, action_type, status)


class TerminalPanel(ScrollableContainer):
    """Terminal output panel."""

    def compose(self) -> ComposeResult:
        yield Label("💻 Terminal", classes="panel-title")
        yield RichLog(id="terminal-log", highlight=True, markup=True)

    def write(self, text: str, style: str = ""):
        """Write to terminal."""
        log = self.query_one("#terminal-log", RichLog)
        timestamp = datetime.now().strftime("%H:%M:%S")
        if style:
            log.write(f"[dim]{timestamp}[/dim] {Text(text, style=style)}")
        else:
            log.write(f"[dim]{timestamp}[/dim] {text}")

    def clear(self):
        """Clear terminal."""
        log = self.query_one("#terminal-log", RichLog)
        log.clear()


class IDEInterface(App):
    """
    Enhanced IDE interface for self-coding agent.

    Features:
    - Editable code editor with syntax highlighting
    - Tabbed interface for multiple files
    - File explorer
    - Terminal panel
    - Task and action tracking
    - Command palette
    - Search/replace
    - Status bar
    """

    CSS = """
    Screen {
        background: $background;
    }

    .panel-title {
        background: $boost;
        color: $text;
        padding: 0 1;
        text-style: bold;
    }

    .welcome-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin: 2 0;
    }

    .welcome-text {
        text-align: center;
        color: $text-muted;
    }

    .editor-header {
        background: $primary;
        padding: 0 1;
        color: $text;
    }

    #file-explorer {
        width: 30;
        border-right: solid $primary;
        background: $surface;
    }

    #main-area {
        width: 1fr;
    }

    #editor-area {
        height: 2fr;
        border: solid $secondary;
    }

    #side-panels {
        width: 35;
        border-left: solid $primary;
    }

    #task-panel {
        height: 1fr;
        border-bottom: solid $accent;
    }

    #action-panel {
        height: 1fr;
        border-bottom: solid $accent;
    }

    #terminal-panel {
        height: 1fr;
        border-top: solid $warning;
    }

    #command-area {
        height: auto;
        background: $panel;
        padding: 1;
    }

    #command-input {
        width: 1fr;
    }

    #execute-btn {
        width: auto;
        margin-left: 1;
    }

    StatusBar {
        background: $primary;
        color: $text;
        height: 1;
        padding: 0 1;
    }

    Button {
        margin: 0 1;
    }

    .dialog-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+o", "open_file", "Open"),
        Binding("ctrl+n", "new_file", "New"),
        Binding("ctrl+s", "save_file", "Save"),
        Binding("ctrl+w", "close_file", "Close"),
        Binding("ctrl+f", "search", "Search"),
        Binding("ctrl+r", "run_task", "Run Task"),
        Binding("ctrl+l", "clear_terminal", "Clear"),
        Binding("ctrl+p", "command_palette", "Palette"),
        Binding("f1", "show_help", "Help"),
        Binding("f2", "focus_tasks", "Tasks"),
        Binding("f3", "focus_actions", "Actions"),
        Binding("f4", "agent_status", "Status"),
        Binding("f5", "git_status", "Git"),
        Binding("f6", "codebreaker", "Codebreaker"),
    ]

    def __init__(self, workspace_root: str = None, **kwargs):
        super().__init__(**kwargs)
        self.workspace_root = workspace_root or os.getcwd()
        self.agent = SelfCodingAgent(self.workspace_root)
        self.hardware_config_path = Path(DEFAULT_HARDWARE_CONFIG)

        # Session management
        from .session_manager import SessionManager
        self.session_manager = SessionManager()
        self.current_session_id = None

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header(show_clock=True)

        with Horizontal():
            # Left: File explorer
            yield DirectoryTree(self.workspace_root, id="file-explorer")

            # Center: Main editing area
            with Vertical(id="main-area"):
                with Container(id="editor-area"):
                    yield TabbedEditor(id="tabbed-editor")

                # Terminal
                yield TerminalPanel(id="terminal-panel")

                # Command input
                with Horizontal(id="command-area"):
                    yield Input(placeholder="Type a coding task or command...", id="command-input")
                    yield Button("Execute", variant="primary", id="execute-btn")

            # Right: Side panels
            with Vertical(id="side-panels"):
                yield TaskPanel(self.agent, id="task-panel")
                yield ActionHistoryPanel(self.agent, id="action-panel")

        yield StatusBar()
        yield Footer()

    def on_mount(self):
        """Initialize when app mounts."""
        self.title = "SWORD Self-Coding IDE"
        self.sub_title = f"{self.workspace_root}"

        # Welcome message
        terminal = self.query_one("#terminal-panel", TerminalPanel)
        terminal.write("╔═══════════════════════════════════════════════════════╗", style="bold blue")
        terminal.write("║        SWORD Self-Coding IDE - Enhanced              ║", style="bold blue")
        terminal.write("╚═══════════════════════════════════════════════════════╝", style="bold blue")
        terminal.write(f"Workspace: {self.workspace_root}")
        terminal.write("Type a coding task below or use Ctrl+P for command palette")
        terminal.write("Press F1 for help\n")

    @on(DirectoryTree.FileSelected)
    def on_file_selected(self, event: DirectoryTree.FileSelected):
        """Handle file selection in tree."""
        tabbed_editor = self.query_one("#tabbed-editor", TabbedEditor)
        tabbed_editor.open_file(str(event.path))

        # Update status bar
        status_bar = self.query_one(StatusBar)
        status_bar.current_file = str(event.path)
        status_bar.language = os.path.splitext(str(event.path))[1][1:]

        try:
            stat = os.stat(event.path)
            status_bar.file_size = stat.st_size
            with open(event.path, 'r') as f:
                status_bar.line_count = sum(1 for _ in f)
        except:
            pass

    @on(Button.Pressed, "#execute-btn")
    def on_execute_pressed(self):
        """Handle execute button."""
        self.execute_command()

    @on(Input.Submitted, "#command-input")
    def on_command_submitted(self, event: Input.Submitted):
        """Handle command submission."""
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
        elif command.lower().startswith("open "):
            file_path = command[5:].strip()
            self.open_file_by_path(file_path)
            return
        elif command.lower() == "sessions":
            self.show_sessions()
            return
        elif command.lower().startswith("resume "):
            session_id = command[7:].strip()
            self.resume_session(session_id)
            return
        elif command.lower() == "save":
            self.save_current_session()
            return
        elif command.lower().startswith("codebreaker"):
            payload_override = None
            device_keys: list[str] = []
            benchmark_crypto = False

            parts = command.split(" ", 1)
            if len(parts) > 1:
                for token in parts[1].split():
                    if token.lower().startswith("payload="):
                        payload_override = token.split("=", 1)[1].strip() or None
                    elif token.lower().startswith("devices="):
                        device_keys = [k.strip() for k in token.split("=", 1)[1].split(",") if k.strip()]
                    elif token.lower() in {"bench", "benchmark", "supcop", "supercop"}:
                        benchmark_crypto = True
                    elif payload_override is None:
                        payload_override = token.strip()

            self.launch_codebreaker(payload_override, device_keys or None, benchmark_crypto)
            return
        elif command.lower().startswith("prompt:") or command.lower().startswith("llm:"):
            # Direct LLM prompting
            prompt = command.split(":", 1)[1].strip()
            asyncio.create_task(self.direct_llm_prompt(prompt))
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
        terminal.write(f"\n╔═══ Agent Status ═══╗", style="bold blue")
        terminal.write(f"  Workspace: {self.workspace_root}")
        terminal.write(f"  Total tasks: {len(self.agent.tasks)}")
        terminal.write(f"  Actions taken: {len(self.agent.action_history)}")
        terminal.write(f"╚═══════════════════╝", style="bold blue")

    def launch_codebreaker(
        self,
        payload: str | None = None,
        device_keys: list[str] | None = None,
        benchmark_crypto: bool = False,
    ):
        """Open the codebreaker modal with optional payload, device selection, and SUPERCOP benchmarking."""
        terminal = self.query_one("#terminal-panel", TerminalPanel)
        source = "custom payload" if payload else "default payload"
        selection = ", ".join(device_keys) if device_keys else "all devices"
        bench_label = "with SUPERCOP" if benchmark_crypto else "no benchmark"
        terminal.write(
            f"⚡ Launching codebreaker ({source}; selection: {selection}; {bench_label})…",
            style="magenta",
        )
        self.push_screen(
            CodebreakerModal(
                payload or DEFAULT_PAYLOAD,
                self.hardware_config_path,
                device_keys or [],
                benchmark_crypto,
            )
        )

    def action_codebreaker(self):
        """Trigger codebreaker analysis (F6)."""
        self.launch_codebreaker()

    def open_file_by_path(self, file_path: str):
        """Open file by path."""
        full_path = os.path.join(self.workspace_root, file_path)
        if os.path.exists(full_path):
            tabbed_editor = self.query_one("#tabbed-editor", TabbedEditor)
            tabbed_editor.open_file(full_path)
        else:
            self.notify(f"File not found: {file_path}", severity="error")

    def action_quit(self):
        """Quit the application."""
        self.exit()

    def action_open_file(self):
        """Open file (focus file tree)."""
        tree = self.query_one("#file-explorer", DirectoryTree)
        tree.focus()

    def action_new_file(self):
        """Create new file."""
        self.notify("New file (not yet implemented)", severity="information")

    def action_save_file(self):
        """Save current file."""
        tabbed_editor = self.query_one("#tabbed-editor", TabbedEditor)
        if tabbed_editor.save_current():
            status_bar = self.query_one(StatusBar)
            status_bar.modified = False

    def action_close_file(self):
        """Close current file."""
        tabbed_editor = self.query_one("#tabbed-editor", TabbedEditor)
        tabbed_editor.close_current()

    def action_search(self):
        """Show search dialog."""
        def handle_search(result):
            if result:
                terminal = self.query_one("#terminal-panel", TerminalPanel)
                terminal.write(f"Search: {result}", style="cyan")

        self.push_screen(SearchModal(), handle_search)

    def action_run_task(self):
        """Focus command input."""
        input_widget = self.query_one("#command-input", Input)
        input_widget.focus()

    def action_clear_terminal(self):
        """Clear terminal."""
        terminal = self.query_one("#terminal-panel", TerminalPanel)
        terminal.clear()

    def action_command_palette(self):
        """Show command palette."""
        def handle_command(action):
            if action:
                terminal = self.query_one("#terminal-panel", TerminalPanel)
                terminal.write(f"Command: {action}", style="cyan")
                # Execute the action
                if hasattr(self, f"action_{action}"):
                    getattr(self, f"action_{action}")()

        self.push_screen(CommandPalette(), handle_command)

    def action_show_help(self):
        """Show help."""
        terminal = self.query_one("#terminal-panel", TerminalPanel)
        terminal.write("\n╔═══ Keyboard Shortcuts ═══╗", style="bold blue")
        terminal.write("  Ctrl+Q     - Quit")
        terminal.write("  Ctrl+O     - Open file (focus tree)")
        terminal.write("  Ctrl+N     - New file")
        terminal.write("  Ctrl+S     - Save file")
        terminal.write("  Ctrl+W     - Close file")
        terminal.write("  Ctrl+F     - Search")
        terminal.write("  Ctrl+R     - Run task")
        terminal.write("  Ctrl+L     - Clear terminal")
        terminal.write("  Ctrl+P     - Command palette")
        terminal.write("  F1         - Help")
        terminal.write("  F2         - Focus tasks")
        terminal.write("  F3         - Focus actions")
        terminal.write("  F4         - Agent status")
        terminal.write("  F5         - Git status")
        terminal.write("  F6         - Codebreaker hardware check")
        terminal.write("\n╔═══ Commands ═══╗", style="bold blue")
        terminal.write("  help         - Show this help")
        terminal.write("  status       - Show agent status")
        terminal.write("  clear        - Clear terminal")
        terminal.write("  open PATH    - Open file by path")
        terminal.write("  sessions     - List saved sessions")
        terminal.write("  save         - Save current session")
        terminal.write("  resume ID    - Resume session by ID")
        terminal.write("  codebreaker [PAYLOAD] [devices=a,b] - Decode payload + optimize selection")
        terminal.write("  prompt: TEXT - Direct LLM prompting")
        terminal.write("  llm: TEXT    - Direct LLM prompting (alias)")
        terminal.write("\n╔═══ Coding Tasks ═══╗", style="bold blue")
        terminal.write("  Type natural language tasks:")
        terminal.write("  'Add a function to calculate fibonacci'")
        terminal.write("  'Fix the bug in authentication module'")
        terminal.write("  'Refactor database connection code'")
        terminal.write("\n╔═══ Direct Prompting ═══╗", style="bold blue")
        terminal.write("  prompt: What is a binary search tree?")
        terminal.write("  llm: Explain how async/await works")
        terminal.write("  llm: Write a quick sort algorithm")
        terminal.write("\n╔═══ Extended Context ═══╗", style="bold blue")
        terminal.write("  • 128K token context via 50GB RAM buffer")
        terminal.write("  • Sessions auto-save every 5 minutes")
        terminal.write("  • Resume sessions across restarts")
        terminal.write("╚══════════════════════════╝", style="bold blue")

    def action_focus_tasks(self):
        """Focus task panel."""
        task_panel = self.query_one("#task-panel", TaskPanel)
        task_panel.focus()

    def action_focus_actions(self):
        """Focus action panel."""
        action_panel = self.query_one("#action-panel", ActionHistoryPanel)
        action_panel.focus()

    def action_agent_status(self):
        """Show agent status."""
        self.show_status()

    def action_git_status(self):
        """Show git status."""
        terminal = self.query_one("#terminal-panel", TerminalPanel)
        try:
            import subprocess
            result = subprocess.run(
                ["git", "status", "--short"],
                cwd=self.workspace_root,
                capture_output=True,
                text=True
            )
            terminal.write("\n╔═══ Git Status ═══╗", style="bold blue")
            if result.stdout:
                terminal.write(result.stdout)
            else:
                terminal.write("  Working tree clean")
            terminal.write("╚══════════════════╝", style="bold blue")
        except Exception as e:
            terminal.write(f"Git error: {e}", style="red")

    def show_sessions(self):
        """Show available sessions."""
        terminal = self.query_one("#terminal-panel", TerminalPanel)
        sessions = self.session_manager.list_sessions(limit=10)

        terminal.write("\n╔═══ Available Sessions ═══╗", style="bold blue")

        if not sessions:
            terminal.write("  No saved sessions")
        else:
            for i, session in enumerate(sessions, 1):
                timestamp = datetime.fromtimestamp(session.last_active).strftime("%Y-%m-%d %H:%M")
                size_kb = self.session_manager.get_session_size(session.session_id) / 1024

                terminal.write(f"  {i}. {session.session_id[:8]}... ({timestamp})")
                terminal.write(f"     Tasks: {session.task_count}, Actions: {session.action_count}, Size: {size_kb:.1f} KB")
                terminal.write(f"     Resume: 'resume {session.session_id}'")

        terminal.write("╚══════════════════════════╝", style="bold blue")

    def resume_session(self, session_id: str):
        """Resume a previous session."""
        terminal = self.query_one("#terminal-panel", TerminalPanel)

        terminal.write(f"Resuming session {session_id[:8]}...", style="cyan")

        if self.session_manager.restore_session(self.agent, session_id):
            self.current_session_id = session_id
            terminal.write("✓ Session restored successfully", style="green")
            terminal.write(f"  Tasks: {len(self.agent.tasks)}")
            terminal.write(f"  Actions: {len(self.agent.action_history)}")
            terminal.write(f"  Conversation: {len(self.agent.conversation)} messages")

            # Refresh panels
            self.refresh_panels()
        else:
            terminal.write("✗ Failed to restore session", style="red")

    def save_current_session(self):
        """Save current session."""
        terminal = self.query_one("#terminal-panel", TerminalPanel)

        terminal.write("Saving session...", style="cyan")

        try:
            session_id = self.session_manager.save_session(self.agent)
            self.current_session_id = session_id

            size_kb = self.session_manager.get_session_size(session_id) / 1024
            terminal.write(f"✓ Session saved: {session_id[:8]}... ({size_kb:.1f} KB)", style="green")
        except Exception as e:
            terminal.write(f"✗ Error saving session: {e}", style="red")

    async def direct_llm_prompt(self, prompt: str):
        """
        Direct LLM prompting - send prompt directly to model without agent wrapper.

        This allows the user to interact with the LLM directly for:
        - Questions and answers
        - General conversation
        - Code generation without autonomous execution
        - Explanations and analysis
        """
        terminal = self.query_one("#terminal-panel", TerminalPanel)

        terminal.write("💬 Direct LLM prompting...", style="magenta")

        try:
            # This would call the router directly in production
            # For now, simulate a response
            response = f"""
[This would send your prompt directly to the LLM]

Your prompt: {prompt}

In production, this would:
1. Send prompt to configured model ({self.agent.model_name})
2. Return raw LLM response without agent processing
3. Allow direct conversation and Q&A
4. Support extended context (128K tokens via RAM buffer)

To enable direct prompting, connect to router at {self.agent.router_url}
"""

            terminal.write("\n🤖 LLM Response:", style="magenta")
            terminal.write(response)

            # Add to conversation history
            from .self_coder import ConversationMessage
            self.agent.conversation.append(
                ConversationMessage(role="user", content=prompt)
            )
            self.agent.conversation.append(
                ConversationMessage(role="assistant", content=response)
            )

        except Exception as e:
            terminal.write(f"Error: {e}", style="red")


def run_ide(workspace_root: str = None):
    """Run the IDE interface."""
    app = IDEInterface(workspace_root)
    app.run()


if __name__ == "__main__":
    import sys
    workspace = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    run_ide(workspace)
