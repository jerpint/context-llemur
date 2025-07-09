#!/usr/bin/env python3
"""
MCP Server for ctx - Collaborative Memory for Humans and LLMs

This MCP server provides AI agents with persistent, version-controlled memory
through the ctx system. It offers repository management, semantic workflows,
file operations, and navigation capabilities.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from fastmcp import FastMCP
from src.ctx_core import CtxCore, OperationResult

# Initialize the MCP server
mcp = FastMCP("ctx-server")

# Initialize the core logic
core = CtxCore()

def format_ctx_show_all(directory: str = "", branch: str = "", pattern: str = "") -> str:
    """Display all file contents with clear delimiters for LLM context absorption.
    
    This command shows the entire repository state in one output, perfect for providing
    complete context to LLM agents.
    
    Args:
        directory: Optional directory to show (relative to ctx root)
        branch: Optional branch to show files from (default: current branch)
        pattern: Optional file pattern to filter (e.g., "*.md")
        
    Returns:
        Formatted output with all file contents and clear delimiters
    """
    # Convert empty strings to None for the core logic
    dir_param = directory if directory else None
    branch_param = branch if branch else None
    pattern_param = pattern if pattern else None
    
    result = core.show_all(directory=dir_param, branch=branch_param, pattern=pattern_param)
    
    if not result.success:
        return f"❌ {result.error}"
    
    show_result = result.data
    
    # Build formatted output
    output = "=" * 80 + "\n"
    output += "📁 CTX REPOSITORY CONTENTS\n"
    output += "=" * 80 + "\n"
    output += f"Branch: {show_result.branch}\n"
    if show_result.directory:
        output += f"Directory: {show_result.directory}\n"
    if show_result.pattern:
        output += f"Pattern: {show_result.pattern}\n"
    output += f"Total files: {show_result.total_files}\n\n"
    
    # Add each file with clear delimiters
    for i, file_info in enumerate(show_result.files):
        output += "=" * 80 + "\n"
        output += f"📄 FILE {i+1}/{show_result.total_files}: {file_info['path']}\n"
        output += f"📊 Size: {file_info['size']} chars, Lines: {file_info['lines']}\n"
        output += "=" * 80 + "\n\n"
        output += file_info['content']
        output += "\n\n"
    
    output += "=" * 80 + "\n"
    output += "✅ REPOSITORY CONTENTS COMPLETE\n"
    output += "=" * 80 + "\n"
    
    return output

# === Repository Management Tools ===

@mcp.tool
def ctx_show_all(directory: str = "", branch: str = "", pattern: str = "") -> str:
    """Display all file contents with clear delimiters for LLM context absorption.
    
    This command shows the entire repository state in one output, perfect for providing
    complete context to LLM agents.
    
    Args:
        directory: Optional directory to show (relative to ctx root)
        branch: Optional branch to show files from (default: current branch)
        pattern: Optional file pattern to filter (e.g., "*.md")
        
    Returns:
        Formatted output with all file contents and clear delimiters
    """
    return format_ctx_show_all(directory, branch, pattern)


@mcp.tool
def ctx_load() -> str:
    """Load the current ctx repository.

    ctx is a system for collaborative memory for LLMs and humans.

    When a user calls ctx load, just run this function to get all the context you need.

    
    Returns:
        Success message and repository details
    """
    show_all_str = format_ctx_show_all()
    return show_all_str

@mcp.tool
def ctx_new(directory: str = "context") -> str:
    """Create a new ctx repository for collaborative memory.
    
    Args:
        directory: Name of the directory to create (default: "context")
        
    Returns:
        Success message and repository details
    """
    result = core.create_new_ctx(directory)
    
    if result.success:
        return f"✅ {result.message}\n\nRepository created at: {directory}"
    else:
        return f"❌ {result.error}"

@mcp.tool
def ctx_status() -> str:
    """Get the status of the current ctx repository.
    
    Returns:
        Repository status including current branch, changes, and metadata
    """
    result = core.get_status()
    
    if result.success:
        status = result.data
        if status:
            repo_info = status.repository
            output = f"📊 Repository Status\n\n"
            output += f"Repository: {repo_info.name}\n"
            output += f"Current Branch: {status.current_branch}\n"
            output += f"All Branches: {', '.join(status.all_branches)}\n"
            output += f"Has Changes: {'Yes' if status.is_dirty else 'No'}\n"
            
            if status.uncommitted_changes:
                output += f"\nUncommitted Changes:\n"
                for change in status.uncommitted_changes:
                    output += f"  • {change}\n"
            
            return output
        else:
            return result.message
    else:
        return f"❌ {result.error}"

@mcp.tool
def ctx_list() -> str:
    """List all available ctx repositories.
    
    Returns:
        List of discovered repositories with their status
    """
    result = core.list_repositories()
    
    if result.success:
        repositories = result.data
        if not repositories:
            return "📂 No ctx repositories found\n\nUse ctx_new() to create your first repository."
        
        output = "📂 Available ctx repositories:\n\n"
        for repo in repositories:
            status = "🟢 Active" if repo.is_active else "⚪ Available"
            validity = "✅ Valid" if repo.is_valid else "❌ Invalid"
            output += f"  {status} {repo.name} - {validity}\n"
            output += f"    Path: {repo.path}\n\n"
        
        return output
    else:
        return f"❌ {result.error}"

@mcp.tool
def ctx_switch(repository_name: str) -> str:
    """Switch to a different ctx repository.
    
    Args:
        repository_name: Name of the repository to switch to
        
    Returns:
        Success message confirming the switch
    """
    result = core.switch_repository(repository_name)
    
    if result.success:
        return f"✅ {result.message}"
    else:
        available = result.data.get('available_repositories', []) if result.data else []
        error_msg = f"❌ {result.error}"
        if available:
            error_msg += f"\n\nAvailable repositories: {', '.join(available)}"
        return error_msg

# === Semantic Workflow Tools ===

@mcp.tool
def ctx_explore(topic: str) -> str:
    """Start exploring a new topic by creating a new branch.
    
    Args:
        topic: The topic or question to explore
        
    Returns:
        Success message and branch information
    """
    result = core.start_exploration(topic)
    
    if result.success:
        return f"🔍 {result.message}\n\nYou're now on branch '{topic}' ready to explore this topic."
    else:
        return f"❌ {result.error}"

@mcp.tool
def ctx_save(message: str) -> str:
    """Saves the current state of the context repository.
    
    Args:
        message: Description of what you're saving
        
    Returns:
        Success message confirming the save
    """
    result = core.save(message)
    
    if result.success:
        return f"💾 {result.message}"
    else:
        return f"❌ {result.error}"

@mcp.tool
def ctx_discard(force: bool = False) -> str:
    """Reset to last commit, dropping all changes.
    
    This performs a git reset --hard HEAD operation, which:
    - Removes all staged changes
    - Removes all unstaged changes
    - Resets all files to their state at the last commit
    - With force=True: also removes untracked files and directories
    
    Args:
        force: If True, also removes untracked files and directories (default: False)
        
    Returns:
        Success message confirming the discard operation
    """
    result = core.discard(force=force)
    
    if result.success:
        return f"🗑️ {result.message}"
    else:
        return f"❌ {result.error}"

@mcp.tool
def ctx_integrate(source_branch: str, target_branch: str = "main") -> str:
    """Integrate insights from one branch into another.
    
    Args:
        source_branch: The branch with insights to integrate
        target_branch: The branch to integrate into (default: "main")
        
    Returns:
        Success message or conflict information
    """
    # First get a preview to check for conflicts
    preview_result = core.get_merge_preview(source_branch, target_branch)
    
    if not preview_result.success:
        return f"❌ {preview_result.error}"
    
    preview = preview_result.data
    
    if preview.has_conflicts:
        output = f"⚠️ Merge conflicts detected!\n\n"
        output += f"Conflicts in {len(preview.conflicts)} files:\n"
        for conflict in preview.conflicts:
            output += f"  • {conflict.get('file', 'Unknown file')}\n"
        output += f"\nResolve conflicts manually before integrating."
        return output
    
    # Perform the integration
    result = core.perform_integration(source_branch, target_branch)
    
    if result.success:
        return f"🔄 {result.message}"
    else:
        return f"❌ {result.error}"

@mcp.tool
def ctx_diff(staged: bool = False, source_branch: str = "", target_branch: str = "") -> str:
    """Get differences between branches or current changes.
    
    Args:
        staged: Show only staged changes (default: False)
        source_branch: First branch to compare (optional)
        target_branch: Second branch to compare (optional)
        
    Returns:
        Diff output showing changes
    """
    branches = []
    if source_branch:
        branches.append(source_branch)
    if target_branch:
        branches.append(target_branch)
    
    result = core.get_diff(staged=staged, branches=branches if branches else None)
    
    if result.success:
        diff_data = result.data
        if not diff_data['has_changes']:
            return "📄 No changes to show"
        
        output = "📋 Diff Results\n\n"
        if diff_data['staged']:
            output += "Type: Staged changes\n"
        elif diff_data['branches']:
            if len(diff_data['branches']) == 1:
                output += f"Type: Changes vs {diff_data['branches'][0]}\n"
            else:
                output += f"Type: Changes between {diff_data['branches'][0]} and {diff_data['branches'][1]}\n"
        else:
            output += "Type: Current changes\n"
        
        output += "=" * 50 + "\n"
        output += diff_data['diff']
        return output
    else:
        return f"❌ {result.error}"

# === File Operations Tools ===

@mcp.tool
def ctx_read_file(filepath: str, branch: str = "") -> str:
    """Read a specific file from the ctx repository.
    
    Args:
        filepath: Path to the file relative to ctx root
        branch: Optional branch to read from (default: current branch)
        
    Returns:
        File contents or error message
    """
    if not core.is_ctx_repo():
        return "❌ Not in a ctx repository"
    
    try:
        if branch:
            # Read from specific branch
            content = core.get_file_content_at_branch(filepath, branch)
            if content is None:
                return f"❌ File '{filepath}' not found in branch '{branch}'"
            return f"📄 {filepath} (branch: {branch})\n{'=' * 50}\n{content}"
        else:
            # Read from current working directory
            ctx_root = core.get_active_ctx_path()
            if not ctx_root:
                return "❌ Could not find ctx root"
            
            file_path = ctx_root / filepath
            if not file_path.exists():
                return f"❌ File '{filepath}' not found"
            
            if not file_path.is_file():
                return f"❌ '{filepath}' is not a file"
            
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            return f"📄 {filepath}\n{'=' * 50}\n{content}"
    
    except Exception as e:
        return f"❌ Error reading file: {e}"

@mcp.tool
def ctx_write_file(filepath: str, content: str) -> str:
    """Write content to a file in the ctx repository.
    
    Args:
        filepath: Path to the file to write
        content: Content to write to the file
        
    Returns:
        Success message or error
    """
    ctx_root = core.get_active_ctx_path()
    if not ctx_root:
        return "❌ Not in a ctx repository"
    
    try:
        file_path = ctx_root / filepath
        
        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return f"✅ File '{filepath}' written successfully"
    except Exception as e:
        return f"❌ Error writing file: {e}"

@mcp.tool
def ctx_list_files(directory: str = "") -> str:
    """List files in the ctx repository.
    
    Args:
        directory: Directory to list (default: root of repository)
        
    Returns:
        List of files and directories
    """
    ctx_root = core.get_active_ctx_path()
    if not ctx_root:
        return "❌ Not in a ctx repository"
    
    try:
        target_dir = ctx_root / directory if directory else ctx_root
        
        if not target_dir.exists():
            return f"❌ Directory '{directory}' not found"
        
        if not target_dir.is_dir():
            return f"❌ '{directory}' is not a directory"
        
        output = f"📁 Files in {directory or 'repository root'}:\n\n"
        
        # Get all items, sorted with directories first
        items = list(target_dir.iterdir())
        items.sort(key=lambda x: (x.is_file(), x.name))
        
        for item in items:
            if item.name.startswith('.'):
                continue  # Skip hidden files
            
            icon = "📁" if item.is_dir() else "📄"
            rel_path = item.relative_to(ctx_root)
            output += f"  {icon} {rel_path}\n"
        
        return output
    except Exception as e:
        return f"❌ Error listing files: {e}"

# === Navigation Tools ===

@mcp.tool
def ctx_get_branches() -> str:
    """Get all branches in the ctx repository.
    
    Returns:
        List of all branches with current branch highlighted
    """
    if not core.is_ctx_repo():
        return "❌ Not in a ctx repository"
    
    try:
        current_branch = core.get_current_branch()
        all_branches = core.get_all_branches()
        
        output = "🌿 Repository branches:\n\n"
        for branch in all_branches:
            indicator = "→" if branch == current_branch else " "
            output += f"  {indicator} {branch}\n"
        
        return output
    except Exception as e:
        return f"❌ Error getting branches: {e}"

@mcp.tool
def ctx_get_history(branch: str = "", limit: int = 10) -> str:
    """Get commit history for a branch.
    
    Args:
        branch: Branch to get history for (default: current branch)
        limit: Maximum number of commits to show (default: 10)
        
    Returns:
        Commit history with messages and dates
    """
    if not core.is_ctx_repo():
        return "❌ Not in a ctx repository"
    
    repo = core.get_ctx_repo()
    if not repo:
        return "❌ No ctx repository found"
    
    try:
        if branch:
            # Get history for specific branch
            if branch not in core.get_all_branches():
                return f"❌ Branch '{branch}' not found"
            target_branch = repo.heads[branch]
        else:
            # Get history for current branch
            target_branch = repo.active_branch
            branch = target_branch.name
        
        commits = list(repo.iter_commits(target_branch, max_count=limit))
        
        output = f"📜 History for branch '{branch}' (last {min(len(commits), limit)} commits):\n\n"
        
        for commit in commits:
            # Format commit date
            date_str = commit.committed_datetime.strftime("%Y-%m-%d %H:%M")
            
            # Get short hash
            short_hash = commit.hexsha[:7]
            
            # Get commit message (first line only)
            message = str(commit.message).strip().split('\n')[0]
            
            output += f"  {short_hash} - {date_str}\n"
            output += f"    {message}\n\n"
        
        return output
    except Exception as e:
        return f"❌ Error getting history: {e}"

@mcp.tool
def ctx_search_content(query: str, file_pattern: str = "*") -> str:
    """Search for content within files in the ctx repository.
    
    Args:
        query: Text to search for
        file_pattern: File pattern to search in (default: "*" for all files)
        
    Returns:
        Search results with file paths and line numbers
    """
    ctx_root = core.get_active_ctx_path()
    if not ctx_root:
        return "❌ Not in a ctx repository"
    
    try:
        import fnmatch
        
        matches = []
        
        # Walk through all files in the repository
        for file_path in ctx_root.rglob('*'):
            # Skip directories and hidden files
            if file_path.is_dir() or file_path.name.startswith('.'):
                continue
            
            # Check if file matches pattern
            rel_path = file_path.relative_to(ctx_root)
            if not fnmatch.fnmatch(str(rel_path), file_pattern):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        if query.lower() in line.lower():
                            matches.append({
                                'file': str(rel_path),
                                'line': line_num,
                                'content': line.strip()
                            })
            except (UnicodeDecodeError, PermissionError):
                # Skip binary files or files we can't read
                continue
        
        if not matches:
            return f"🔍 No matches found for '{query}'"
        
        output = f"🔍 Found {len(matches)} matches for '{query}':\n\n"
        
        current_file = None
        for match in matches:
            if match['file'] != current_file:
                current_file = match['file']
                output += f"📄 {current_file}:\n"
            
            output += f"  Line {match['line']}: {match['content']}\n"
        
        return output
    except Exception as e:
        return f"❌ Error searching content: {e}"

# === Server Entry Point ===

def run_server():
    """Run the MCP server"""
    mcp.run()

if __name__ == "__main__":
    run_server() 