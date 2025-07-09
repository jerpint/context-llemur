#!/usr/bin/env python3

import os
from pathlib import Path
import shutil
import tomllib
import tomli_w
from git import Repo, InvalidGitRepositoryError, GitCommandError
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Union
from enum import Enum
import fnmatch

class OperationResult:
    """Base class for operation results"""
    def __init__(self, success: bool, message: str = "", data: Any = None, error: str = ""):
        self.success = success
        self.message = message
        self.data = data
        self.error = error

@dataclass
class RepositoryInfo:
    """Information about a ctx repository"""
    name: str
    path: Path
    absolute_path: Path
    is_active: bool
    exists: bool
    is_valid: bool

@dataclass
class RepositoryStatus:
    """Status of a ctx repository"""
    repository: RepositoryInfo
    current_branch: str
    all_branches: List[str]
    is_dirty: bool
    uncommitted_changes: List[str]

@dataclass
class MergePreview:
    """Preview of a merge operation"""
    source_branch: str
    target_branch: str
    changed_files: List[str]
    conflicts: List[Dict[str, str]]
    has_conflicts: bool
    is_clean: bool

@dataclass
class ShowAllResult:
    """Result of show_all operation"""
    files: List[Dict[str, Any]]
    total_files: int
    directory: Optional[str]
    branch: str
    pattern: Optional[str]

