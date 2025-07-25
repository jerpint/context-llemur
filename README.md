# context-llemur 🐒

*Stop re-explaining your context to every LLM.*

Every AI conversation starts from zero. Whether you're switching from Claude to Cursor, or from ChatGPT to a local LLM, you're constantly re-explaining your project context. `ctx` solves this by giving you **portable, version-controlled context** that travels between ALL your AI tools.

## **ctx Features**

- **MCP Server Integration**: Full Model Context Protocol support
- **Git-Based**: It's just git under the hood
- **CLI for Humans**: Take over whenever you feel like it
- **Portable**: Use it with any LLM - no vendor lock-in, no assumptions

## Quickstart


### CLI

```bash
# Create a new context repository (defaults to ./context)
ctx new

# add/edit some files inside the `context/` directory
# or use your favourite LLM to edit for you (e.g. cursor, MCP)
echo "The next goal of this project is to..." >> context/goals.txt

# Save your context for versioning and tracking 
ctx save "Updated goals"  # equivalent to git add -A && git commit -m "..."
```

### MCP

`ctx` includes a full MCP server with tools that give AI agents persistent, version-controlled memory.

#### Starting the MCP Server

```bash
ctx mcp
```

#### Claude Desktop Integration

Add this to your `~/Library/Application\ Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "context-llemur": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/your/project/",
        "--with",
        "context-llemur",
        "ctx",
        "mcp"
      ]
    }
  }
}
```

Now start your conversation with `ctx load` and your LLM will have access to the entire context folder and all MCP-supported operations:

- **Repository Management**: Create, switch, and manage contexts
- **Semantic Workflows**: Explore topics, save insights, integrate knowledge
- **File Operations**: Read, write, and organize context files
- **Navigation**: Browse branches, history, and search content


## Installation

Install with uv:
```bash
uv add context-llemur
```

After installation, activate your environment to use the `ctx` command directly:
```bash
source .venv/bin/activate
ctx --help
```

Alternatively, you can use `uv run ctx ...`

To install with pip:
```bash
pip install context-llemur
```
## Core Commands

### ctx Management
- `ctx new [name]` - Create new context repository (default: ./context/)
- `ctx status` - Show current repository status
- `ctx list` - List all discovered context repositories
- `ctx switch <name>` - Switch to a different context repository

### ctx Workflows
- `ctx explore <topic>` - Start exploring a new topic (creates a new branch)
- `ctx save <message>` - Save current insights, equivalent to `git add -A && git commit -m`
- `ctx integrate <exploration>` - Merge insights back to main context
- `ctx diff` - Show current changes
- `ctx discard [--force]` - Reset to last commit, dropping all changes

### File Operations
- `ctx mv <source> <destination>` - Move or rename files (git mv equivalent)
- `ctx rm <filepath> [--force]` - Remove files from repository (git rm equivalent)

### Content Operations
- `ctx load [directory]` - Display all file contents with clear delimiters
- `ctx recent` - Show recent activity and modified files
- `ctx mcp` - Start MCP server for AI agent integration

## Core Philosophy

- **Context is not code** The context of a project evolves naturally over time - goals, TODOs, rules, milestones, etc. These concepts are traditionally tracked outside of repos (think of PRs, Issues, etc.) - `ctx` tracks them as individual git repositories.
- **Context should be portable** You should be able to provide the context easily to any LLM or human, without any friction. Context should be as platform agnostic as possible.
- **Context history matters** - Just like code, it should be easy to track what changed in context, revert to previous states and freely explore without fear of losing context
- **Each context is different** As little assumptions as possible should have to be made about the structure and contents of context

## Design
An important design decision of `ctx` is to *not* use embeddings for retrieval. Instead, it relies on LLMs and humans to manage the context in a structured manner. The idea is that context windows are getting longer, and agents are getting more capable of finding information when properly structured.

At its core, a `ctx` folder is an independently tracked `git` repository. It can easily be loaded as an MCP server, and exposes all `ctx` primitives by default to any LLM with its own `ctx.txt` file.

## Managing Contexts

`ctx` supports switching between multiple independent contexts. 

Creating a new context will automatically switch to the new context. Switch back to the previous context using `ctx switch`.

Contexts are managed using the following two files:

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

## Advanced Workflows

You can `explore` new ideas and `integrate` them back to the main context when ready:

```bash
ctx explore "new-feature"
echo "the first feature we will work on will be..." > TODOS.txt
ctx save "add new feature"
ctx integrate "new-feature"
```

`ctx` is mostly wrapper commands around a git repository, so if you navigate to your `ctx` repository, you can also just use whatever git commands you are used to.


## Git Command Mapping
For users familiar with git, here's the direct mapping:

| ctx Command | Git Equivalent | Purpose |
|-------------|----------------|---------|
| `ctx save "<message>"` | `git add -A && git commit -m "<message>"` | Stage and commit changes |
| `ctx status` | `git status && git branch` | Show repo and branch status |
| `ctx discard` | `git reset --hard HEAD` | Reset to last commit |
| `ctx mv <source> <destination>` | `git mv <source> <destination>` | Move or rename files |
| `ctx rm <filepath>` | `git rm <filepath>` | Remove files from repository |
| `ctx explore <topic>` | `git checkout -b <topic>` | Create and switch to new branch |
| `ctx integrate <branch>` | `git merge <branch>` | Merge branch into current |

## Use Cases

### Cursor/Agentic IDEs/CLI tools

The primary use-case for `ctx` is for it to be used with agentic LLMs. In fact, `ctx` was developed using `ctx` and `cursor`!

A suggested workflow is to include the entire `context` folder at the start of each conversation. This can be done by adding e.g. a `.cursorrule` to always include the `context/` folder or by using the `MCP` server and the `ctx load` function.

By default, each new context folder includes the [ctx.txt](./src/template/ctx.txt) file, which explains to the LLM what context is, so it out-of-the-box will be aware that it is using `ctx` and know how to interact with it. `MCP` servers are also self-documenting so the LLM will immediately know what it can do with `ctx`.

### Claude Desktop / Other LLMs
Keep track of topics you care about in an explicit way. One use-case I've been using this for is tracking workouts and having Claude generate new workouts for me based on my workout history and leveraging its artifcats.

I basically just run `ctx load + propose me a new workout` inside Claude Desktop and it immediately will know what to do. I can in the same conversation log what I did, and ask Claude to save it back to the context.

---

⚠️ `ctx` is in active development and things might change.