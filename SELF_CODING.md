# SWORD Self-Coding Agent

A local Claude-like autonomous coding agent with IDE interface for the SWORD Coder MoE Router.

## Overview

The self-coding agent provides autonomous code generation, modification, and testing capabilities with an IDE-like interface. It integrates with MCP (Model Context Protocol) servers for enhanced functionality including documentation lookup, persistent memory, and uncensored analysis.

## Features

### 🤖 Autonomous Coding Agent
- **Code Generation**: Automatically generate new code from natural language descriptions
- **Code Modification**: Intelligently edit existing code using the Edit tool
- **Multi-step Planning**: Break down complex tasks into actionable steps
- **Self-Testing**: Automatically test code after modifications
- **Context Awareness**: Understand codebase structure through analysis

### 💻 IDE Interface (Textual TUI)
- **File Explorer**: Browse and navigate project files
- **Code Editor**: View files with syntax highlighting
- **Terminal Panel**: View agent execution output and logs
- **Task Panel**: Track coding tasks and their status
- **Action History**: See all agent actions and their results
- **Command Input**: Give coding tasks in natural language

### 🔌 MCP Server Integration
- **filesystem**: Secure local file access with path validation
- **context7**: Library and API documentation lookup
- **memlayer**: Persistent memory and knowledge graph
- **heretic**: Uncensored security and threat analysis
- **sequentialthinking**: Multi-step reasoning and planning
- **fetch**: Web content retrieval

## Installation

### Prerequisites
```bash
# Python 3.8+ required
python3 --version

# Install dependencies
pip install -r requirements.txt
```

### Dependencies Added
The following packages enable self-coding functionality:
- `textual>=0.47.0` - Modern TUI framework
- `pygments>=2.17.0` - Syntax highlighting
- `prompt-toolkit>=3.0.43` - Advanced terminal UI
- `litellm>=1.17.0` - LLM abstraction layer
- `tiktoken>=0.5.2` - Token counting

## Usage

### Option 1: TUI Launcher (Recommended)
```bash
./sword_launcher.sh
```
Select from menu:
- **IDE** - Launch full IDE interface
- **SelfCode** - Interactive command-line session
- **Test** - Test MCP servers

### Option 2: Command Line

#### Launch IDE Interface
```bash
python main.py --ide --workspace /path/to/project
```

**Keyboard Shortcuts:**
- `Ctrl+Q` - Quit
- `Ctrl+O` - Open file
- `Ctrl+S` - Save file
- `Ctrl+R` - Run task
- `Ctrl+L` - Clear terminal
- `F1` - Show help

#### Interactive Self-Coding Session
```bash
python main.py --self-code --workspace /path/to/project
```

**Commands:**
- `help` - Show available commands
- `status` - Show agent status
- `history` - Show action history
- `exit` - Exit session

Or describe a coding task:
```
>>> Add a function to calculate fibonacci numbers
>>> Fix the bug in the authentication module
>>> Refactor the database connection code
```

## Example Tasks

### Code Generation
```
>>> Create a REST API endpoint for user registration in src/api.py
```
The agent will:
1. Search for similar API implementations
2. Read existing API code
3. Generate the new endpoint
4. Write to the file
5. Test the implementation

### Bug Fixing
```
>>> Fix the SQL injection vulnerability in src/database.py line 42
```
The agent will:
1. Read the vulnerable code
2. Understand the security issue
3. Implement parameterized queries
4. Test the fix
5. Verify no regressions

### Code Refactoring
```
>>> Refactor src/utils.py to use async/await instead of callbacks
```
The agent will:
1. Analyze current code structure
2. Plan refactoring strategy
3. Refactor incrementally
4. Test after each change
5. Update tests if needed

## MCP Server Configuration

### Configuration File
`config/mcp_servers.yaml` - Configure MCP servers

### Key Servers

#### context7 (Documentation)
```bash
# Query documentation
agent.get_context("pytorch tensor operations")
```

#### memlayer (Persistent Memory)
```bash
# Store important information
agent.store_memory("api_key_location", "Stored in environment variables")

# Recall later
agent.recall_memory("api_key_location")
```

#### heretic (Uncensored Analysis)
```bash
# Security analysis with exploit scenarios
agent.analyze_security(code, include_exploits=True)

# Threat modeling
agent.create_threat_model(system, scope="full_stack")
```

#### filesystem (File Operations)
```bash
# All file operations are automatically secured
agent.read_file("src/module.py")
agent.write_file("src/new_module.py", content)
agent.search_files("pattern", "**/*.py")
```

## Architecture

### Components

```
src/
├── self_coder.py        # Main autonomous agent
├── ide_interface.py     # Textual-based IDE
├── code_tools.py        # File operation tools
├── mcp_router.py        # MCP integration (existing)
└── heretic_server.py    # Heretic MCP server

config/
└── mcp_servers.yaml     # MCP server configuration
```

### Agent Workflow

1. **Task Planning**: Break down user request into steps
2. **Context Gathering**: Search and read relevant files
3. **Action Generation**: Determine what tools to use
4. **Execution**: Execute actions (read, write, edit, run)
5. **Validation**: Test changes and verify success
6. **Memory**: Store important context in memlayer

