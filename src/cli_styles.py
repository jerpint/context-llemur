#!/usr/bin/env python3

import click
import shutil
from typing import List, Optional

def get_terminal_width() -> int:
    """Get terminal width, default to 80 if not available"""
    try:
        return shutil.get_terminal_size().columns
    except:
        return 80

def print_banner():
    """Print the main ctx banner"""
    banner = """
╭───────────────────────────────────────────────────────────╮
│                                                           │
│               ░██████  ░██████████░██    ░██              │ 
│              ░██   ░██     ░██     ░██  ░██               │
│             ░██            ░██      ░██░██                │
│             ░██            ░██       ░███                 │
│             ░██            ░██      ░██░██                │
│              ░██   ░██     ░██     ░██  ░██               │
│               ░██████      ░██    ░██    ░██              │
│                                                           │
│                                                           │
╰───────────────────────────────────────────────────────────╯
    """
    click.echo(click.style(banner, fg='cyan', bold=True))

def print_section_header(title: str, icon: str = "📋"):
    """Print a beautiful, compact section header"""
    width = get_terminal_width()
    if width < 60:
        # Simple format for narrow terminals
        click.echo(f"\n{icon} {title}")
        click.echo("─" * min(len(title) + 4, width - 2))
    else:
        # Compact format for wider terminals
        title_text = f"{icon} {title}"
        box_width = min(len(title_text) + 4, width - 2)
        border = "─" * (box_width - 1)
        click.echo(f"\n╭{border}╮")
        click.echo(f"│ {click.style(title_text, bold=True, fg='blue')} │")
        click.echo(f"╰{border}╯")

def print_success_box(message: str, icon: str = "✨"):
    """Print a success message in a nice box"""
    lines = message.split('\n')
    max_len = max(len(line) for line in lines) + 4
    width = min(max_len, get_terminal_width() - 4)
    
    click.echo(f"\n╭{'─' * width}╮")
    for line in lines:
        padded_line = f" {icon} {line}".ljust(width - 1)
        click.echo(f"│{click.style(padded_line, fg='green', bold=True)}│")
    click.echo(f"╰{'─' * width}╯")

def print_warning_box(message: str, icon: str = "⚠️"):
    """Print a warning message in a nice box"""
    lines = message.split('\n')
    max_len = max(len(line) for line in lines) + 4
    width = min(max_len, get_terminal_width() - 4)
    
    click.echo(f"\n╭{'─' * width}╮")
    for line in lines:
        padded_line = f" {icon} {line}".ljust(width - 1)
        click.echo(f"│{click.style(padded_line, fg='yellow', bold=True)}│")
    click.echo(f"╰{'─' * width}╯")

def print_error_box(message: str, icon: str = "❌"):
    """Print an error message in a nice box"""
    lines = message.split('\n')
    max_len = max(len(line) for line in lines) + 4
    width = min(max_len, get_terminal_width() - 4)
    
    click.echo(f"\n╭{'─' * width}╮")
    for line in lines:
        padded_line = f" {icon} {line}".ljust(width - 1)
        click.echo(f"│{click.style(padded_line, fg='red', bold=True)}│")
    click.echo(f"╰{'─' * width}╯")

def print_repository_card(name: str, is_active: bool = False, exists: bool = True, path: Optional[str] = None):
    """Print a beautiful repository card"""
    width = min(50, get_terminal_width() - 4)
    
    # Choose colors and icons based on status
    if is_active:
        border_color = 'green'
        status_icon = "🟢"
        status_text = "ACTIVE"
    elif exists:
        border_color = 'blue'
        status_icon = "🔵"
        status_text = "READY"
    else:
        border_color = 'red'
        status_icon = "🔴"
        status_text = "MISSING"
    
    # Build the card
    click.echo(f"╭{'─' * (width - 2)}╮")
    
    # Title line
    title_line = f" {status_icon} {name}"
    status_line = f"{status_text} "
    padding = width - len(title_line) - len(status_line) - 2
    click.echo(f"│{click.style(title_line, bold=True)}{' ' * padding}{click.style(status_line, fg=border_color, bold=True)}│")
    
    # Path line if provided
    if path:
        path_line = f" 📁 {path}"
        if len(path_line) > width - 2:
            path_line = f" 📁 ...{path[-(width-10):]}"
        padding = width - len(path_line) - 2
        click.echo(f"│{click.style(path_line, fg='white', dim=True)}{' ' * padding}│")
    
    click.echo(f"╰{'─' * (width - 2)}╯\n")

