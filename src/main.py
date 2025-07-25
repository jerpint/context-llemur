#!/usr/bin/env python3

import click
import sys
from src.ctx_core import CtxCore
from src.cli_styles import (
    print_banner, print_section_header, print_success_box, print_warning_box, 
    print_error_box, print_repository_card, print_status_summary, 
    print_integration_preview, print_celebration, print_explore_banner
)

# Initialize the core logic
ctx_core = CtxCore()

@click.group(invoke_without_command=True)
# @click.version_option()
@click.pass_context
def main(ctx):
    """ctx: collaborative memory for humans and LLMs (context-llemur)"""
    # Show beautiful banner when no command is provided
    if ctx.invoked_subcommand is None:
        print_banner()
        click.echo(ctx.get_help())

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
        print_section_header("Creating New Repository", "🎯")
        
        click.echo(f"\n📂 Creating '{target_dir}' directory and copying template files...")
        for filename in result.data['copied_files']:
            click.echo(f"   ✓ Copied {filename}")
        click.echo("   ✓ Created .ctx marker file")
        click.echo(f"   ✓ Initialized git repository")
        click.echo(f"   ✓ Files committed with 'first commit' message")
        click.echo(f"   ✓ Added '{target_dir}' to ctx config as active repository")
        
        print_celebration()
        
        print_section_header("Next Steps", "🚀")
        click.echo(f"1. {click.style('cd ' + target_dir, bold=True, fg='cyan')}")
        click.echo(f"2. {click.style('Edit ctx.txt with your context', bold=True, fg='cyan')}")
        click.echo(f"3. {click.style('Start exploring ideas on feature branches!', bold=True, fg='cyan')}")
    else:
        print_error_box(f"Failed to create repository: {result.error}")
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
    
    # Show beautiful preview
    print_integration_preview(
        source=merge_preview.source_branch,
        target=merge_preview.target_branch,
        changed_files=merge_preview.changed_files,
        has_conflicts=merge_preview.has_conflicts,
        conflicts=merge_preview.conflicts
    )
    
    if not merge_preview.changed_files:
        return
    
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
        print_celebration()
        print_success_box(f"Insights from '{exploration}' successfully integrated into '{target}'!", "🎉")
    else:
        print_error_box(f"Integration failed: {integration_result.error}\nCheck the repository for any conflicts that need manual resolution.")
        sys.exit(1)

@main.command()
def status():
    """Show current ctx repository status"""
    result = ctx_core.get_status()
    
    if not result.success:
        print_error_box(f"Failed to get status: {result.error}")
        sys.exit(1)
    
    status_data = result.data
    
    print_status_summary(
        repository_name=status_data.repository.name,
        current_branch=status_data.current_branch,
        all_branches=status_data.all_branches,
        is_dirty=status_data.is_dirty,
        uncommitted_changes=status_data.uncommitted_changes,
        repo_path=status_data.repository.absolute_path
    )

@main.command()
@click.argument('topic')
def explore(topic):
    """Start exploring a new topic or idea
    
    Git equivalent: git checkout -b <topic>
    """
    result = ctx_core.start_exploration(topic)
    
    if result.success:
        print_explore_banner(topic)
        print_success_box("Branch created successfully!\nDocument your ideas and insights as you explore!", "🚀")
    else:
        print_error_box(f"Failed to start exploration: {result.error}")
        sys.exit(1)

@main.command()
@click.argument('message')
def save(message):
    """Saves the current state of the context repository
    
    Git equivalent: git add -A && git commit -m "<message>"
    """
    result = ctx_core.save(message)
    
    if result.success:
        print_success_box(f"Saved: {result.message}", "💾")
    else:
        print_error_box(f"Failed to save: {result.error}")
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
        print_error_box(f"Failed to list repositories: {result.error}")
        sys.exit(1)
    
    repositories = result.data
    
    if not repositories:
        print_section_header("No Repositories Found", "📂")
        print_warning_box("No ctx repositories found in config.\nRun 'ctx new' to create a new ctx repository.", "💡")
        return
    
    print_section_header("Discovered Repositories", "📂")
    
    for repo_info in repositories:
        print_repository_card(
            name=repo_info.name,
            is_active=repo_info.is_active,
            exists=repo_info.exists,
            path=getattr(repo_info, 'path', None)
        )

@main.command()
@click.argument('ctx_name')
def switch(ctx_name):
    """Switch to a different ctx repository"""
    result = ctx_core.switch_repository(ctx_name)
    
    if result.success:
        print_success_box(f"Switched to repository: {ctx_name}", "🔄")
    else:
        available = result.data.get('available_repositories', []) if result.data else []
        error_msg = f"Failed to switch: {result.error}"
        if available:
            error_msg += f"\nAvailable repositories: {', '.join(available)}"
        print_error_box(error_msg)
        sys.exit(1)

@main.command()
@click.argument('directory', required=False)
@click.option('--branch', help='Branch to show files from (default: current branch)')
@click.option('--pattern', help='File pattern to filter (e.g., "*.md")')
def show_all(directory, branch, pattern):
    """Show all the current ctx repository contents
    
    Perfect for LLM context absorption - shows entire repository state in one command.
    
    Examples:
        ctx load                        # Show all files in current branch
        ctx load --pattern "*.md"       # Show only markdown files
        ctx load docs --branch main     # Show files in 'docs' directory from main branch
    """
    result = ctx_core.show_all(directory=directory, branch=branch, pattern=pattern)
    if result.success:
        click.echo(result.data)
    click.echo(result.error)


@main.command()
@click.argument('ctx_name', required=False)
@click.option('--pattern', help='File pattern to filter (e.g., "*.md")')
def load(ctx_name, pattern):
    """Load the ctx_name
    
    Perfect for LLM context absorption - shows entire repository state in one command.
    
    Examples:
        ctx load                        # Show all files in current branch
        ctx load --pattern "*.md"       # Show only markdown files
        ctx load docs --branch main     # Show files in 'docs' directory from main branch
    """
    result = ctx_core.load_ctx(ctx_name, pattern=pattern)
    if result.success:
        click.echo(result.data)
    click.echo(result.error)

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

@main.command()
@click.argument('source')
@click.argument('destination')
def mv(source, destination):
    """Move a file within the ctx repository
    
    Git equivalent: git mv <source> <destination>
    
    Examples:
        ctx mv old-file.txt new-file.txt       # Rename file
        ctx mv file.txt subdir/file.txt        # Move to subdirectory
        ctx mv subdir/file.txt file.txt        # Move to parent directory
    """
    result = ctx_core.move_file(source, destination)
    
    if result.success:
        click.echo(f"✓ {result.message}")
    else:
        click.echo(f"Error: {result.error}", err=True)
        sys.exit(1)

@main.command()
@click.argument('filepath')
@click.option('--force', is_flag=True, help='Force removal even if file has uncommitted changes')
def rm(filepath, force):
    """Remove a file from the ctx repository
    
    Git equivalent: git rm <filepath>
    
    This will:
    - Remove the file from git tracking
    - Remove the file from the filesystem
    - Fail if file has uncommitted changes (unless --force is used)
    
    Examples:
        ctx rm old-file.txt                    # Remove tracked file
        ctx rm --force modified-file.txt       # Force remove file with changes
    """
    result = ctx_core.remove_file(filepath, force=force)
    
    if result.success:
        click.echo(f"✓ {result.message}")
    else:
        click.echo(f"Error: {result.error}", err=True)
        sys.exit(1)

if __name__ == "__main__":
    main()