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

def is_gid_repo():
    """Check if current directory is a gid repository"""
    return Path('.git').exists() and Path('.gid').exists()

def ensure_gid_repo():
    """Ensure we're in a gid repository"""
    if not is_gid_repo():
        click.echo("Error: Not in a gid repository. Run 'gid init' first.", err=True)
        sys.exit(1)

def get_template_dir():
    """Get the path to the template directory"""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    return script_dir / "template"

@click.group()
@click.version_option()
def main():
    """gid: git for ideas - collaborative memory for humans and LLMs"""
    pass

@main.command()
def init():
    """Initialize a new gid repository"""
    if Path('.gid').exists():
        click.echo("Error: .gid directory already exists", err=True)
        sys.exit(1)
    
    # Initialize git repo if not already initialized
    if not Path('.git').exists():
        click.echo("Initializing git repository...")
        run_git(['init'], capture_output=False)
    
    # Create .gid directory
    gid_dir = Path('.gid')
    gid_dir.mkdir()
    
    # Copy template files
    template_dir = get_template_dir()
    if not template_dir.exists():
        click.echo(f"Error: Template directory not found at {template_dir}", err=True)
        sys.exit(1)
    
    click.echo("Creating .gid directory and copying template files...")
    
    # Copy all files from template directory
    for template_file in template_dir.glob('*'):
        if template_file.is_file():
            dest_file = gid_dir / template_file.name
            shutil.copy2(template_file, dest_file)
            click.echo(f"Copied {template_file.name}")
    
    # Add .gid to git
    run_git(['add', '.gid/'], capture_output=False)
    
    click.echo("✓ gid repository initialized successfully!")
    click.echo("✓ Template files copied to .gid/")
    click.echo("✓ Files staged for commit")
    click.echo("")
    click.echo("Next steps:")
    click.echo("1. git commit -m 'Initial gid setup'")
    click.echo("2. Edit .gid/goals.txt with your project goals")
    click.echo("3. Start exploring ideas on feature branches!")

if __name__ == "__main__":
    main()
