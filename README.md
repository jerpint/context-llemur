# context-llemur 🐒

context-llemur (ctx) is meant to help LLM amenesia and facilitate human-llm collaboration.

**Collaborative memory for humans and LLMs**

`context-llemur` or `ctx` is a git-friendly tool for managing collaborative context between humans and AI assistants. Think "git for ideas".

`ctx` helps you track, explore, and integrate insights across different explorations and conversations. It also mitigates the LLM amnesia tool.

## Installation

Installation is recommended using `uv` package manager:

```bash
git clone https://github.com/jerpint/context-llemur
cd context-llemur
uv add 
uv pip install -e .
```

> Coming soon: pypi

## Quick Start

```bash
# Create a new context repository
ctx new research                  # Creates ./research/ directory

# Start exploring a new idea
ctx explore "machine-learning-bias"

# Capture insights as you discover them
ctx capture "identified key bias sources in training data"

# Preview what you'd integrate back
ctx integrate "machine-learning-bias" --preview

# Integrate your insights back to main context
ctx integrate "machine-learning-bias"
```

## Why context-llemur?

- **Git-friendly**: Uses familiar git workflows under the hood
- **Collaborative**: Designed for human-LLM collaboration
- **Portable**: Context repositories are just git directories with files
- **Flexible**: Works with any AI assistant or tool

## Core Commands

### Repository Management
- `ctx new [name]` - Create new context repository (default: ./context/)
- `ctx status` - Show current repository status
- `ctx list` - List all discovered context repositories
- `ctx switch <name>` - Switch to a different context repository

### Exploration & Integration
- `ctx explore <topic>` - Start exploring a new topic (creates branch)
- `ctx capture <message>` - Capture current insights (commits changes)
- `ctx integrate <exploration>` - Merge insights back to main context
- `ctx integrate <exploration> --preview` - Preview integration without executing

## Repository Discovery

ctx uses a simple config-based approach for managing multiple context repositories:

- **`.ctx.config`**: TOML file at your project root tracks active and discovered repositories
- **`.ctx` marker**: Empty file in each context repository for identification
- **Auto-discovery**: `ctx new` automatically registers new repositories
- **Seamless workflow**: Run `ctx new research` from project root, then `ctx status` works immediately

Example `.ctx.config`:
```toml
active_ctx = "research"
discovered_ctx = ["ctx", "research", "experiments"]
```

This design allows you to:
- Create multiple context repositories in the same workspace
- Switch between them easily with `ctx switch <name>`
- Work from your project root without changing directories
- Keep repositories portable and git-friendly

---