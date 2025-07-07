#!/usr/bin/env python3

import click
import sys
from .ctx_core import CtxCore

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
def init():
    """Initialize a new ctx repository (deprecated - use 'ctx new' instead)"""
    click.echo("Warning: 'ctx init' is deprecated. Use 'ctx new' instead.", err=True)
    # Call the new command with default directory
    from click.testing import CliRunner
    runner = CliRunner()
    result = runner.invoke(new, ['context'])
    if result.exit_code != 0:
        sys.exit(result.exit_code)

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
def capture(message):
    """Capture current insights and thinking
    
    Git equivalent: git add . && git commit -m "<message>"
    """
    result = ctx_core.capture_insights(message)
    
    if result.success:
        click.echo(f"✓ {result.message}")
    else:
        click.echo(f"Error: {result.error}", err=True)
        sys.exit(1)

@main.command()
def list():
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
        click.echo(f"✓ Switched to ctx repository: {ctx_name}")
    else:
        click.echo(f"Error: {result.error}", err=True)
        if result.data and 'available_repositories' in result.data:
            click.echo("Available repositories:")
            for repo in result.data['available_repositories']:
                click.echo(f"  • {repo}")
        sys.exit(1)

@main.command()
@click.option('--staged', is_flag=True, help='Show staged changes')
@click.argument('branches', nargs=-1)
def diff(staged, branches):
    """Show git diff output for the ctx repository
    
    Examples:
        ctx diff                    # Show unstaged changes
        ctx diff --staged          # Show staged changes  
        ctx diff main              # Show changes vs main branch
        ctx diff main develop      # Show diff between two branches
    """
    result = ctx_core.get_diff(staged=staged, branches=list(branches))
    
    if not result.success:
        click.echo(f"Error: {result.error}", err=True)
        if result.data and 'available_branches' in result.data:
            click.echo(f"Available branches: {', '.join(result.data['available_branches'])}")
        sys.exit(1)
    
    diff_data = result.data
    
    if not diff_data['has_changes']:
        if diff_data['staged']:
            click.echo("No staged changes.")
        elif diff_data['branches']:
            if len(diff_data['branches']) == 1:
                click.echo(f"No changes between current branch and {diff_data['branches'][0]}.")
            else:
                click.echo(f"No changes between {diff_data['branches'][0]} and {diff_data['branches'][1]}.")
        else:
            click.echo("No unstaged changes.")
    else:
        click.echo(diff_data['diff'])

if __name__ == "__main__":
    main()