class CtxCore:
    """Core business logic for ctx operations"""
    
    def __init__(self):
        self._project_root: Optional[Path] = None
    
    @property
    def project_root(self) -> Path:
        if self._project_root is None:
            self._project_root = self.find_project_root()
        return self._project_root

    def find_project_root(self) -> Path:
        """Find the project root by looking for ctx.config file."""
        current_dir = Path.cwd()
        
        # Search upward from current directory
        for parent in [current_dir] + list(current_dir.parents):
            if (parent / 'ctx.config').exists():
                return parent
            
        return current_dir  # Default to current directory if nothing is found
    
    def get_ctx_config_path(self) -> Path:
        """Get the path to the ctx.config file"""
        return self.project_root / 'ctx.config'
    
    def load_ctx_config(self) -> Dict[str, Any]:
        """Load the ctx configuration from ctx.config file"""
        config_path = self.get_ctx_config_path()
        
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
    
    def save_ctx_config(self, config: Dict[str, Any]) -> OperationResult:
        """Save the ctx configuration to ctx.config file"""
        config_path = self.get_ctx_config_path()
        
        try:
            with open(config_path, 'wb') as f:
                tomli_w.dump(config, f)
            return OperationResult(True, "Configuration saved successfully")
        except Exception as e:
            return OperationResult(False, error=f"Could not save config: {e}")
    
    def ensure_ctx_config(self) -> OperationResult:
        """Ensure the ctx.config file exists, creating it if necessary"""
        config_path = self.get_ctx_config_path()
        
        if not config_path.exists():
            default_config = {
                'discovered_ctx': []
            }
            try:
                with open(config_path, 'wb') as f:
                    tomli_w.dump(default_config, f)
                return OperationResult(True, f"Created ctx.config at {str(config_path)}")
            except Exception as e:
                return OperationResult(False, error=f"Could not create ctx.config: {e}")
        
        return OperationResult(True, "ctx.config already exists")
    
    def get_active_ctx_path(self) -> Optional[Path]:
        """
        Find the active ctx repository.
        1. First, check if the current directory is inside a ctx repo by searching upwards for a .ctx file.
        2. If so, that directory is the active context.
        3. If not, fall back to loading the configuration from the project root.
        """
        # 1. Check if we are currently inside a ctx repo
        current_dir = Path.cwd()
        # Search upward from current directory, but not past the project root
        for parent in [current_dir] + list(current_dir.parents):
            if parent == self.project_root.parent:
                break
            if (parent / '.ctx').exists():
                # We found it. This is the active context path.
                return parent

        # 2. If not inside a repo, fall back to config file
        config = self.load_ctx_config()
        active_ctx_name = config.get('active_ctx')
        
        if not active_ctx_name:
            return None
        
        # Use project root to construct path
        ctx_path = self.project_root / active_ctx_name
        
        # Verify it still exists and has .ctx marker
        if ctx_path.exists() and (ctx_path / '.ctx').exists():
            return ctx_path
        
        return None
    
    def get_ctx_repo(self) -> Optional[Repo]:
        """Get the GitPython repo object for the ctx directory"""
        ctx_dir = self.get_active_ctx_path()
        if not ctx_dir:
            return None
        try:
            return Repo(ctx_dir)
        except InvalidGitRepositoryError:
            return None
    
    def is_ctx_repo(self) -> bool:
        """Check if we're in or under a ctx repository"""
        return self.get_active_ctx_path() is not None
    
    def get_template_dir(self) -> Path:
        """Get the path to the template directory"""
        script_dir = Path(__file__).parent
        return script_dir / "template"
    
    def get_current_branch(self) -> str:
        """Get the current git branch name"""
        repo = self.get_ctx_repo()
        if not repo:
            return 'main'
        try:
            return repo.active_branch.name
        except:
            return 'main'
    
    def get_all_branches(self) -> List[str]:
        """Get all git branches"""
        repo = self.get_ctx_repo()
        if not repo:
            return ['main']
        try:
            return [branch.name for branch in repo.branches]
        except:
            return ['main']
    
    def get_changed_files(self, source_branch: str, target_branch: str = 'main') -> List[str]:
        """Get files that differ between two branches"""
        repo = self.get_ctx_repo()
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
    
    def get_file_content_at_branch(self, filepath: str, branch: str) -> Optional[str]:
        """Get file content at a specific branch"""
        repo = self.get_ctx_repo()
        if not repo:
            return None
        
        try:
            return repo.git.show(f'{branch}:{filepath}')
        except GitCommandError:
            return None
    
    def detect_merge_conflicts(self, source_branch: str, target_branch: str = 'main') -> List[Dict[str, str]]:
        """Detect potential merge conflicts between branches"""
        conflicts = []
        changed_files = self.get_changed_files(source_branch, target_branch)
        
        for filepath in changed_files:
            target_content = self.get_file_content_at_branch(filepath, target_branch)
            source_content = self.get_file_content_at_branch(filepath, source_branch)
            
            if target_content is not None and source_content is not None:
                if target_content != source_content:
                    conflicts.append({
                        'file': filepath,
                        'target_content': target_content,
                        'source_content': source_content
                    })
        
        return conflicts
    
    # Core Operations
    
    def create_new_ctx(self, directory: str = 'context') -> OperationResult:
        """Create a new ctx repository"""
        # Ensure ctx.config exists first
        config_result = self.ensure_ctx_config()
        if not config_result.success:
            return config_result
        
        ctx_dir = self.project_root / directory
        
        if ctx_dir.exists():
            # Also check for .ctx marker
            if (ctx_dir / '.ctx').exists():
                return OperationResult(False, error=f"Directory '{directory}' already exists")
        
        # Create directory
        ctx_dir.mkdir(parents=True)
        
        # Copy template files
        template_dir = self.get_template_dir()
        if not template_dir.exists():
            return OperationResult(False, error=f"Template directory not found at {template_dir}")
        
        copied_files = []
        
        # Copy all files from template directory
        for template_file in template_dir.glob('*'):
            if template_file.is_file():
                dest_file = ctx_dir / template_file.name
                shutil.copy2(template_file, dest_file)
                copied_files.append(template_file.name)
        
        # Create .ctx marker file
        ctx_marker = ctx_dir / '.ctx'
        ctx_marker.touch()
        
        # Initialize the git repo in the directory
        try:
            repo = Repo.init(ctx_dir)
            
            # Add all files to git (including .ctx marker)
            repo.git.add('-A')
            
            # Commit the initial files
            repo.index.commit('first commit')
            
            # Add to config as the active ctx repository
            config = self.load_ctx_config()
            
            # Convert to relative path from current directory
            try:
                relative_path = str(ctx_dir.relative_to(Path.cwd()))
            except ValueError:
                relative_path = str(ctx_dir.name)
            
            # Add to discovered list if not already there
            if relative_path not in config['discovered_ctx']:
                config['discovered_ctx'].append(relative_path)
            
            # Set as active
            config['active_ctx'] = relative_path
            
            # Save config
            save_result = self.save_ctx_config(config)
            if not save_result.success:
                return save_result
            
            return OperationResult(
                True, 
                f"ctx repository initialized successfully in '{directory}'",
                data={
                    'directory': directory,
                    'copied_files': copied_files,
                    'relative_path': relative_path
                }
            )
            
        except Exception as e:
            return OperationResult(False, error=f"Error initializing git repository: {e}")
    
    def get_status(self) -> OperationResult:
        """Get the current status of the ctx repository"""
        if not self.is_ctx_repo():
            return OperationResult(False, error="Not in a ctx repository")
        
        ctx_dir = self.get_active_ctx_path()
        if not ctx_dir:
            return OperationResult(False, error="No ctx repository found")
        
        repo_info = RepositoryInfo(
            name=ctx_dir.name,
            path=ctx_dir,
            absolute_path=ctx_dir.absolute(),
            is_active=True,
            exists=True,
            is_valid=True
        )
        
        current_branch = self.get_current_branch()
        all_branches = self.get_all_branches()
        
        repo = self.get_ctx_repo()
        uncommitted_changes = []
        is_dirty = False
        
        if repo:
            try:
                is_dirty = repo.is_dirty()
                if is_dirty:
                    for item in repo.git.status('--porcelain').split('\n'):
                        if item.strip():
                            uncommitted_changes.append(item.strip())
            except:
                pass
        
        status = RepositoryStatus(
            repository=repo_info,
            current_branch=current_branch,
            all_branches=all_branches,
            is_dirty=is_dirty,
            uncommitted_changes=uncommitted_changes
        )
        
        return OperationResult(True, "Status retrieved successfully", data=status)
    
    def start_exploration(self, topic: str) -> OperationResult:
        """Start exploring a new topic or idea"""
        if not self.is_ctx_repo():
            return OperationResult(False, error="Not in a ctx repository")
        
        repo = self.get_ctx_repo()
        if not repo:
            return OperationResult(False, error="No ctx repository found")
        
        try:
            # Create and checkout new branch
            new_branch = repo.create_head(topic)
            new_branch.checkout()
            return OperationResult(True, f"Started exploring '{topic}'", data={'topic': topic})
        except Exception as e:
            return OperationResult(False, error=f"Error starting exploration: {e}")
    
    def save(self, message: str) -> OperationResult:
        """Save the current state of the context repository"""
        if not self.is_ctx_repo():
            return OperationResult(False, error="Not in a ctx repository")
        
        repo = self.get_ctx_repo()
        if not repo:
            return OperationResult(False, error="No ctx repository found")
        
        try:
            # Add all changes
            repo.git.add(A=True)
            
            # Check if there are changes to commit
            if not repo.is_dirty():
                return OperationResult(True, "No changes to save")
            
            # Commit the changes
            repo.index.commit(message)
            
            return OperationResult(True, f"Saved context: {message}")
            
        except Exception as e:
            return OperationResult(False, error=f"Error saving context: {e}")
    
    def discard(self, force: bool = False) -> OperationResult:
        """Discard all changes and reset to the last commit
        
        This performs a git reset --hard HEAD operation, which:
        - Removes all staged changes
        - Removes all unstaged changes
        - Resets all files to their state at the last commit
        
        Args:
            force: If True, also removes untracked files and directories (git clean -fd)
        """
        if not self.is_ctx_repo():
            return OperationResult(False, error="Not in a ctx repository")
        
        repo = self.get_ctx_repo()
        if not repo:
            return OperationResult(False, error="No ctx repository found")
        
        try:
            # Perform hard reset to HEAD
            repo.git.reset('--hard', 'HEAD')
            
            # Only clean untracked files if force is True
            if force:
                repo.git.clean('-fd')
                return OperationResult(True, "All changes discarded and untracked files removed. Reset to last commit.")
            else:
                return OperationResult(True, "All changes discarded. Reset to last commit.")
            
        except GitCommandError as e:
            return OperationResult(False, error=f"Error discarding changes: {e}")
        except Exception as e:
            return OperationResult(False, error=f"Error discarding changes: {e}")
    
    def get_merge_preview(self, source_branch: str, target_branch: str = 'main') -> OperationResult:
        """Get a preview of what would happen in a merge"""
        if not self.is_ctx_repo():
            return OperationResult(False, error="Not in a ctx repository")
        
        # Validate branches exist
        all_branches = self.get_all_branches()
        if source_branch not in all_branches:
            return OperationResult(False, error=f"Exploration '{source_branch}' does not exist")
        
        if target_branch not in all_branches:
            return OperationResult(False, error=f"Target branch '{target_branch}' does not exist")
        
        if source_branch == target_branch:
            return OperationResult(False, error="Cannot integrate exploration into itself")
        
        changed_files = self.get_changed_files(source_branch, target_branch)
        conflicts = self.detect_merge_conflicts(source_branch, target_branch)
        
        preview = MergePreview(
            source_branch=source_branch,
            target_branch=target_branch,
            changed_files=changed_files,
            conflicts=conflicts,
            has_conflicts=len(conflicts) > 0,
            is_clean=len(conflicts) == 0
        )
        
        return OperationResult(True, "Merge preview generated", data=preview)
    
    def perform_integration(self, source_branch: str, target_branch: str = 'main') -> OperationResult:
        """Perform the actual merge/integration"""
        if not self.is_ctx_repo():
            return OperationResult(False, error="Not in a ctx repository")
        
        repo = self.get_ctx_repo()
        if not repo:
            return OperationResult(False, error="No ctx repository found")
        
        try:
            # Switch to target branch
            repo.git.checkout(target_branch)
            
            # Perform merge
            repo.git.merge(source_branch, '--no-edit')
            
            return OperationResult(
                True, 
                f"Successfully merged {source_branch} into {target_branch}",
                data={
                    'source_branch': source_branch,
                    'target_branch': target_branch
                }
            )
            
        except GitCommandError as e:
            return OperationResult(False, error=f"Merge failed: {e}")
        except Exception as e:
            return OperationResult(False, error=f"Error performing integration: {e}")
    
    def list_repositories(self) -> OperationResult:
        """List all discovered ctx repositories"""
        config = self.load_ctx_config()
        
        if not config['discovered_ctx']:
            return OperationResult(True, "No ctx repositories found", data=[])
        
        repositories = []
        for ctx_path in config['discovered_ctx']:
            full_path = Path.cwd() / ctx_path
            is_active = ctx_path == config['active_ctx']
            exists = full_path.exists() and (full_path / '.ctx').exists()
            
            repo_info = RepositoryInfo(
                name=ctx_path,
                path=full_path,
                absolute_path=full_path.absolute(),
                is_active=is_active,
                exists=exists,
                is_valid=exists
            )
            repositories.append(repo_info)
        
        return OperationResult(True, "Repositories listed", data=repositories)
    
    def switch_repository(self, ctx_name: str) -> OperationResult:
        """Switch to a different ctx repository"""
        config = self.load_ctx_config()
        
        if ctx_name not in config['discovered_ctx']:
            return OperationResult(
                False, 
                error=f"ctx repository '{ctx_name}' not found in config",
                data={'available_repositories': config['discovered_ctx']}
            )
        
        # Verify the repository still exists
        ctx_path = Path.cwd() / ctx_name
        
        if not ctx_path.exists() or not (ctx_path / '.ctx').exists():
            return OperationResult(False, error=f"ctx repository '{ctx_name}' directory is missing or invalid")
        
        # Switch to the new active repository
        config['active_ctx'] = ctx_name
        save_result = self.save_ctx_config(config)
        
        if not save_result.success:
            return save_result
        
        return OperationResult(True, f"Switched to ctx repository: {ctx_name}", data={'repository': ctx_name})
    
    def get_diff(self, staged: bool = False, branches: Optional[List[str]] = None) -> OperationResult:
        """Get git diff output for the ctx repository"""
        if not self.is_ctx_repo():
            return OperationResult(False, error="Not in a ctx repository")
        
        repo = self.get_ctx_repo()
        if not repo:
            return OperationResult(False, error="No ctx repository found")
        
        try:
            # Build git diff command based on options and arguments
            diff_args = []
            
            if staged:
                diff_args.append('--staged')
            
            if branches is None:
                branches = []
            
            # Handle branch arguments
            if len(branches) == 1:
                # Compare current branch with specified branch
                diff_args.append(branches[0])
            elif len(branches) == 2:
                # Compare two specified branches
                diff_args.append(f'{branches[0]}...{branches[1]}')
            elif len(branches) > 2:
                return OperationResult(False, error="Too many branch arguments. Use 0, 1, or 2 branches.")
            
            # Get diff output
            diff_output = repo.git.diff(*diff_args)
            
            return OperationResult(
                True, 
                "Diff retrieved successfully",
                data={
                    'diff': diff_output,
                    'staged': staged,
                    'branches': branches,
                    'has_changes': bool(diff_output.strip())
                }
            )
            
        except GitCommandError as e:
            if "unknown revision" in str(e).lower():
                all_branches = self.get_all_branches()
                return OperationResult(
                    False, 
                    error="Unknown branch or revision specified",
                    data={'available_branches': all_branches}
                )
            else:
                return OperationResult(False, error=f"Error getting diff: {e}")
        except Exception as e:
            return OperationResult(False, error=f"Error getting diff: {e}")

    def show_all(self, directory: Optional[str] = None, branch: Optional[str] = None, pattern: Optional[str] = None) -> OperationResult:
        """Display all file contents with clear delimiters for LLM context absorption
        
        Args:
            directory: Optional directory to show (relative to ctx root)
            branch: Optional branch to show files from (default: current branch)
            pattern: Optional file pattern to filter (e.g., "*.md")
        
        Returns:
            OperationResult with file contents and metadata
        """
        if not self.is_ctx_repo():
            return OperationResult(False, error="Not in a ctx repository")
        
        repo = self.get_ctx_repo()
        if not repo:
            return OperationResult(False, error="No ctx repository found")
            
        # Determine the branch to use
        if branch is None:
            branch = self.get_current_branch()
        
        # Validate branch exists
        all_branches = self.get_all_branches()
        if branch not in all_branches:
            return OperationResult(False, error=f"Branch '{branch}' does not exist")
        
        ctx_root = self.get_active_ctx_path()
        if not ctx_root:
            return OperationResult(False, error="Could not find ctx root")
        
        # Determine the directory to scan
        if directory:
            target_dir = ctx_root / directory
            if not target_dir.exists():
                return OperationResult(False, error=f"Directory '{directory}' does not exist")
            if not target_dir.is_dir():
                return OperationResult(False, error=f"'{directory}' is not a directory")
            scan_path = directory
        else:
            target_dir = ctx_root
            scan_path = "."
        
        try:
            # Get all files in the target directory (recursively)
            all_files = []
            
            def collect_files(path: Path, relative_base: str = ""):
                """Recursively collect all files"""
                for item in path.iterdir():
                    if item.is_file():
                        # Skip git files and hidden files
                        if item.name.startswith('.'):
                            continue
                        
                        # Build relative path from ctx root
                        if relative_base:
                            rel_path = f"{relative_base}/{item.name}"
                        else:
                            rel_path = item.name
                        
                        # Apply pattern filter if specified
                        if pattern and not fnmatch.fnmatch(item.name, pattern):
                            continue
                        
                        all_files.append((rel_path, item))
                    elif item.is_dir() and not item.name.startswith('.'):
                        # Recursively scan subdirectories
                        new_base = f"{relative_base}/{item.name}" if relative_base else item.name
                        collect_files(item, new_base)
            
            collect_files(target_dir, scan_path if scan_path != "." else "")
            
            # Sort files for consistent output
            all_files.sort(key=lambda x: x[0])
            
            # Read file contents
            file_contents = []
            for rel_path, file_path in all_files:
                try:
                    # Try to get content from the specified branch
                    if branch != self.get_current_branch():
                        # Use git to get file content from specific branch
                        content = self.get_file_content_at_branch(rel_path, branch)
                        if content is None:
                            # File might not exist in that branch
                            continue
                    else:
                        # Read from working directory
                        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                            content = f.read()
                    
                    file_contents.append({
                        'path': rel_path,
                        'content': content,
                        'size': len(content),
                        'lines': content.count('\n') + 1 if content else 0
                    })
                    
                except Exception as e:
                    # Skip files that can't be read (binary files, etc.)
                    file_contents.append({
                        'path': rel_path,
                        'content': f"[ERROR: Could not read file - {e}]",
                        'size': 0,
                        'lines': 0
                    })
            
            result = ShowAllResult(
                files=file_contents,
                total_files=len(file_contents),
                directory=directory,
                branch=branch,
                pattern=pattern
            )
            
            return OperationResult(True, "Files retrieved successfully", data=result)
            
        except Exception as e:
            return OperationResult(False, error=f"Error reading files: {e}") 
    
    def get_repository_info(self, name: str) -> RepositoryInfo:
        """Get information about a specific ctx repository"""
        config = self.load_ctx_config()
        active_ctx = config.get('active_ctx')
        
        path = self.project_root / name
        absolute_path = path.resolve()
        exists = path.exists() and (path / '.ctx').exists()
        
        repo = None
        if exists:
            try:
                repo = Repo(path)
            except InvalidGitRepositoryError:
                pass
        
        is_valid = repo is not None
        
        return RepositoryInfo(
            name=name,
            path=path,
            absolute_path=absolute_path,
            is_active=name == active_ctx,
            exists=exists,
            is_valid=is_valid
        )
    
    def delete_repository(self, name: str, force: bool = False) -> OperationResult:
        """Delete a ctx repository"""
        config = self.load_ctx_config()
        
        if name not in config['discovered_ctx']:
            return OperationResult(False, error=f"Context repository '{name}' not found in config")
        
        ctx_path = self.project_root / name
        
        if not ctx_path.exists() or not (ctx_path / '.ctx').exists():
            # Directory doesn't exist, so just remove from config
            pass
        
        # Remove from discovered list
        config['discovered_ctx'].remove(name)
        
        # If it's the active repository, set active to None
        if config['active_ctx'] == name:
            config['active_ctx'] = None
        
        # Save updated config
        save_result = self.save_ctx_config(config)
        
        if not save_result.success:
            return save_result
        
        # If directory exists, delete it
        if ctx_path.exists():
            try:
                shutil.rmtree(ctx_path)
            except Exception as e:
                return OperationResult(False, error=f"Error deleting directory: {e}")
        
        return OperationResult(True, f"Deleted ctx repository: {name}", data={'repository': name})