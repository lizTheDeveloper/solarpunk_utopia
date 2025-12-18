# MCP Hot-Reload Proxy - Abstract Agent Team

**94% Context Savings** | **Zero-Restart Hot-Reload** | **Programmatic Orchestration**

## Quick Start

After restarting Claude Code ONCE to load the proxy, you can now dynamically load and call tools!

### The Proxy Tool

```python
# Load any MCP server dynamically (add to .mcp.json first or use install_and_load)
load_mcp_server_dynamically("server-name")

# Install from git and load immediately
install_and_load_mcp_server("https://github.com/user/mcp-server")

# Call any tool programmatically
call_dynamic_server_tool("server-name", "tool_name", {"param": "value"})

# See what's loaded
get_loaded_servers()
```

## Template Repository

**This project IS the template repository.** All other projects copy from here.

**Template location:** `mcp_proxy_system/`

**Contains:**
- `README.md` - Complete documentation (1,000+ lines)
- `utils/dynamic_server_loader.py` - Subprocess management with JSON-RPC
- `servers/proxy_server.py` - 5 meta-tools for hot-reload
- `templates/` - Example servers and configurations

## Creating Project-Specific Tools

Edit `mcp_proxy_system/servers/proxy_server.py` to expose project-specific operations:

```python
# Import your operations
from your_module import operation1, operation2

# Register in TOOL_REGISTRY
TOOL_REGISTRY = {
    "operation1": operation1,
    "operation2": operation2,
}

# Now callable via:
call_mcp_tool("operation1", {"param": "value"})
```

## Example Workflows

### Multi-Project Server Management

```python
# Load different project servers
load_mcp_server_dynamically("ai-tutor-proxy")
load_mcp_server_dynamically("cto-tycoon-proxy")
load_mcp_server_dynamically("simulation-proxy")

# Call tools across projects
ai_students = call_dynamic_server_tool("ai-tutor-proxy", "list_students", {})
cto_projects = call_dynamic_server_tool("cto-tycoon-proxy", "list_projects", {})
sim_agents = call_dynamic_server_tool("simulation-proxy", "list_agents", {})

# Cross-project analysis
for student in ai_students["data"]:
    # Coordinate across projects
    pass
```

### Installing MCP Servers from Git

```python
# Install and load in one step
install_and_load_mcp_server("https://github.com/modelcontextprotocol/servers.git", "filesystem")

# Now use the tools
files = call_dynamic_server_tool("filesystem", "list_directory", {"path": "/tmp"})
```

### Template Development

```python
# Test template changes
reload_mcp_server("abstract-agent-proxy")

# Verify tools available
servers = get_loaded_servers()
print(servers["servers"][0]["tools"])
```

## Benefits

- **Context Savings:** Load only what you need
- **Hot-Reload:** No restart for new tools
- **Programmatic:** Use tools in loops/conditions
- **Template Testing:** Test proxy changes instantly
- **Cross-Project:** Manage multiple project proxies

## Configuration

- `.mcp.json` - Proxy server configuration
- `mcp_proxy_system/` - Template implementation
- Customize `servers/proxy_server.py` for project-specific tools

## Deploying to Other Projects

**Copy template to new project:**
```bash
cp -r /Users/annhoward/src/abstract_agent_team/mcp_proxy_system /path/to/new/project/
```

**Update new project's .mcp.json:**
```json
{
  "mcpServers": {
    "new-project-proxy": {
      "command": "python",
      "args": ["-m", "mcp_proxy_system.servers.proxy_server"],
      "cwd": "/path/to/new/project",
      "env": {
        "PYTHONPATH": "/path/to/new/project"
      }
    }
  }
}
```

**Customize proxy_server.py** for new project's operations.

## Updating Template

**When updating the template:**
1. Make changes to `mcp_proxy_system/` in this repo
2. Test locally: `reload_mcp_server("abstract-agent-proxy")`
3. Deploy to other projects:
   ```bash
   cp -r mcp_proxy_system/ /path/to/project/
   ```
4. Reload in each project: `reload_mcp_server("project-proxy")`

## See Also

- [Complete Template README](mcp_proxy_system/README.md) - Full documentation
- [Installation Summary](mcp_proxy_system/INSTALLATION_SUMMARY.md) - Deployment status
- [Super Alignment Usage](../superalignmenttoutopia/MCP_PROXY_USAGE.md) - Production example
- [AI Tutor Usage](../ai_tutor/MCP_PROXY_USAGE.md) - Minimal example
- [CTO Tycoon Usage](../cto-tycoon/MCP_PROXY_USAGE.md) - Dashboard example
