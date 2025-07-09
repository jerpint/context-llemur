#!/usr/bin/env python3

import click
import sys
from src.ctx_core import CtxCore

# Initialize the core logic
ctx_core = CtxCore()

@click.group()
@click.version_option()
def main():
    """ctx: collaborative memory for humans and LLMs (context-llemur)"""
    pass

@main.command()
@click.argument('directory', required=False, default='context')
@click.option('--dir', 'custom_dir', help='Custom directory name (alternative to positional argument)')
def new(directory, custom_dir):
    """Create a new ctx repository
    
    Examples:
        ctx new                    # Creates 'context' directory
        ctx new my-research        # Creates 'my-research' directory
        ctx new --dir ideas        # Creates 'ideas' directory
    """
    # Use custom_dir if provided, otherwise use directory argument
    target_dir = custom_dir if custom_dir else directory
    
    result = ctx_core.create_new_ctx(target_dir)
    
    if result.success:
        click.echo(f"Creating '{target_dir}' directory and copying template files...")
        for filename in result.data['copied_files']:
            click.echo(f"Copied {filename}")
        click.echo("Created .ctx marker file")
        click.echo(f"Initializing git repository in '{target_dir}'...")
        click.echo(f"✓ {result.message}")
        click.echo(f"✓ Files committed with 'first commit' message")
        click.echo(f"✓ Added '{target_dir}' to ctx config as active repository")
        click.echo("")
        click.echo("Next steps:")
        click.echo(f"1. cd {target_dir}")
        click.echo(f"2. Edit ctx.txt with your context")
        click.echo("3. Start exploring ideas on feature branches!")
    else:
        click.echo(f"Error: {result.error}", err=True)
        sys.exit(1)

@main.command()
@click.argument('exploration')
@click.option('--preview', is_flag=True, help='Show what would be integrated without performing the integration')
@click.option('--target', default='main', help='Target branch to integrate into (default: main)')
def integrate(exploration, preview, target):
    """Integrate insights from an exploration
    
    Git equivalent: git merge <exploration>
    """
    # Get merge preview
    preview_result = ctx_core.get_merge_preview(exploration, target)
    
    if not preview_result.success:
        click.echo(f"Error: {preview_result.error}", err=True)
        sys.exit(1)
    
    merge_preview = preview_result.data
    
    # Show preview
    click.echo(f"Merge preview: {merge_preview.source_branch} → {merge_preview.target_branch}")
    click.echo("=" * 50)
    
    if not merge_preview.changed_files:
        click.echo("No changes to merge.")
        return
    
    click.echo(f"Files that would be affected: {len(merge_preview.changed_files)}")
    for filepath in merge_preview.changed_files:
        click.echo(f"  • {filepath}")
    
    if merge_preview.has_conflicts:
        click.echo(f"\n⚠️  Potential conflicts detected: {len(merge_preview.conflicts)}")
        for conflict in merge_preview.conflicts:
            click.echo(f"  • {conflict['file']}")
    else:
        click.echo(f"\n✓ No conflicts detected. Merge should be clean.")
    
    # If preview mode, stop here
    if preview:
        return
    
    # Ask for confirmation if there are conflicts
    if merge_preview.has_conflicts:
        if not click.confirm(f"\n⚠️  Conflicts detected. Proceed with integration anyway?"):
            click.echo("Integration cancelled.")
            return
    
    # Perform the integration
    click.echo(f"\nProceeding with integration...")
    integration_result = ctx_core.perform_integration(exploration, target)
    
    if integration_result.success:
        click.echo(f"\n🎉 Insights from '{exploration}' successfully integrated into '{target}'!")
    else:
        click.echo(f"\n❌ Integration failed: {integration_result.error}")
        click.echo(f"Check the ctx/ directory for any conflicts that need manual resolution.")
        sys.exit(1)

