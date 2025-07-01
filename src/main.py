#!/usr/bin/env python3

import click
import subprocess
import os
from pathlib import Path
import sys
import shutil

def run_git(cmd, capture_output=True):
    """Run git command and return result"""
    try:
        if capture_output:
            return subprocess.run(['git'] + cmd, capture_output=True, text=True, check=True)
        else:
            return subprocess.run(['git'] + cmd, check=True)
    except subprocess.CalledProcessError as e:
        click.echo(f"Git error: {e}", err=True)
        sys.exit(1)

def is_ctx_repo():
    """Check if current directory is a ctx repository"""
    return Path('.git').exists() and Path('.ctx').exists()

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

@click.group()
@click.version_option()
def main():
    """ctx: collaborative memory for humans and LLMs"""
    pass

@main.command()
def init():
    """Initialize a new ctx repository"""
    if Path('.ctx').exists():
        click.echo("Error: .ctx directory already exists", err=True)
        sys.exit(1)
    
    
    current_dir = Path.cwd()

    # Create ctx directory
    ctx_dir = Path('ctx')
    ctx_dir.mkdir()

    
    # Copy template files
    template_dir = get_template_dir()
    if not template_dir.exists():
        click.echo(f"Error: Template directory not found at {template_dir}", err=True)
        sys.exit(1)
    
    click.echo("Creating .ctx directory and copying template files...")
    
    # Copy all files from template directory
    for template_file in template_dir.glob('*'):
        if template_file.is_file():
            dest_file = ctx_dir / template_file.name
            shutil.copy2(template_file, dest_file)
            click.echo(f"Copied {template_file.name}")
    
    click.echo("Initializing ctx repository...")

    # intialize the git repo in the .ctx directory
    os.chdir(ctx_dir)
    run_git(['init'], capture_output=False)

    # Add .ctx to git
    run_git(['add', '-A'], capture_output=False)
    
    # Commit the initial files
    run_git(['commit', '-m', 'first commit'], capture_output=False)

    os.chdir(current_dir)
    
    click.echo(f"✓ ctx repository initialized successfully in {ctx_dir}")
    click.echo(f"✓ Files committed with 'first commit' message in {ctx_dir}")
    click.echo("")
    click.echo("Next steps:")
    click.echo(f"1. Edit {ctx_dir}/ctx.txt with your context")
    click.echo("2. Start exploring ideas on feature branches!")

if __name__ == "__main__":
    main()