#!/usr/bin/env python3

import click
import os
from pathlib import Path
import sys
import shutil
import tomllib
import tomli_w
from git import Repo, InvalidGitRepositoryError, GitCommandError

def find_project_root():
    """Find the project root by looking for ctx.config file"""
    current_dir = Path.cwd()
    
    # Search upward from current directory (with reasonable limits)
    max_depth = 10
    depth = 0
    
    for parent in [current_dir] + list(current_dir.parents):
        depth += 1
        if depth > max_depth:
            break
            
        config_file = parent / 'ctx.config'
        if config_file.exists():
            return parent
    
    return current_dir  # Default to current directory if no config found

def get_ctx_config_path():
    """Get the path to the ctx.config file"""
    project_root = find_project_root()
    return project_root / 'ctx.config'

def ensure_ctx_config():
    """Ensure the ctx.config file exists, creating it if necessary"""
    # Use current directory as project root for initial creation
    config_path = Path.cwd() / 'ctx.config'
    
    if not config_path.exists():
        # Create default config (omit active_ctx if None to avoid TOML serialization issues)
        default_config = {
            'discovered_ctx': []
        }
        try:
            with open(config_path, 'wb') as f:
                tomli_w.dump(default_config, f)
            click.echo(f"✓ Created ctx.config at {str(config_path)}")
        except Exception as e:
            click.echo(f"Warning: Could not create ctx.config: {e}", err=True)

def load_ctx_config():
    """Load the ctx configuration from ctx.config file"""
    config_path = Path.cwd() / 'ctx.config'
    
    if not config_path.exists():
        return {
            'active_ctx': None,
            'discovered_ctx': []
        }
    
    try:
        with open(config_path, 'rb') as f:
            config = tomllib.load(f)
            return {
                'active_ctx': config.get('active_ctx'),
                'discovered_ctx': config.get('discovered_ctx', [])
            }
    except Exception:
        return {
            'active_ctx': None,
            'discovered_ctx': []
        }

def save_ctx_config(config):
    """Save the ctx configuration to ctx.config file"""
    config_path = get_ctx_config_path()
    
    try:
        with open(config_path, 'wb') as f:
            tomli_w.dump(config, f)
    except Exception as e:
        click.echo(f"Warning: Could not save config: {e}", err=True)

def add_ctx_to_config(ctx_path, set_as_active=True):
    """Add a ctx directory to the config and optionally set as active"""
    # Simple approach: work directly with the config file
    config_path = Path.cwd() / 'ctx.config'
    
    # Load existing config or create empty one
    if config_path.exists():
        try:
            with open(config_path, 'rb') as f:
                config = tomllib.load(f)
        except Exception:
            config = {}
    else:
        config = {}
    
    # Ensure required keys exist
    if 'discovered_ctx' not in config:
        config['discovered_ctx'] = []
    
    # Convert to relative path from current directory
    ctx_path = Path(ctx_path)
    try:
        relative_path = str(ctx_path.relative_to(Path.cwd()))
    except ValueError:
        relative_path = str(ctx_path.name)  # Just use the directory name
    
    # Add to discovered list if not already there
    if relative_path not in config['discovered_ctx']:
        config['discovered_ctx'].append(relative_path)
    
    # Set as active if requested
    if set_as_active:
        config['active_ctx'] = relative_path
    
    # Save config
    try:
        with open(config_path, 'wb') as f:
            tomli_w.dump(config, f)
    except Exception as e:
        click.echo(f"Warning: Could not save config: {e}", err=True)

def find_ctx_root():
    """Find the active ctx repository from config"""
    config = load_ctx_config()
    
    if not config['active_ctx']:
        return None
    
    # Use current directory as project root
    ctx_path = Path.cwd() / config['active_ctx']
    
    # Verify it still exists and has .ctx marker
    if ctx_path.exists() and (ctx_path / '.ctx').exists():
        return ctx_path
    
    return None

