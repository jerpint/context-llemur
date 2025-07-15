# context-llemur 🐒

context-llemur, or `ctx` aims to make context management for LLMs portable and easy.
It exposes key commands to humans and LLMs making edits easy to track and automate.

## Core philosophy

- **Context is not code** The context of a project evolves naturally over time - goals, TODOs, rules, milestones, etc. These concepts are traditionally tracked outside of repos (think PRs, Issues, etc.) - `ctx` tracks them as indidivual git repositories.
- **Context should be portable** You should be able to provide the context easily to any LLM or human, without any friction. Context should be as platform agnostic as possible.
- **Context history matters** - Just like code, it should be easy to track what changed in context, revert to previous states and freely explore without fear of losing context
- **Each context is different** As little assumptions as possible should have to be made about the structure and contents of context

## Design
An important design decision of `ctx` is to *not* use embeddings. The idea is that context windows are getting longer, and agents are getting more capable of finding information when properly structured.

At its core, a `ctx` folder is an independently tracked `git` repository. It can easily be loaded as an MCP server, and exposes all `ctx` primitives by default to any LLM with its own `ctx.txt` file.

## Installation

Using `uv`, just add it as a dependency to your project:

    uv add context-llemur

After installation, activate your environment to use the `ctx` command directly:
```bash
source .venv/bin/activate
ctx --help
```

Alternatively, you can use `uv run ctx ...`

## Quickstart

Start by initializing a new `ctx` folder: 

    ctx new

This will create, in your current directory, a new `context` folder and a `ctx.config` file to keep track of multiple context folders (more on that later).

```bash
# Create a new context/ repository
ctx new

# add/edit some files inside the `context/` directory
echo "The next goal of this project is to..." >> context/goals.txt

# Save your context over time
ctx save "Updated goals"  # equivalent to git add -A && git commit -m "..."
```
Note that the idea here is to let LLMs run these commands on your behalf. Simply provide them the context and let them figure out the rest on your behalf.

In the following section we will see different ways to give access to LLMs to `ctx`

## Use-cases

### Cursor/Agentic IDEs/CLI tools

The primary use-case for `ctx` is for it to be used with agentic LLMs. In fact, `ctx` was developped using `ctx` and `cursor`!

A suggested workflow is to include the entire `context` folder at the start of each conversation. This can be done by adding e.g. a `.cursorrule` to always include the `context/` folder or by using the `MCP` server and the `ctx load` function.

By default, each new context folder includes the [ctx.txt](./src/template/ctx.txt) file, which explains to the LLM what context is, so it out-the-box will be aware that it is using `ctx` and know how to interact with it. `MCP` servers are also self-documenting so the LLM will immediately know what it can do with `ctx`.

### MCP Server

`ctx` exists as a standalone MCP server with the same primitives as the CLI tool, allowing you to easily keep any LLM up-to-date. 

Start an MCP server using the `ctx mcp` command. Then just type `ctx load` to your LLM, it'll know what to do!

#### Claude MCP


To use `ctx` with Claude Desktop as an MCP service simply add to your `~/Library/Application\ Support/Claude/claude_desktop_config.json`

```
{
  "mcpServers": {
    "context-llemur": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/your/contexts/",
        "--with",
        "context-llemur",
        "ctx",
        "mcp"
      ]
    }
  }
}
```

Now start your conversation with `ctx load` and voila!

## Core Commands

- `ctx new [name]` - Create new context repository (default: ./context/)
- `ctx save <message>` - save current insights, equivalent to `git -A && git commit -m`
- `ctx status` - Show current repository status
- `ctx list` - List all discovered context repositories
- `ctx switch <name>` - Switch to a different context repository
- `ctx explore <topic>` - Start exploring a new topic (creates a new branch)
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

## More workflows

You can `explore` new ideas and `integrate` them back to the main context when ready

```bash
ctx explore "new-feature"
echo "the first feature we will work on will be..." > TODOS.txt
ctx save "add new feature"
ctx integrate
```

`ctx` is mostly wrapper commands around a git repository, so if you navigate to your `ctx` repository, you can also just use whatever git commands you are used to.

---

⚠️ `ctx` is in active development and things might change.