def print_branch_tree(current_branch: str, all_branches: List[str]):
    """Print a beautiful branch tree"""
    click.echo(f"\n🌳 {click.style('Branch Tree', bold=True, fg='green')}")
    click.echo("├─" + "─" * 30)
    
    for i, branch in enumerate(all_branches):
        is_current = branch == current_branch
        is_last = i == len(all_branches) - 1
        
        if is_current:
            prefix = "├─➤ " if not is_last else "└─➤ "
            branch_text = click.style(f"{branch} (current)", bold=True, fg='green')
        else:
            prefix = "├── " if not is_last else "└── "
            branch_text = click.style(branch, fg='blue')
        
        click.echo(f"{prefix}{branch_text}")

def print_status_summary(repository_name: str, current_branch: str, all_branches: List[str], 
                        is_dirty: bool, uncommitted_changes: List[str], repo_path: str):
    """Print a beautiful status summary"""
    print_section_header("Repository Status", "📊")
    
    # Repository info box
    click.echo(f"\n📦 {click.style('Repository:', bold=True)} {click.style(repository_name, fg='cyan', bold=True)}")
    click.echo(f"📍 {click.style('Location:', bold=True)} {click.style(repo_path, fg='white', dim=True)}")
    
    # Branch tree
    print_branch_tree(current_branch, all_branches)
    
    # Changes status
    if is_dirty:
        print_warning_box(f"Working tree has {len(uncommitted_changes)} uncommitted changes")
        click.echo(f"\n📝 {click.style('Uncommitted Changes:', bold=True, fg='yellow')}")
        for change in uncommitted_changes:
            click.echo(f"   • {change}")
    else:
        print_success_box("Working tree is clean", "✨")

def print_integration_preview(source: str, target: str, changed_files: List[str], 
                            has_conflicts: bool, conflicts: List[dict]):
    """Print a beautiful integration preview"""
    print_section_header("Integration Preview", "🔀")
    
    # Source and target
    click.echo(f"\n{click.style('Source:', bold=True)} {click.style(source, fg='blue', bold=True)}")
    click.echo(f"{click.style('Target:', bold=True)} {click.style(target, fg='green', bold=True)}")
    
    if not changed_files:
        print_success_box("No changes to merge", "ℹ️")
        return
    
    # Files to be changed
    click.echo(f"\n📄 {click.style('Files to be modified:', bold=True)} {len(changed_files)}")
    for file in changed_files:
        click.echo(f"   • {file}")
    
    # Conflicts
    if has_conflicts:
        print_warning_box(f"⚠️  {len(conflicts)} potential conflicts detected")
        for conflict in conflicts:
            click.echo(f"   • {conflict['file']}")
    else:
        print_success_box("No conflicts detected - merge should be clean", "✅")

def print_celebration():
    """Print a celebration ASCII art"""
    celebration = """
    ╭───────────────╮
    │    Success!   │
    ╰───────────────╯
    """
    click.echo(click.style(celebration, fg='green', bold=True))

def print_explore_banner(topic: str):
    """Print exploration start banner"""
    banner = f"""
🔍 Starting Exploration: {topic}
{"─" * (25 + len(topic))}
Ready to capture insights and ideas!
    """
    click.echo(click.style(banner, fg='blue', bold=True)) 