def get_ctx_dir():
    """Get the ctx directory path"""
    return find_ctx_root()

def get_ctx_repo():
    """Get the GitPython repo object for the ctx directory"""
    ctx_dir = get_ctx_dir()
    if not ctx_dir:
        return None
    try:
        return Repo(ctx_dir)
    except InvalidGitRepositoryError:
        return None

def is_ctx_repo():
    """Check if we're in or under a ctx repository"""
    return get_ctx_dir() is not None

def ensure_ctx_repo():
    """Ensure we're in a ctx repository"""
    if not is_ctx_repo():
        click.echo("Error: Not in a ctx repository. Run 'ctx new' first.", err=True)
        sys.exit(1)

def get_template_dir():
    """Get the path to the template directory"""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    return script_dir / "template"

def get_current_branch():
    """Get the current git branch name"""
    repo = get_ctx_repo()
    if not repo:
        return 'main'
    try:
        return repo.active_branch.name
    except:
        return 'main'

def get_all_branches():
    """Get all git branches"""
    repo = get_ctx_repo()
    if not repo:
        return ['main']
    try:
        return [branch.name for branch in repo.branches]
    except:
        return ['main']

def get_changed_files(source_branch, target_branch='main'):
    """Get files that differ between two branches"""
    repo = get_ctx_repo()
    if not repo:
        return []
    
    try:
        # Get the diff between branches
        diff = repo.git.diff('--name-only', f'{target_branch}...{source_branch}')
        if not diff.strip():
            return []
        return [line.strip() for line in diff.split('\n') if line.strip()]
    except GitCommandError:
        return []

def get_file_content_at_branch(filepath, branch):
    """Get file content at a specific branch"""
    repo = get_ctx_repo()
    if not repo:
        return None
    
    try:
        return repo.git.show(f'{branch}:{filepath}')
    except GitCommandError:
        return None

def detect_merge_conflicts(source_branch, target_branch='main'):
    """Detect potential merge conflicts between branches"""
    conflicts = []
    changed_files = get_changed_files(source_branch, target_branch)
    
    for filepath in changed_files:
        target_content = get_file_content_at_branch(filepath, target_branch)
        source_content = get_file_content_at_branch(filepath, source_branch)
        
        if target_content is not None and source_content is not None:
            if target_content != source_content:
                conflicts.append({
                    'file': filepath,
                    'target_content': target_content,
                    'source_content': source_content
                })
    
    return conflicts

def show_merge_preview(source_branch, target_branch='main'):
    """Show what would happen in a merge"""
    click.echo(f"Merge preview: {source_branch} → {target_branch}")
    click.echo("=" * 50)
    
    changed_files = get_changed_files(source_branch, target_branch)
    conflicts = detect_merge_conflicts(source_branch, target_branch)
    
    if not changed_files:
        click.echo("No changes to merge.")
        return False
    
    click.echo(f"Files that would be affected: {len(changed_files)}")
    for filepath in changed_files:
        click.echo(f"  • {filepath}")
    
    if conflicts:
        click.echo(f"\n⚠️  Potential conflicts detected: {len(conflicts)}")
        for conflict in conflicts:
            click.echo(f"  • {conflict['file']}")
        return True
    else:
        click.echo(f"\n✓ No conflicts detected. Merge should be clean.")
        return False

