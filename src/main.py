#!/usr/bin/env python3

import click
import os
from pathlib import Path
import sys
import shutil
from git import Repo, InvalidGitRepositoryError, GitCommandError

def get_ctx_dir():
    """Get the ctx directory path"""
    return Path('ctx')

def get_ctx_repo():
    """Get the GitPython repo object for the ctx directory"""
    ctx_dir = get_ctx_dir()
    if not ctx_dir.exists():
        return None
    try:
        return Repo(ctx_dir)
    except InvalidGitRepositoryError:
        return None

def is_ctx_repo():
    """Check if current directory is a ctx repository"""
    return get_ctx_repo() is not None

def ensure_ctx_repo():
    """Ensure we're in a ctx repository"""
    if not is_ctx_repo():
        click.echo("Error: Not in a ctx repository. Run 'ctx init' first.", err=True)
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
    """ctx: collaborative memory for humans and LLMs"""
    pass

@main.command()
def init():
    """Initialize a new ctx repository"""
    if Path('ctx').exists():
        click.echo("Error: ctx directory already exists", err=True)
        sys.exit(1)
    
    # Create ctx directory
    ctx_dir = Path('ctx')
    ctx_dir.mkdir()

    # Copy template files
    template_dir = get_template_dir()
    if not template_dir.exists():
        click.echo(f"Error: Template directory not found at {template_dir}", err=True)
        sys.exit(1)
    
    click.echo("Creating ctx directory and copying template files...")
    
    # Copy all files from template directory
    for template_file in template_dir.glob('*'):
        if template_file.is_file():
            dest_file = ctx_dir / template_file.name
            shutil.copy2(template_file, dest_file)
            click.echo(f"Copied {template_file.name}")
    
    click.echo("Initializing ctx repository...")

    # Initialize the git repo in the ctx directory
    try:
        repo = Repo.init(ctx_dir)
        
        # Add all files to git
        repo.git.add('-A')
        
        # Commit the initial files
        repo.index.commit('first commit')
        
        click.echo(f"✓ ctx repository initialized successfully in {ctx_dir}")
        click.echo(f"✓ Files committed with 'first commit' message in {ctx_dir}")
        click.echo("")
        click.echo("Next steps:")
        click.echo(f"1. Edit {ctx_dir}/ctx.txt with your context")
        click.echo("2. Start exploring ideas on feature branches!")
        
    except Exception as e:
        click.echo(f"Error initializing git repository: {e}", err=True)
        sys.exit(1)

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

if __name__ == "__main__":
    main()