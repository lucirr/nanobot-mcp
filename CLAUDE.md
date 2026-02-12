# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

nanobot is an ultra-lightweight personal AI assistant framework (~4,000 lines of core code). It provides a complete agent system with tool execution, multi-channel chat support, LLM provider abstraction, and MCP integration.

## Development Commands

### Installation & Setup
```bash
# Install from source (development)
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"

# Initialize configuration
nanobot onboard
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_tool_validation.py

# Run with async support (configured in pyproject.toml)
pytest -v
```

### Linting
```bash
# Check code style (Ruff is configured in pyproject.toml)
ruff check .

# Format code
ruff check --fix .
```

### Running the Agent
```bash
# Single message
nanobot agent -m "Hello!"

# Interactive mode
nanobot agent

# Start gateway (for chat channels)
nanobot gateway

# Show status
nanobot status
```

## Architecture

### Core Agent Loop (`nanobot/agent/loop.py`)

The agent loop is the heart of nanobot:
1. Receives messages from the message bus
2. Builds context with history, memory, and skills
3. Calls the LLM with available tools
4. Executes tool calls iteratively
5. Sends responses back through the bus

Key concepts:
- **Max iterations**: Default 20 iterations to prevent infinite loops
- **Tool execution**: Synchronous tool call → result → next LLM call
- **Session management**: Conversation state persisted per channel:chat_id
- **MCP integration**: External tools registered dynamically

### Tool System (`nanobot/agent/tools/`)

Uses a **registry pattern** for tool management:
- `base.py`: Base `Tool` class with validation logic
- `registry.py`: `ToolRegistry` manages all available tools
- `filesystem.py`: File operations (read, write, edit, list)
- `shell.py`: Shell command execution with safety checks
- `web.py`: Web search (Brave API) and web fetch
- `message.py`: Send messages to channels
- `spawn.py`: Launch subagents for background tasks

**Adding new tools**:
1. Extend `Tool` class in `nanobot/agent/tools/`
2. Implement required properties: `name`, `description`, `parameters`, `execute()`
3. Register in `AgentLoop._register_default_tools()`

### Provider System (`nanobot/providers/`)

Abstraction layer for LLM providers using LiteLLM:
- `base.py`: `LLMProvider` interface
- `litellm_provider.py`: Main implementation using LiteLLM
- `registry.py`: **Provider registry** - single source of truth for all providers

**Adding a new provider** (2 steps):
1. Add `ProviderSpec` to `PROVIDERS` list in `registry.py`
2. Add field to `ProvidersConfig` in `config/schema.py`

Registry handles: environment variables, model prefixing, auto-detection, and display formatting.

### Channel System (`nanobot/channels/`)

Multi-channel chat support:
- `base.py`: `Channel` base class
- `manager.py`: `ChannelManager` orchestrates all channels
- Individual implementations: `telegram.py`, `discord.py`, `whatsapp.py`, `mochat.py`, `slack.py`, `email.py`, `feishu.py`, `dingtalk.py`, `qq.py`

All channels:
- Publish inbound messages to the message bus
- Listen for outbound messages from the bus
- Handle channel-specific authentication and message formatting

### Message Bus (`nanobot/bus/`)

Asynchronous message routing:
- `queue.py`: `MessageBus` with asyncio queues
- `events.py`: `InboundMessage` and `OutboundMessage` types

Flow: Channel → Bus → Agent Loop → Bus → Channel

### Configuration (`nanobot/config/`)

Pydantic-based configuration system:
- `schema.py`: All config models (providers, channels, tools, agents)
- `loader.py`: Load/save config from `~/.nanobot/config.json`

Config structure:
- `providers.*`: API keys and settings for LLM providers
- `channels.*`: Settings for each chat channel
- `agents.defaults.*`: Default agent behavior (model, iterations, workspace)
- `tools.*`: Tool-specific settings (web search API, exec timeout, MCP servers)

### MCP Integration (`nanobot/mcp/`)

Model Context Protocol client support:
- `manager.py`: `MCPManager` coordinates multiple MCP servers
- `client.py`: `MCPClient` handles HTTP/SSE transport
- `tool_wrapper.py`: Wraps MCP tools as nanobot tools

MCP servers defined in config at `tools.mcp.servers.*`:
```json
{
  "tools": {
    "mcp": {
      "enabled": true,
      "servers": {
        "my-server": {
          "enabled": true,
          "transport": "http",
          "url": "http://localhost:8080",
          "timeout": 30
        }
      }
    }
  }
}
```

### Workspace System

User workspace at `~/.nanobot/workspace/` contains:

**Bootstrap files** (loaded into system prompt):
- `AGENTS.md`: Agent instructions and guidelines
- `SOUL.md`: Personality and values
- `USER.md`: User information and preferences
- `TOOLS.md`: Available tools documentation
- `IDENTITY.md`: Custom identity (optional)