def perform_merge(source_branch, target_branch='main'):
    """Perform the actual merge"""
    repo = get_ctx_repo()
    if not repo:
        click.echo("Error: No ctx repository found", err=True)
        return False
    
    try:
        # Switch to target branch
        repo.git.checkout(target_branch)
        click.echo(f"Switched to {target_branch}")
        
        # Perform merge
        repo.git.merge(source_branch, '--no-edit')
        click.echo(f"✓ Successfully merged {source_branch} into {target_branch}")
        return True
        
    except GitCommandError as e:
        click.echo(f"Merge failed: {e}", err=True)
        click.echo("You may need to resolve conflicts manually in the ctx/ directory.")
        return False

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
    # Ensure ctx.config exists first
    ensure_ctx_config()
    
    # Use custom_dir if provided, otherwise use directory argument
    target_dir = custom_dir if custom_dir else directory
    ctx_dir = Path(target_dir)
    
    if ctx_dir.exists():
        click.echo(f"Error: Directory '{target_dir}' already exists", err=True)
        sys.exit(1)
    
    # Create directory
    ctx_dir.mkdir(parents=True)

    # Copy template files
    template_dir = get_template_dir()
    if not template_dir.exists():
        click.echo(f"Error: Template directory not found at {template_dir}", err=True)
        sys.exit(1)
    
    click.echo(f"Creating '{target_dir}' directory and copying template files...")
    
    # Copy all files from template directory
    for template_file in template_dir.glob('*'):
        if template_file.is_file():
            dest_file = ctx_dir / template_file.name
            shutil.copy2(template_file, dest_file)
            click.echo(f"Copied {template_file.name}")
    
    # Create .ctx marker file
    ctx_marker = ctx_dir / '.ctx'
    ctx_marker.touch()
    click.echo("Created .ctx marker file")
    
    click.echo(f"Initializing git repository in '{target_dir}'...")

    # Initialize the git repo in the directory
    try:
        repo = Repo.init(ctx_dir)
        
        # Add all files to git (including .ctx marker)
        repo.git.add('-A')
        
        # Commit the initial files
        repo.index.commit('first commit')
        
        click.echo(f"✓ ctx repository initialized successfully in '{target_dir}'")
        click.echo(f"✓ Files committed with 'first commit' message")
        
        # Add to config as the active ctx repository
        add_ctx_to_config(ctx_dir.absolute(), set_as_active=True)
        click.echo(f"✓ Added '{target_dir}' to ctx config as active repository")
        
        click.echo("")
        click.echo("Next steps:")
        click.echo(f"1. cd {target_dir}")
        click.echo(f"2. Edit ctx.txt with your context")
        click.echo("3. Start exploring ideas on feature branches!")
        
    except Exception as e:
        click.echo(f"Error initializing git repository: {e}", err=True)
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
    ensure_ctx_repo()
    
    # Validate branches exist
    all_branches = get_all_branches()
    if exploration not in all_branches:
        click.echo(f"Error: Exploration '{exploration}' does not exist", err=True)
        click.echo(f"Available explorations: {', '.join(all_branches)}")
        sys.exit(1)
    
    if target not in all_branches:
        click.echo(f"Error: Target branch '{target}' does not exist", err=True)
        sys.exit(1)
    
    if exploration == target:
        click.echo(f"Error: Cannot integrate exploration into itself", err=True)
        sys.exit(1)
    
    # Show preview
    has_conflicts = show_merge_preview(exploration, target)
    
    if preview:
        return
    
    if has_conflicts:
        if not click.confirm(f"\n⚠️  Conflicts detected. Proceed with integration anyway?"):
            click.echo("Integration cancelled.")
            return
    
    # Perform the integration
    click.echo(f"\nProceeding with integration...")
    if perform_merge(exploration, target):
        click.echo(f"\n🎉 Insights from '{exploration}' successfully integrated into '{target}'!")
    else:
        click.echo(f"\n❌ Integration failed. Check the ctx/ directory for any conflicts that need manual resolution.")

@main.command()
def status():
    """Show current ctx repository status"""
    ensure_ctx_repo()
    
    ctx_dir = get_ctx_dir()
    if ctx_dir:
        click.echo(f"ctx repository: {ctx_dir.name} ({ctx_dir.absolute()})")
    
    current_branch = get_current_branch()
    all_branches = get_all_branches()
    
    click.echo(f"Current branch: {current_branch}")
    click.echo(f"All branches: {', '.join(all_branches)}")
    
    # Show git status
    repo = get_ctx_repo()
    if repo:
        try:
            if repo.is_dirty():
                click.echo("\nUncommitted changes:")
                for item in repo.git.status('--porcelain').split('\n'):
                    if item.strip():
                        click.echo(f"  {item}")
            else:
                click.echo("\nWorking tree clean")
        except:
            click.echo("\nCould not get repository status")

