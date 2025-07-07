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

class CtxCore:
    """Core business logic for ctx operations"""
    
    def __init__(self):
        pass
    
    def find_project_root(self) -> Path:
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
    
    def get_ctx_config_path(self) -> Path:
        """Get the path to the ctx.config file"""
        project_root = self.find_project_root()
        return project_root / 'ctx.config'
    
    def load_ctx_config(self) -> Dict[str, Any]:
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
        config_path = Path.cwd() / 'ctx.config'
        
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
    
    def find_ctx_root(self) -> Optional[Path]:
        """Find the active ctx repository from config"""
        config = self.load_ctx_config()
        
        if not config['active_ctx']:
            return None
        
        # Use current directory as project root
        ctx_path = Path.cwd() / config['active_ctx']
        
        # Verify it still exists and has .ctx marker
        if ctx_path.exists() and (ctx_path / '.ctx').exists():
            return ctx_path
        
        return None
    
    def get_ctx_repo(self) -> Optional[Repo]:
        """Get the GitPython repo object for the ctx directory"""
        ctx_dir = self.find_ctx_root()
        if not ctx_dir:
            return None
        try:
            return Repo(ctx_dir)
        except InvalidGitRepositoryError:
            return None
    
    def is_ctx_repo(self) -> bool:
        """Check if we're in or under a ctx repository"""
        return self.find_ctx_root() is not None
    
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
        
        ctx_dir = Path(directory)
        
        if ctx_dir.exists():
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
        
        ctx_dir = self.find_ctx_root()
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
    
    def capture_insights(self, message: str) -> OperationResult:
        """Capture current insights and thinking"""
        if not self.is_ctx_repo():
            return OperationResult(False, error="Not in a ctx repository")
        
        repo = self.get_ctx_repo()
        if not repo:
            return OperationResult(False, error="No ctx repository found")
        
        try:
            # Check if there are any changes to commit
            if not repo.is_dirty(untracked_files=True):
                return OperationResult(True, "No changes to capture")
            
            # Stage all changes
            repo.git.add('-A')
            
            # Commit with the provided message
            repo.index.commit(message)
            return OperationResult(True, f"Captured: {message}", data={'message': message})
            
        except Exception as e:
            return OperationResult(False, error=f"Error capturing insights: {e}")
    
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
    
    def get_diff(self, staged: bool = False, branches: List[str] = None) -> OperationResult:
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