**Memory system**:
- `memory/MEMORY.md`: Long-term persistent memory
- `memory/YYYY-MM-DD.md`: Daily notes (auto-created)

**Skills system**:
- `skills/`: User-defined custom skills
- `nanobot/skills/`: Bundled skills (github, weather, tmux, etc.)
- Each skill has a `SKILL.md` file with instructions
- Skills loaded progressively (always-loaded vs. on-demand)

**Heartbeat** (`HEARTBEAT.md`):
- Checked every 30 minutes
- Used for periodic task management

### Session Management (`nanobot/session/`)

Conversation state management:
- Session key format: `{channel}:{chat_id}`
- History stored as message list: `[{"role": "user", "content": "..."}, ...]`
- Persisted to `~/.nanobot/data/sessions/{session_key}.json`
- Helper methods: `add_message()`, `get_history()`, `clear()`

### Subagent System (`nanobot/agent/subagent.py`)

Background task execution:
- Spawned via `spawn` tool
- Runs independently in asyncio task
- Announces completion via system message
- Results routed back to original channel

## Key Design Patterns

### Provider Registry Pattern
Single source of truth in `providers/registry.py`. Each provider defined as `ProviderSpec` with:
- Keywords for auto-matching
- Environment variable names
- Model prefixing rules
- Gateway detection logic

### Tool Registry Pattern
All tools registered in `ToolRegistry`:
- Auto-generates OpenAI function calling schemas
- Validates parameters before execution
- Executes with error handling

### Context Builder Pattern
`ContextBuilder` assembles prompts from multiple sources:
1. Core identity (runtime, workspace, time)
2. Bootstrap files (AGENTS.md, SOUL.md, etc.)
3. Memory context
4. Skills (always-loaded + available summary)
5. Conversation history
6. Current message

### Channel Manager Pattern
`ChannelManager` orchestrates all channels:
- Starts/stops channels concurrently
- Routes messages via shared message bus
- Each channel runs independently

## Important Implementation Details

### Tool Execution Safety
- Shell commands have dangerous command blocking (rm -rf, format, dd, etc.)
- Output truncation (10KB for shell, 50KB for web fetch)
- Configurable timeout (default 60s for shell)
- Optional workspace restriction (`tools.restrictToWorkspace`)

### Message Bus Flow
```
User Input → Channel → InboundMessage → Bus → Agent Loop
                                                    ↓
User Output ← Channel ← OutboundMessage ← Bus ← Response
```

### Agent Loop Iteration
```
1. Build context (system + history + current message)
2. Call LLM with tools
3. If tool calls: execute all → add results → goto 2
4. If no tool calls: return final response
5. Save to session
```

### Provider Matching Logic
1. Match by model name keywords (e.g., "deepseek" → deepseek provider)
2. Fallback to gateway providers (OpenRouter, AiHubMix)
3. Fallback to first provider with API key
4. Apply model prefixing based on provider spec

### Skill Loading
- **Always-loaded**: Full content included in system prompt
- **Available**: Only summary shown; agent uses `read_file` to load when needed
- Skills marked as always-loaded via metadata in SKILL.md

## Testing Approach

Tests use pytest with pytest-asyncio:
- `tests/test_tool_validation.py`: Tool parameter validation
- `tests/test_email_channel.py`: Email channel functionality
- `tests/test_mcp_*.py`: MCP client and server testing
- `tests/test_cli_input.py`: CLI input handling

Testing pattern:
```python
async def test_something():
    # Setup
    registry = ToolRegistry()
    tool = SomeTool()
    registry.register(tool)

    # Execute
    result = await registry.execute("tool_name", {"param": "value"})

    # Assert
    assert "expected" in result
```

## Code Style

- Python 3.11+ required
- Type hints used throughout
- Line length: 100 characters (Ruff config)
- Async/await for I/O operations
- Pydantic for data validation
- Loguru for logging

## Common Development Tasks

### Adding a Channel
1. Create new file in `nanobot/channels/`
2. Extend `Channel` base class
3. Implement `start()` and `stop()` methods
4. Add config model to `config/schema.py`
5. Register in `ChannelManager.__init__()`

### Adding a Provider
1. Add `ProviderSpec` to `providers/registry.py`
2. Add config field to `ProvidersConfig` in `config/schema.py`
3. That's it! Auto-wiring handles the rest

### Debugging Agent Behavior
- Use `nanobot agent --logs` to see runtime logs
- Check session files in `~/.nanobot/data/sessions/`
- Inspect workspace files (`~/.nanobot/workspace/`)
- Enable DEBUG logging: `logger.enable("nanobot")`

### Working with MCP
- MCP servers configured in `tools.mcp.servers.*`
- Initialize happens in `AgentLoop._initialize_mcp()`
- Tools automatically wrapped and registered
- Fault-tolerant: failures don't prevent agent startup
