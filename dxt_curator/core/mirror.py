"""
Repository mirroring functionality for DXT Curator.

This module provides the core mirroring functionality that creates GitHub repositories
in the DXT-Mirror organization and sets up dual remotes for continuous synchronization.

Key Features:
1. Create mirror repositories in DXT-Mirror organization
2. Set up dual remotes (fetch from original, push to mirror)
3. Initial clone and sync of repository contents
4. Branch protection and repository settings
5. Webhook setup for continuous sync (optional)

Design Philosophy:
- Respect original repositories (read-only access)
- Maintain clear attribution to original authors
- Provide transparent mirroring process
- Support both one-time and continuous sync
"""

import os
import git
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import requests
from urllib.parse import urlparse

# from ..utils.security import PromptSecurityManager


class GitHubMirrorManager:
    """
    Manages GitHub repository mirroring operations.
    
    This class handles the complete mirroring workflow:
    1. Create mirror repository on GitHub
    2. Clone original repository
    3. Set up dual remotes
    4. Push to mirror repository
    5. Configure repository settings
    6. Prevent mirroring of blocklisted repositories
    """
    
    def __init__(self, github_token: str, mirror_org: str = "DXT-Mirror", blocklist: List[str] = None, daily_limit: int = 100, temp_dir: str = None):
        """
        Initialize mirror manager.
        
        Args:
            github_token: GitHub API token with repo creation permissions
            mirror_org: GitHub organization for mirror repositories
            blocklist: List of URL patterns to block from mirroring
            daily_limit: Maximum number of repositories to mirror per day
            temp_dir: Custom temporary directory for cloning (optional)
        """
        self.github_token = github_token
        self.mirror_org = mirror_org
        self.daily_limit = daily_limit
        self.temp_dir = temp_dir
        self.github_api_base = "https://api.github.com"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "DXT-Mirror/1.0"
        })
        
        # Initialize blocklist with default patterns
        self.blocklist = blocklist or []
        self._init_default_blocklist()
        
        # Initialize rate limiting
        self.rate_limit_file = Path("inventory/metadata/daily_mirror_count.json")
        self.retry_queue_file = Path("inventory/metadata/mirror_retry_queue.json")
        self._init_rate_limiting()
        
        print(f"🔧 GitHub Mirror Manager initialized for organization: {mirror_org}")
        print(f"🚫 Blocklist patterns: {len(self.blocklist)} entries")
        print(f"📊 Daily mirror limit: {daily_limit} repositories")
        print(f"📈 Today's mirror count: {self.get_daily_mirror_count()}")
        if temp_dir:
            print(f"📁 Using custom temp directory: {temp_dir}")
        else:
            print(f"📁 Using system temp directory: {tempfile.gettempdir()}")
    
    def _init_default_blocklist(self):
        """Initialize default blocklist patterns."""
        default_patterns = [
            f"github.com/{self.mirror_org}/*",  # Don't mirror our own mirrors
            f"https://github.com/{self.mirror_org}/*",
            f"git@github.com:{self.mirror_org}/*",
            # Add other common patterns that should never be mirrored
            "github.com/mirrors/*",
            "https://github.com/mirrors/*",
        ]
        
        # Add default patterns if not already in blocklist
        for pattern in default_patterns:
            if pattern not in self.blocklist:
                self.blocklist.append(pattern)
    
    def add_to_blocklist(self, pattern: str):
        """
        Add a URL pattern to the blocklist.
        
        Args:
            pattern: URL pattern to block (supports wildcards)
        """
        if pattern not in self.blocklist:
            self.blocklist.append(pattern)
            print(f"🚫 Added to blocklist: {pattern}")
    
    def remove_from_blocklist(self, pattern: str):
        """
        Remove a URL pattern from the blocklist.
        
        Args:
            pattern: URL pattern to remove
        """
        if pattern in self.blocklist:
            self.blocklist.remove(pattern)
            print(f"✅ Removed from blocklist: {pattern}")
    
    def is_blocked(self, repo_url: str) -> bool:
        """
        Check if a repository URL is blocked from mirroring.
        
        Args:
            repo_url: Repository URL to check
            
        Returns:
            True if repository is blocked, False otherwise
        """
        # Normalize URL for comparison
        normalized_url = repo_url.lower().strip()
        
        # Remove common prefixes and suffixes for comparison
        for prefix in ['https://', 'http://', 'git@']:
            if normalized_url.startswith(prefix):
                normalized_url = normalized_url[len(prefix):]
                break
        
        if normalized_url.endswith('.git'):
            normalized_url = normalized_url[:-4]
        
        # Check against blocklist patterns
        for pattern in self.blocklist:
            pattern_normalized = pattern.lower().strip()
            
            # Remove prefixes from pattern
            for prefix in ['https://', 'http://', 'git@']:
                if pattern_normalized.startswith(prefix):
                    pattern_normalized = pattern_normalized[len(prefix):]
                    break
            
            if pattern_normalized.endswith('.git'):
                pattern_normalized = pattern_normalized[:-4]
            
            # Simple wildcard matching
            if pattern_normalized.endswith('/*'):
                pattern_base = pattern_normalized[:-2]
                if normalized_url.startswith(pattern_base):
                    return True
            elif pattern_normalized == normalized_url:
                return True
        
        return False
    
    def get_blocked_reason(self, repo_url: str) -> Optional[str]:
        """
        Get the reason why a repository is blocked.
        
        Args:
            repo_url: Repository URL to check
            
        Returns:
            Reason string if blocked, None otherwise
        """
        if not self.is_blocked(repo_url):
            return None
        
        # Find matching pattern
        normalized_url = repo_url.lower().strip()
        for prefix in ['https://', 'http://', 'git@']:
            if normalized_url.startswith(prefix):
                normalized_url = normalized_url[len(prefix):]
                break
        
        if normalized_url.endswith('.git'):
            normalized_url = normalized_url[:-4]
        
        for pattern in self.blocklist:
            pattern_normalized = pattern.lower().strip()
            for prefix in ['https://', 'http://', 'git@']:
                if pattern_normalized.startswith(prefix):
                    pattern_normalized = pattern_normalized[len(prefix):]
                    break
            
            if pattern_normalized.endswith('.git'):
                pattern_normalized = pattern_normalized[:-4]
            
            if pattern_normalized.endswith('/*'):
                pattern_base = pattern_normalized[:-2]
                if normalized_url.startswith(pattern_base):
                    if pattern_base.startswith(f"{self.mirror_org.lower()}/"):
                        return f"Repository is from {self.mirror_org} organization (already a mirror)"
                    else:
                        return f"Repository matches blocked pattern: {pattern}"
            elif pattern_normalized == normalized_url:
                return f"Repository matches blocked pattern: {pattern}"
        
        return "Repository is blocked"
    
    def _init_rate_limiting(self):
        """Initialize rate limiting files and directories."""
        # Create metadata directory if it doesn't exist
        self.rate_limit_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize rate limit file if it doesn't exist
        if not self.rate_limit_file.exists():
            self._save_rate_limit_data({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "count": 0
            })
        
        # Initialize retry queue if it doesn't exist
        if not self.retry_queue_file.exists():
            self._save_retry_queue([])
    
    def _save_rate_limit_data(self, data: Dict[str, Any]):
        """Save rate limit data to file."""
        with open(self.rate_limit_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_rate_limit_data(self) -> Dict[str, Any]:
        """Load rate limit data from file."""
        try:
            with open(self.rate_limit_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"date": datetime.now().strftime("%Y-%m-%d"), "count": 0}
    
    def _save_retry_queue(self, queue: List[Dict[str, Any]]):
        """Save retry queue to file."""
        with open(self.retry_queue_file, 'w') as f:
            json.dump(queue, f, indent=2)
    
    def _load_retry_queue(self) -> List[Dict[str, Any]]:
        """Load retry queue from file."""
        try:
            with open(self.retry_queue_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def get_daily_mirror_count(self) -> int:
        """Get today's mirror count."""
        data = self._load_rate_limit_data()
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Reset count if it's a new day
        if data.get("date") != today:
            data = {"date": today, "count": 0}
            self._save_rate_limit_data(data)
        
        return data.get("count", 0)
    
    def increment_daily_mirror_count(self):
        """Increment today's mirror count."""
        data = self._load_rate_limit_data()
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Reset count if it's a new day
        if data.get("date") != today:
            data = {"date": today, "count": 0}
        
        data["count"] += 1
        self._save_rate_limit_data(data)
        
        print(f"📊 Daily mirror count: {data['count']}/{self.daily_limit}")
    
    def can_create_mirror(self) -> bool:
        """Check if we can create another mirror today."""
        count = self.get_daily_mirror_count()
        return count < self.daily_limit
    
    def get_remaining_daily_mirrors(self) -> int:
        """Get remaining mirrors we can create today."""
        count = self.get_daily_mirror_count()
        return max(0, self.daily_limit - count)
    
    def add_to_retry_queue(self, repo_data: Dict[str, Any], reason: str = "Daily limit reached"):
        """Add repository to retry queue."""
        queue = self._load_retry_queue()
        
        # Check if already in queue
        repo_url = repo_data.get('clone_url', '')
        for item in queue:
            if item.get('repository_url') == repo_url:
                print(f"ℹ️  Repository already in retry queue: {repo_data.get('full_name')}")
                return
        
        queue_item = {
            "repository_url": repo_url,
            "full_name": repo_data.get('full_name'),
            "repository_data": repo_data,
            "reason": reason,
            "added_date": datetime.now().isoformat(),
            "retry_count": 0
        }
        
        queue.append(queue_item)
        self._save_retry_queue(queue)
        
        print(f"📝 Added to retry queue: {repo_data.get('full_name')} ({reason})")
    
    def get_retry_queue(self) -> List[Dict[str, Any]]:
        """Get current retry queue."""
        return self._load_retry_queue()
    
    def remove_from_retry_queue(self, repo_url: str):
        """Remove repository from retry queue."""
        queue = self._load_retry_queue()
        original_length = len(queue)
        
        queue = [item for item in queue if item.get('repository_url') != repo_url]
        
        if len(queue) < original_length:
            self._save_retry_queue(queue)
            print(f"✅ Removed from retry queue: {repo_url}")
        else:
            print(f"⚠️  Repository not found in retry queue: {repo_url}")
    
    def clear_retry_queue(self):
        """Clear the entire retry queue."""
        self._save_retry_queue([])
        print("🧹 Cleared retry queue")
    
    def process_retry_queue(self, limit: int = None) -> Dict[str, Any]:
        """
        Process repositories in the retry queue.
        
        Args:
            limit: Maximum number of repositories to process
            
        Returns:
            Processing results
        """
        if not self.can_create_mirror():
            remaining = self.get_remaining_daily_mirrors()
            print(f"⏸️  Cannot process retry queue - daily limit reached (0/{self.daily_limit} remaining)")
            return {
                'processed': 0,
                'remaining_daily': remaining,
                'queue_size': len(self.get_retry_queue()),
                'message': 'Daily limit reached'
            }
        
        queue = self.get_retry_queue()
        if not queue:
            print("📭 Retry queue is empty")
            return {
                'processed': 0,
                'remaining_daily': self.get_remaining_daily_mirrors(),
                'queue_size': 0,
                'message': 'Queue is empty'
            }
        
        # Limit processing to daily limit or specified limit
        remaining_today = self.get_remaining_daily_mirrors()
        if limit:
            process_count = min(limit, remaining_today, len(queue))
        else:
            process_count = min(remaining_today, len(queue))
        
        print(f"🔄 Processing {process_count} repositories from retry queue...")
        
        processed = 0
        failed = 0
        results = []
        
        for i in range(process_count):
            if not self.can_create_mirror():
                print("⏸️  Daily limit reached during processing")
                break
            
            item = queue[i]
            repo_data = item['repository_data']
            repo_url = item['repository_url']
            
            try:
                print(f"\n🔄 Processing {repo_data.get('full_name')}...")
                
                # Attempt to mirror
                result = self.clone_and_mirror(repo_data)
                
                if result.get('status') == 'success':
                    # Remove from queue on success
                    self.remove_from_retry_queue(repo_url)
                    processed += 1
                    results.append(result)
                else:
                    # Update retry count
                    item['retry_count'] += 1
                    item['last_retry'] = datetime.now().isoformat()
                    failed += 1
                    
            except Exception as e:
                print(f"❌ Failed to process {repo_data.get('full_name')}: {e}")
                item['retry_count'] += 1
                item['last_retry'] = datetime.now().isoformat()
                item['last_error'] = str(e)
                failed += 1
        
        # Save updated queue
        self._save_retry_queue(queue)
        
        remaining_queue = len(queue) - processed
        
        print(f"\n🎉 Retry queue processing completed!")
        print(f"   ✅ Successfully processed: {processed}")
        print(f"   ❌ Failed: {failed}")
        print(f"   📝 Remaining in queue: {remaining_queue}")
        print(f"   📊 Daily mirrors remaining: {self.get_remaining_daily_mirrors()}")
        
        return {
            'processed': processed,
            'failed': failed,
            'remaining_queue': remaining_queue,
            'remaining_daily': self.get_remaining_daily_mirrors(),
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
    
    def create_mirror_repository(self, original_repo: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a mirror repository in the DXT-Mirror organization.
        
        Args:
            original_repo: Repository data from GitHub API
            
        Returns:
            Created repository data from GitHub API
        """
        original_name = original_repo['full_name']
        original_owner = original_repo['owner']['login']
        repo_name = original_repo['name']
        
        # Create mirror repository name
        mirror_name = f"{original_owner}_{repo_name}"
        
        # Prepare repository data
        repo_data = {
            "name": mirror_name,
            "description": f"🪞 Mirror of {original_name} - {original_repo.get('description', '')}",
            "private": False,  # Mirrors are public for transparency
            "has_issues": False,  # Issues should go to original repo
            "has_projects": False,
            "has_wiki": False,
            "auto_init": False,  # We'll push the original content
            "topics": [
                "dxt-mirror",
                "claude-desktop",
                "mirror"
            ] + (original_repo.get('topics', []) or [])
        }
        
        # Create repository
        url = f"{self.github_api_base}/orgs/{self.mirror_org}/repos"
        response = self.session.post(url, json=repo_data)
        
        if response.status_code == 201:
            mirror_repo = response.json()
            print(f"✅ Created mirror repository: {mirror_repo['full_name']}")
            return mirror_repo
        elif response.status_code == 422:
            # Repository might already exist
            existing_url = f"{self.github_api_base}/repos/{self.mirror_org}/{mirror_name}"
            existing_response = self.session.get(existing_url)
            if existing_response.status_code == 200:
                print(f"ℹ️  Mirror repository already exists: {self.mirror_org}/{mirror_name}")
                return existing_response.json()
            else:
                raise Exception(f"Repository creation failed: {response.json()}")
        else:
            raise Exception(f"Repository creation failed: {response.status_code} {response.text}")
    
    def setup_dual_remotes(self, repo_path: Path, original_url: str, mirror_url: str) -> None:
        """
        Set up dual remotes for a repository.
        
        Args:
            repo_path: Path to local repository
            original_url: Original repository URL (for fetching)
            mirror_url: Mirror repository URL (for pushing)
        """
        try:
            repo = git.Repo(repo_path)
            
            # Remove default origin
            try:
                repo.delete_remote('origin')
            except:
                pass
            
            # Add original remote (for fetching)
            original_remote = repo.create_remote('original', original_url)
            
            # Add mirror remote (for pushing)
            mirror_remote = repo.create_remote('mirror', mirror_url)
            
            print(f"🔗 Set up dual remotes:")
            print(f"   📥 original: {original_url}")
            print(f"   📤 mirror: {mirror_url}")
            
            return original_remote, mirror_remote
            
        except Exception as e:
            raise Exception(f"Failed to set up dual remotes: {e}")
    
    def clone_and_mirror(self, original_repo: Dict[str, Any], temp_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Clone original repository and set up mirror.
        
        Args:
            original_repo: Repository data from GitHub API
            temp_dir: Optional temporary directory for cloning
            
        Returns:
            Mirror operation results
        """
        original_url = original_repo['clone_url']
        original_name = original_repo['full_name']
        
        # Check if repository is blocked
        if self.is_blocked(original_url):
            reason = self.get_blocked_reason(original_url)
            error_msg = f"Repository is blocked from mirroring: {reason}"
            print(f"🚫 {error_msg}")
            return {
                'original_repo': original_name,
                'mirror_repo': None,
                'mirror_url': None,
                'status': 'blocked',
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            }
        
        # Check daily mirror limit
        if not self.can_create_mirror():
            remaining = self.get_remaining_daily_mirrors()
            error_msg = f"Daily mirror limit reached ({self.get_daily_mirror_count()}/{self.daily_limit})"
            print(f"⏸️  {error_msg}")
            
            # Add to retry queue
            self.add_to_retry_queue(original_repo, "Daily limit reached")
            
            return {
                'original_repo': original_name,
                'mirror_repo': None,
                'mirror_url': None,
                'status': 'rate_limited',
                'error': error_msg,
                'remaining_daily': remaining,
                'retry_queued': True,
                'timestamp': datetime.now().isoformat()
            }
        
        # Create mirror repository
        mirror_repo = self.create_mirror_repository(original_repo)
        mirror_url = mirror_repo['clone_url'].replace('https://github.com/', 
                                                     f'https://{self.github_token}@github.com/')
        
        # Set up temporary directory
        if temp_dir:
            temp_path = Path(temp_dir)
            temp_path.mkdir(parents=True, exist_ok=True)
            cleanup_temp = False
        elif self.temp_dir:
            temp_path = Path(self.temp_dir)
            temp_path.mkdir(parents=True, exist_ok=True)
            cleanup_temp = False
        else:
            temp_path = Path(tempfile.mkdtemp(prefix="dxt_mirror_"))
            cleanup_temp = True
        
        repo_path = temp_path / original_repo['name']
        
        try:
            print(f"📥 Cloning {original_name}...")
            
            # Clone with bare option for better mirroring
            subprocess.run([
                'git', 'clone', '--bare', original_url, str(repo_path)
            ], check=True, capture_output=True)
            
            # Change to repo directory and push to mirror
            print(f"📤 Pushing to mirror...")
            
            # Push all branches and tags to mirror
            subprocess.run([
                'git', '--git-dir', str(repo_path), 'push', '--mirror', mirror_url
            ], check=True, capture_output=True)
            
            # Update mirror repository settings
            self.configure_mirror_repository(mirror_repo, original_repo)
            
            # Increment daily mirror count
            self.increment_daily_mirror_count()
            
            result = {
                'original_repo': original_name,
                'mirror_repo': mirror_repo['full_name'],
                'mirror_url': mirror_repo['html_url'],
                'status': 'success',
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"✅ Successfully mirrored {original_name} → {mirror_repo['full_name']}")
            return result
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Git operation failed: {e.stderr.decode() if e.stderr else str(e)}"
            print(f"❌ Mirror failed: {error_msg}")
            raise Exception(error_msg)
        except Exception as e:
            print(f"❌ Mirror failed: {e}")
            raise
        finally:
            # Cleanup temporary directory
            if cleanup_temp and temp_path.exists():
                shutil.rmtree(temp_path, ignore_errors=True)
    
    def configure_mirror_repository(self, mirror_repo: Dict[str, Any], original_repo: Dict[str, Any]) -> None:
        """
        Configure mirror repository settings.
        
        Args:
            mirror_repo: Mirror repository data
            original_repo: Original repository data
        """
        mirror_name = mirror_repo['name']
        original_name = original_repo['full_name']
        
        # Update repository description with attribution
        description = f"🪞 Mirror of {original_name}"
        if original_repo.get('description'):
            description += f" - {original_repo['description']}"
        
        # Add attribution footer
        description += f"\n\n⚠️ This is a mirror repository. Please visit {original_repo['html_url']} for issues, PRs, and discussions."
        
        # Update repository settings
        update_data = {
            "description": description,
            "homepage": original_repo.get('html_url'),
            "has_issues": False,
            "has_projects": False,
            "has_wiki": False,
            "allow_squash_merge": False,
            "allow_merge_commit": False,
            "allow_rebase_merge": False,
            "delete_branch_on_merge": False
        }
        
        url = f"{self.github_api_base}/repos/{self.mirror_org}/{mirror_name}"
        response = self.session.patch(url, json=update_data)
        
        if response.status_code == 200:
            print(f"⚙️  Configured mirror repository settings")
        else:
            print(f"⚠️  Warning: Failed to update repository settings: {response.text}")
        
        # Add README with attribution if it doesn't exist
        self.add_mirror_readme(mirror_repo, original_repo)
    
    def add_mirror_readme(self, mirror_repo: Dict[str, Any], original_repo: Dict[str, Any]) -> None:
        """
        Add README with mirror attribution.
        
        Args:
            mirror_repo: Mirror repository data
            original_repo: Original repository data
        """
        # Check if README already exists
        readme_url = f"{self.github_api_base}/repos/{mirror_repo['full_name']}/readme"
        response = self.session.get(readme_url)
        
        if response.status_code == 200:
            print("ℹ️  README already exists, skipping mirror attribution")
            return
        
        # Create mirror attribution README
        readme_content = f"""# 🪞 Mirror Repository

This is a mirror of [{original_repo['full_name']}]({original_repo['html_url']}).

## ⚠️ Important Notice

**This is a read-only mirror repository.** 

- **Issues**: Please report issues at [{original_repo['full_name']}]({original_repo['html_url']}/issues)
- **Pull Requests**: Please submit PRs at [{original_repo['full_name']}]({original_repo['html_url']}/pulls)
- **Discussions**: Please use [{original_repo['full_name']}]({original_repo['html_url']}/discussions)

## 🎯 Purpose

This mirror is maintained by [DXT-Mirror](https://github.com/DXT-Mirror) to provide reliable access to DXT (Claude Desktop Extensions) repositories for the community.

## 📋 Original Repository Information

- **Repository**: [{original_repo['full_name']}]({original_repo['html_url']})
- **Owner**: [{original_repo['owner']['login']}]({original_repo['owner']['html_url']})
- **Language**: {original_repo.get('language', 'N/A')}
- **Stars**: {original_repo.get('stargazers_count', 0)}
- **Forks**: {original_repo.get('forks_count', 0)}

## 🔄 Sync Information

This mirror is synchronized with the original repository. For the most up-to-date information, please visit the original repository.

---

*This mirror is part of the DXT-Mirror project, sponsored by the [Cloud Security Alliance (CSA)](https://cloudsecurityalliance.org/).*
"""
        
        # Create README file
        import base64
        encoded_content = base64.b64encode(readme_content.encode()).decode()
        
        readme_data = {
            "message": "Add mirror attribution README",
            "content": encoded_content,
            "committer": {
                "name": "DXT-Mirror Bot",
                "email": "noreply@dxt-mirror.org"
            }
        }
        
        create_url = f"{self.github_api_base}/repos/{mirror_repo['full_name']}/contents/README.md"
        response = self.session.put(create_url, json=readme_data)
        
        if response.status_code == 201:
            print("📄 Added mirror attribution README")
        else:
            print(f"⚠️  Warning: Failed to add mirror README: {response.text}")
    
    def sync_repository(self, original_repo: Dict[str, Any], mirror_repo: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sync an existing mirror repository with its original.
        
        Args:
            original_repo: Original repository data
            mirror_repo: Mirror repository data
            
        Returns:
            Sync operation results
        """
        original_url = original_repo['clone_url']
        mirror_url = mirror_repo['clone_url'].replace('https://github.com/', 
                                                     f'https://{self.github_token}@github.com/')
        
        # Set up temporary directory
        if self.temp_dir:
            temp_path = Path(self.temp_dir)
            temp_path.mkdir(parents=True, exist_ok=True)
            cleanup_temp = False
        else:
            temp_path = Path(tempfile.mkdtemp(prefix="dxt_sync_"))
            cleanup_temp = True
        
        repo_path = temp_path / original_repo['name']
        
        try:
            print(f"🔄 Syncing {original_repo['full_name']}...")
            
            # Clone original repository
            subprocess.run([
                'git', 'clone', '--bare', original_url, str(repo_path)
            ], check=True, capture_output=True)
            
            # Push to mirror
            subprocess.run([
                'git', '--git-dir', str(repo_path), 'push', '--mirror', mirror_url
            ], check=True, capture_output=True)
            
            result = {
                'original_repo': original_repo['full_name'],
                'mirror_repo': mirror_repo['full_name'],
                'status': 'synced',
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"✅ Successfully synced {original_repo['full_name']}")
            return result
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Git sync failed: {e.stderr.decode() if e.stderr else str(e)}"
            print(f"❌ Sync failed: {error_msg}")
            raise Exception(error_msg)
        finally:
            # Cleanup if using temporary directory
            if cleanup_temp and temp_path.exists():
                shutil.rmtree(temp_path, ignore_errors=True)
    
    def get_mirror_info(self, original_repo_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about existing mirror repository.
        
        Args:
            original_repo_name: Original repository name (owner/repo)
            
        Returns:
            Mirror repository data or None if not found
        """
        owner, repo = original_repo_name.split('/')
        mirror_name = f"{owner}_{repo}"
        
        url = f"{self.github_api_base}/repos/{self.mirror_org}/{mirror_name}"
        response = self.session.get(url)
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    
    def list_mirrors(self) -> List[Dict[str, Any]]:
        """
        List all mirror repositories in the organization.
        
        Returns:
            List of mirror repository data
        """
        url = f"{self.github_api_base}/orgs/{self.mirror_org}/repos"
        response = self.session.get(url, params={'per_page': 100})
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to list mirrors: {response.text}")
    
    def delete_mirror(self, original_repo_name: str) -> bool:
        """
        Delete a mirror repository.
        
        Args:
            original_repo_name: Original repository name (owner/repo)
            
        Returns:
            True if deleted successfully
        """
        owner, repo = original_repo_name.split('/')
        mirror_name = f"{owner}_{repo}"
        
        url = f"{self.github_api_base}/repos/{self.mirror_org}/{mirror_name}"
        response = self.session.delete(url)
        
        if response.status_code == 204:
            print(f"🗑️  Deleted mirror repository: {self.mirror_org}/{mirror_name}")
            return True
        else:
            print(f"❌ Failed to delete mirror: {response.text}")
            return False


def main():
    """Command-line interface for mirror operations."""
    import argparse
    
    parser = argparse.ArgumentParser(description='DXT Repository Mirror Manager')
    parser.add_argument('--token', help='GitHub token (or use GITHUB_MIRROR_TOKEN env var)')
    parser.add_argument('--org', default='DXT-Mirror', help='Mirror organization')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Mirror command
    mirror_parser = subparsers.add_parser('mirror', help='Mirror a repository')
    mirror_parser.add_argument('repo', help='Repository to mirror (owner/repo)')
    
    # Sync command
    sync_parser = subparsers.add_parser('sync', help='Sync an existing mirror')
    sync_parser.add_argument('repo', help='Repository to sync (owner/repo)')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List mirror repositories')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a mirror repository')
    delete_parser.add_argument('repo', help='Repository to delete (owner/repo)')
    
    args = parser.parse_args()
    
    # Get GitHub token
    token = args.token or os.getenv('GITHUB_MIRROR_TOKEN') or os.getenv('GITHUB_TOKEN')
    if not token:
        print("❌ Error: No GitHub token provided")
        print("Set GITHUB_MIRROR_TOKEN environment variable or use --token")
        return 1
    
    # Initialize mirror manager
    mirror_manager = GitHubMirrorManager(token, args.org)
    
    try:
        if args.command == 'mirror':
            # Get repository info from GitHub API
            response = requests.get(f"https://api.github.com/repos/{args.repo}")
            if response.status_code == 200:
                repo_data = response.json()
                result = mirror_manager.clone_and_mirror(repo_data)
                print(f"🎉 Mirror operation completed: {result}")
            else:
                print(f"❌ Repository not found: {args.repo}")
                return 1
        
        elif args.command == 'sync':
            # Get repository info
            response = requests.get(f"https://api.github.com/repos/{args.repo}")
            mirror_info = mirror_manager.get_mirror_info(args.repo)
            
            if response.status_code == 200 and mirror_info:
                result = mirror_manager.sync_repository(response.json(), mirror_info)
                print(f"🎉 Sync operation completed: {result}")
            else:
                print(f"❌ Repository or mirror not found: {args.repo}")
                return 1
        
        elif args.command == 'list':
            mirrors = mirror_manager.list_mirrors()
            print(f"📋 Found {len(mirrors)} mirror repositories:")
            for mirror in mirrors:
                print(f"  - {mirror['full_name']} ({mirror['html_url']})")
        
        elif args.command == 'delete':
            success = mirror_manager.delete_mirror(args.repo)
            return 0 if success else 1
        
        else:
            parser.print_help()
            return 1
            
    except Exception as e:
        print(f"❌ Operation failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())