@main.command()
def status():
    """Show current ctx repository status"""
    result = ctx_core.get_status()
    
    if not result.success:
        click.echo(f"Error: {result.error}", err=True)
        sys.exit(1)
    
    status_data = result.data
    
    click.echo(f"ctx repository: {status_data.repository.name} ({status_data.repository.absolute_path})")
    click.echo(f"Current branch: {status_data.current_branch}")
    click.echo(f"All branches: {', '.join(status_data.all_branches)}")
    
    if status_data.is_dirty:
        click.echo("\nUncommitted changes:")
        for item in status_data.uncommitted_changes:
            click.echo(f"  {item}")
    else:
        click.echo("\nWorking tree clean")

@main.command()
@click.argument('topic')
def explore(topic):
    """Start exploring a new topic or idea
    
    Git equivalent: git checkout -b <topic>
    """
    result = ctx_core.start_exploration(topic)
    
    if result.success:
        click.echo(f"✓ Started exploring '{topic}'")
        click.echo("Document your ideas and insights as you explore!")
    else:
        click.echo(f"Error: {result.error}", err=True)
        sys.exit(1)

@main.command()
@click.argument('message')
def save(message):
    """Saves the current state of the context repository
    
    Git equivalent: git add -A && git commit -m "<message>"
    """
    result = ctx_core.save(message)
    
    if result.success:
        click.echo(f"✓ {result.message}")
    else:
        click.echo(f"Error: {result.error}", err=True)
        sys.exit(1)

@main.command()
@click.option('--force', is_flag=True, help='Force discard without confirmation and remove untracked files')
def discard(force):
    """Reset to last commit, dropping all changes
    
    Git equivalent: git reset --hard HEAD
    
    This will:
    - Remove all staged changes
    - Remove all unstaged changes 
    - Reset all files to their state at the last commit
    - With --force: also removes untracked files and directories
    """
    # Check if there are any changes to discard
    status_result = ctx_core.get_status()
    if not status_result.success:
        click.echo(f"Error: {status_result.error}", err=True)
        sys.exit(1)
    
    if not status_result.data.is_dirty:
        click.echo("No changes to discard. Working tree is clean.")
        return
    
    # Show what will be discarded
    click.echo("The following changes will be permanently lost:")
    for item in status_result.data.uncommitted_changes:
        click.echo(f"  {item}")
    
    if force:
        click.echo("\n⚠️  --force flag: untracked files will also be removed")
    
    # Ask for confirmation unless --force is used
    if not force:
        if not click.confirm("\nAre you sure you want to discard all changes? This cannot be undone"):
            click.echo("Discard cancelled.")
            return
    
    # Perform the discard
    result = ctx_core.discard(force=force)
    
    if result.success:
        click.echo(f"✓ {result.message}")
    else:
        click.echo(f"Error: {result.error}", err=True)
        sys.exit(1)

@main.command(name="list")
def list_repos():
    """List all discovered ctx repositories"""
    result = ctx_core.list_repositories()
    
    if not result.success:
        click.echo(f"Error: {result.error}", err=True)
        sys.exit(1)
    
    repositories = result.data
    
    if not repositories:
        click.echo("No ctx repositories found in config.")
        click.echo("Run 'ctx new' to create a new ctx repository.")
        return
    
    click.echo("Discovered ctx repositories:")
    click.echo("=" * 50)
    
    for repo_info in repositories:
        marker = "→ " if repo_info.is_active else "  "
        status = "✓" if repo_info.exists else "✗"
        
        click.echo(f"{marker}{status} {repo_info.name}")
        if repo_info.is_active:
            click.echo("     (Currently active)")
        if not repo_info.exists:
            click.echo("     (Directory missing or invalid)")
        click.echo()

@main.command()
@click.argument('ctx_name')
def switch(ctx_name):
    """Switch to a different ctx repository"""
    result = ctx_core.switch_repository(ctx_name)
    
    if result.success:
        click.echo(f"✓ {result.message}")
    else:
        available = result.data.get('available_repositories', []) if result.data else []
        click.echo(f"Error: {result.error}", err=True)
        if available:
            click.echo(f"Available repositories: {', '.join(available)}")
        sys.exit(1)

