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

## Usage

To get started, navigate to an existing git project. Then run `ctx new`. This will automatically create a `context` folder, which will be tracked indepdently - it automatically initializes its own git repo. It will also create a `ctx.config` at the root to keep track multiple context folders.

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