@main.command()
@click.argument('topic')
def explore(topic):
    """Start exploring a new topic or idea
    
    Git equivalent: git checkout -b <topic>
    """
    ensure_ctx_repo()
    
    repo = get_ctx_repo()
    if not repo:
        click.echo("Error: No ctx repository found", err=True)
        sys.exit(1)
    
    try:
        # Create and checkout new branch
        new_branch = repo.create_head(topic)
        new_branch.checkout()
        click.echo(f"✓ Started exploring '{topic}'")
        click.echo("Document your ideas and insights as you explore!")
        
    except Exception as e:
        click.echo(f"Error starting exploration: {e}", err=True)
        sys.exit(1)

@main.command()
@click.argument('message')
def capture(message):
    """Capture current insights and thinking
    
    Git equivalent: git add . && git commit -m "<message>"
    """
    ensure_ctx_repo()
    
    repo = get_ctx_repo()
    if not repo:
        click.echo("Error: No ctx repository found", err=True)
        sys.exit(1)
    
    try:
        # Check if there are any changes to commit
        if not repo.is_dirty(untracked_files=True):
            click.echo("No changes to capture.")
            return
        
        # Stage all changes
        repo.git.add('-A')
        
        # Commit with the provided message
        repo.index.commit(message)
        click.echo(f"✓ Captured: {message}")
        
    except Exception as e:
        click.echo(f"Error capturing insights: {e}", err=True)
        sys.exit(1)

@main.command()
def list():
    """List all discovered ctx repositories"""
    config = load_ctx_config()
    
    if not config['discovered_ctx']:
        click.echo("No ctx repositories found in config.")
        click.echo("Run 'ctx new' to create a new ctx repository.")
        return
    
    click.echo("Discovered ctx repositories:")
    click.echo("=" * 50)
    
    for ctx_path in config['discovered_ctx']:
        full_path = Path.cwd() / ctx_path
        is_active = ctx_path == config['active_ctx']
        exists = full_path.exists() and (full_path / '.ctx').exists()
        
        marker = "→ " if is_active else "  "
        status = "✓" if exists else "✗"
        
        click.echo(f"{marker}{status} {ctx_path}")
        if is_active:
            click.echo("     (Currently active)")
        if not exists:
            click.echo("     (Directory missing or invalid)")
        click.echo()

@main.command()
@click.argument('ctx_name')
def switch(ctx_name):
    """Switch to a different ctx repository"""
    config = load_ctx_config()
    
    if ctx_name not in config['discovered_ctx']:
        click.echo(f"Error: ctx repository '{ctx_name}' not found in config", err=True)
        click.echo("Available repositories:")
        for repo in config['discovered_ctx']:
            click.echo(f"  • {repo}")
        sys.exit(1)
    
    # Verify the repository still exists
    ctx_path = Path.cwd() / ctx_name
    
    if not ctx_path.exists() or not (ctx_path / '.ctx').exists():
        click.echo(f"Error: ctx repository '{ctx_name}' directory is missing or invalid", err=True)
        sys.exit(1)
    
    # Switch to the new active repository - update config directly
    config['active_ctx'] = ctx_name
    config_path = Path.cwd() / 'ctx.config'
    try:
        with open(config_path, 'wb') as f:
            tomli_w.dump(config, f)
        click.echo(f"✓ Switched to ctx repository: {ctx_name}")
    except Exception as e:
        click.echo(f"Error saving config: {e}", err=True)
        sys.exit(1)

if __name__ == "__main__":
    main()