@main.command()
@click.argument('directory', required=False)
@click.option('--branch', help='Branch to show files from (default: current branch)')
@click.option('--pattern', help='File pattern to filter (e.g., "*.md")')
def show_all(directory, branch, pattern):
    """Display all file contents with clear delimiters
    
    Perfect for LLM context absorption - shows entire repository state in one command.
    
    Examples:
        ctx show_all                    # Show all files in current branch
        ctx show_all --pattern "*.md"   # Show only markdown files
        ctx show_all docs --branch main # Show files in 'docs' directory from main branch
    """
    result = ctx_core.show_all(directory=directory, branch=branch, pattern=pattern)
    
    if not result.success:
        click.echo(f"Error: {result.error}", err=True)
        sys.exit(1)
    
    show_result = result.data
    
    # Print header information
    click.echo("=" * 80)
    click.echo("📁 CTX REPOSITORY CONTENTS")
    click.echo("=" * 80)
    click.echo(f"Branch: {show_result.branch}")
    if show_result.directory:
        click.echo(f"Directory: {show_result.directory}")
    if show_result.pattern:
        click.echo(f"Pattern: {show_result.pattern}")
    click.echo(f"Total files: {show_result.total_files}")
    click.echo()
    
    # Print each file with clear delimiters
    for i, file_info in enumerate(show_result.files):
        click.echo(f"{'=' * 80}")
        click.echo(f"📄 FILE {i+1}/{show_result.total_files}: {file_info['path']}")
        click.echo(f"📊 Size: {file_info['size']} chars, Lines: {file_info['lines']}")
        click.echo(f"{'=' * 80}")
        click.echo()
        click.echo(file_info['content'])
        click.echo()
    
    click.echo("=" * 80)
    click.echo("✅ REPOSITORY CONTENTS COMPLETE")
    click.echo("=" * 80)

@main.command()
@click.option('--staged', is_flag=True, help='Show staged changes')
@click.argument('branches', nargs=-1)
def diff(staged, branches):
    """Show git diff equivalent for the ctx repository
    
    Examples:
        ctx difference                # Show current changes
        ctx difference --staged       # Show staged changes
        ctx difference main           # Show changes vs main branch
        ctx difference feature-branch main # Show changes between two branches
    """
    result = ctx_core.get_diff(staged=staged, branches=list(branches))
    
    if not result.success:
        click.echo(f"Error: {result.error}", err=True)
        if result.data and 'available_branches' in result.data:
            click.echo(f"Available branches: {', '.join(result.data['available_branches'])}")
        sys.exit(1)
    
    diff_data = result.data
    
    if not diff_data['has_changes']:
        click.echo("No changes to show")
        return
    
    # Print diff header
    if diff_data['staged']:
        click.echo("Staged changes:")
    elif diff_data['branches']:
        if len(diff_data['branches']) == 1:
            click.echo(f"Changes vs {diff_data['branches'][0]}:")
        else:
            click.echo(f"Changes between {diff_data['branches'][0]} and {diff_data['branches'][1]}:")
    else:
        click.echo("Current changes:")
    
    click.echo("=" * 50)
    click.echo(diff_data['diff'])

@main.command()
def mcp():
    """Start the MCP server for AI agent integration
    
    This starts the Model Context Protocol server that allows AI agents
    to connect and use ctx as persistent, version-controlled memory.
    """
    try:
        from .mcp_server import run_server
        click.echo("🚀 Starting ctx MCP server...")
        click.echo("   AI agents can now connect to use ctx as persistent memory")
        click.echo("   Press Ctrl+C to stop the server")
        run_server()
    except KeyboardInterrupt:
        click.echo("\n👋 MCP server stopped")
    except ImportError as e:
        click.echo(f"❌ Error importing MCP server: {e}", err=True)
        click.echo("   Make sure fastMCP is installed: pip install fastmcp", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error starting MCP server: {e}", err=True)
        sys.exit(1)

if __name__ == "__main__":
    main()