### Task States
- `PENDING` - Task not started
- `IN_PROGRESS` - Currently working (only one at a time)
- `COMPLETED` - Successfully finished
- `FAILED` - Encountered errors
- `BLOCKED` - Waiting on dependencies

## Advanced Features

### Custom Expert Routing
The agent uses the MoE router to select appropriate models:

```python
# Code generation → DeepSeek-Coder on NPU
# Security analysis → WizardLM-Uncensored on iGPU (via heretic)
# Planning → DeepSeek-R1 on CPU AMX
```

### Knowledge Graph Integration
Store and query relationships via memlayer:

```python
# Create entities
agent.create_entity("FastAPI", type="framework")
agent.create_entity("Authentication", type="module")

# Create relationships
agent.relate_entities("Authentication", "uses", "FastAPI")

# Query graph
agent.query_graph("What modules use FastAPI?")
```

### Sequential Reasoning
Break down complex reasoning:

```python
# Multi-step planning
plan = agent.plan_steps("Implement OAuth2 authentication")
# Returns: ["Set up OAuth provider", "Create token endpoint", ...]

for step in plan:
    result = agent.execute_step(step)
    agent.validate_step(result)
```

## Security Considerations

### Path Validation
All file operations are restricted to workspace:
```python
# ✓ Allowed
agent.read_file("/workspace/src/module.py")

# ✗ Blocked
agent.read_file("/etc/passwd")
```

### Command Execution
Shell commands are sandboxed:
```python
# Timeout and working directory enforced
agent.run_command("pytest", cwd="tests", timeout=30)
```

### Heretic Server Authorization
Uncensored analysis requires authorized use:
- Security testing and penetration testing engagements
- CTF competitions and security research
- Defensive security analysis
- Educational contexts

**NEVER** for:
- Malicious activities
- Unauthorized system access
- Destructive attacks

## Performance

### Hardware Acceleration
Automatically uses available Intel hardware:
- **NPU** (3720): Fast inference for code completion
- **iGPU** (Arc): Large model inference (INT4 quantized)
- **CPU AMX**: Matrix operations for attention layers
- **Movidius VPUs**: Edge inference for small models

### Memory Management
- Tiered model loading based on available RAM
- Aggressive INT4 quantization for 70B+ models
- Disk offload for models >35GB

## Troubleshooting

### Issue: "Virtual environment not found"
```bash
# Run setup first
./scripts/setup.sh
```

### Issue: "MCP server failed to start"
```bash
# Test MCP servers
python main.py --mcp-test

# Check logs
tail -f /tmp/mcp_servers.log
```

### Issue: "Textual import error"
```bash
# Install IDE dependencies
pip install textual textual-dev pygments prompt-toolkit
```

### Issue: "Model not loaded"
```bash
# Check model availability
python main.py --storage

# Download models
./sword_launcher.sh → Download
```

## Examples

### Example 1: Add New Feature
```
IDE Command:
>>> Add a caching layer to the database module using Redis

Agent Actions:
1. Searches for database module
2. Reads existing code
3. Generates Redis cache wrapper
4. Integrates with existing queries
5. Adds cache invalidation logic
6. Creates unit tests
7. Runs tests

Result: ✓ Feature implemented and tested
```

### Example 2: Security Audit
```
IDE Command:
>>> Perform security audit of src/api/ and create threat model

Agent Actions:
1. Analyzes all API endpoints
2. Identifies vulnerabilities (SQLi, XSS, auth issues)
3. Calls heretic server for threat modeling
4. Generates comprehensive security report
5. Stores findings in memlayer

Result: Detailed security report with exploit scenarios
```

### Example 3: Code Refactoring
```
IDE Command:
>>> Refactor src/models.py to use dataclasses instead of dict

Agent Actions:
1. Analyzes current dict-based models
2. Plans incremental migration
3. Creates dataclass equivalents
4. Updates all usages
5. Runs tests after each change
6. Updates documentation

Result: ✓ Code refactored with no regressions
```

## API Reference

### SelfCodingAgent

```python
from self_coder import SelfCodingAgent

agent = SelfCodingAgent(
    workspace_root="/path/to/project",
    model_name="deepseek-coder-33b",
    router_url="http://localhost:8000"
)

# Autonomous coding
result = agent.autonomous_code(
    "Add a function to validate email addresses",
    max_iterations=10
)

# Interactive session
agent.interactive_session()
```

### CodeTools

```python
from code_tools import CodeTools

tools = CodeTools(workspace_root="/path/to/project")

# Read file
content = tools.read_file("src/module.py", start_line=10, end_line=50)

# Edit file
tools.edit_file("src/module.py", old_content, new_content)

# Search
results = tools.search_files("class.*Auth", regex=True)

# Run command
result = tools.run_command("pytest tests/", timeout=60)
```

## Contributing

To extend the self-coding agent:

1. **Add new tools** in `code_tools.py`
2. **Add MCP servers** in `config/mcp_servers.yaml`
3. **Extend agent logic** in `self_coder.py`
4. **Add IDE widgets** in `ide_interface.py`

## License

Same as SWORD Coder MoE Router project.

## Support

For issues and questions:
- Check logs: `/tmp/mcp_servers.log`
- Run tests: `python main.py --mcp-test`
- See main documentation: `GEMINI.md`
