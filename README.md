# context-llemur 🐒

context-llemur, or `ctx`, is a context-engineering CLI tool to enable collaborative memory for humans and LLMs - think "git for ideas".

`ctx` helps overcome LLM amnesia and aims to minimize human repetition by tracking the context of a given project using simple commands.

## Installation

Installation is recommended using the `uv` package manager.

### From git
```bash
# Public repository
uv pip install git+https://github.com/jerpint/context-llemur.git
```

```bash
# Private repository (requires SSH keys)
uv pip install git+ssh://git@github.com/jerpint/context-llemur.git
```

### Locally
```bash
git clone https://github.com/jerpint/context-llemur
cd context-llemur
uv venv && uv pip install -e .
```

After installation, activate your environment and use the ctx command:
```bash
source .venv/bin/activate
ctx --help
```

Alternatively, you can use `uv run ctx ...`

> Coming soon: deploy on pypi

## Quickstart

To get started, navigate to an existing git project or folder. Then run `ctx new`. This will automatically create a `context` folder, which will be tracked indepdently of your current project. It will also create a `ctx.config` at the root to keep track multiple context folders (more on that later).

```bash
# Create a new context repository
ctx new # Creates ./context/ directory

# edit some files inside the `context/` directory
echo "The goal of this project is to..." > goals.txt

# Save your context over time
ctx save "updated goals"  # equivalent to git add -A && git commit -m "..."
```

You can also `explore` new ideas and `integrate` them back to the context when ready

```bash
ctx explore "new-feature"
echo "the first feature we will work on will be..." > TODOS.txt
ctx save "add new feature"
ctx integrate
```

## Use cases

### Cursor

The primary use-case for `ctx` is for it to be used with cursor. In fact, `ctx` was developped using `ctx`!

A suggested workflow is to include the entire `context` folder, or better add a `.cursorrule` to always include the `context` folder.

By default, a new context folder includes `ctx.txt`, which explains to the LLM what context is, so it out-the-box will be aware that it is using `ctx` and you can simply ask it to update your contexts.

### MCP Server

`ctx` also exists as an MCP server with the same primitives as the CLI tool, allowing you to easily get your favourite LLMs up-to-date. Simply start a conversation with `ctx load`.

> TODO: Add instructions for adding the MCP server.




#### Claude

Install the project locally - then add to your `~/Library/Application\ Support/Claude/claude_desktop_config.json`

```
{
  "mcpServers": {
    "context-llemur": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/Users/jerpint/context-llemur",
        "python",
        "src/mcp_server.py"
      ]
    }
  }
}
```

Now simply start your conversation with `ctx load` and voila!

Note: I haven't yet explored the MCP integration in its full capacity, but have a basic working implementation for now.

## Why context-llemur?

- **Platform agnostic** - Doesn't adhere to a specific provider, e.g. `CLAUDE.md` or `cursorrules`
- **Portable**: Context repositories are just git directories with files, take them anywhere with you
- **Git-friendly**: Uses familiar git workflows under the hood, easy to add/extend commands
- **Flexible**: You control the workflow with the LLMs

## Core Commands

### Repository Management
- `ctx new [name]` - Create new context repository (default: ./context/)
- `ctx status` - Show current repository status
- `ctx list` - List all discovered context repositories
- `ctx switch <name>` - Switch to a different context repository

### Exploration & Integration
- `ctx explore <topic>` - Start exploring a new topic (creates branch)
- `ctx save <message>` - save current insights, equivalent to `git -A && git commit -m`
- `ctx integrate <exploration>` - Merge insights back to main context
- `ctx discard` - Reset to last commit, dropping all changes (with --force: also removes untracked files)

## Managing Contexts

`ctx` supports switching between multiple indepdendent contexts. 

Creating a new context will automatically switch to the new context. Switch back to the previous context using `ctx switch`.

Contexts are managed using the following 2 files:

- **`.ctx.config`**: TOML file at the root of the project which tracks active and available repositories
- **`.ctx` marker**: Empty file in each context repository for identification

Example `.ctx.config`:
```toml
active_ctx = "research"
discovered_ctx = ["context", "research", "experiments"]
```

This design allows you to:
- Create multiple context repositories in the same workspace
- Switch between them easily with `ctx switch <name>`
- Work from your project root without changing directories
- Keep repositories portable and git-friendly

---

⚠️ `ctx` is in active development