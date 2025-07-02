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
# Initialize a new context repository
ctx init

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

- `ctx init` - Initialize new context repository
- `ctx explore <topic>` - Start exploring a new topic (creates branch)
- `ctx capture <message>` - Capture current insights (commits changes)
- `ctx integrate <exploration>` - Merge insights back to main context
- `ctx status` - Show current repository status

---