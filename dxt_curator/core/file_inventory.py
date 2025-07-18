"""
File-based inventory system for DXT repositories.

This module provides a GitHub-friendly inventory system that stores repository
information as individual JSON files. This approach offers several advantages:

1. GitHub Native: Each repository record is a separate file, perfect for Git
2. Transparency: All data is human-readable and version-controlled
3. Flexibility: Easy to add new fields without schema migrations
4. Scalability: No database limits, works with any number of repositories
5. Collaboration: Multiple contributors can work on inventory simultaneously

Design Philosophy:
- URL as Primary Key: Repository URLs are unique and descriptive
- UUID Filenames: Prevent filename conflicts and enable parallel processing
- JSON Format: Human-readable, widely supported, AI-friendly
- Directory Structure: Organized storage with easy navigation
- Version Control: Full history of all changes via Git
"""

import json
import uuid
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from urllib.parse import urlparse
import os
import csv


class FileInventory:
    """
    File-based repository inventory system.
    
    This class manages repository information as individual JSON files stored
    in a directory structure. Each repository gets a unique UUID-based filename,
    with the repository URL as the primary key for lookups.
    
    Directory Structure:
    inventory/
    ├── repositories/              # Repository files organized by date
    │   ├── 2024/                     # Year-based organization
    │   │   ├── 01/                   # Month-based subdivision
    │   │   │   ├── abc123...def.json # UUID-based filenames
    │   │   │   └── def456...789.json
    │   │   ├── 02/
    │   │   │   └── ...
    │   │   └── ...
    │   ├── 2025/
    │   │   ├── 01/
    │   │   └── ...
    │   └── ...
    ├── indexes/                   # Index files for fast lookups
    │   ├── url_to_uuid.json          # URL → UUID + path mapping
    │   ├── status_index.json         # Status → UUID list mapping
    │   ├── tag_index.json            # Tag → UUID list mapping
    │   └── master_index.csv          # Master CSV: URL, UUID, Path (alphabetical)
    └── metadata/                  # System metadata
        ├── stats.json                # Inventory statistics
        └── last_updated.json         # Last modification timestamps
    """
    
    def __init__(self, base_dir: str = "inventory"):
        """
        Initialize the file-based inventory system.
        
        Args:
            base_dir: Base directory for inventory files
        """
        self.base_dir = Path(base_dir)
        self.repos_dir = self.base_dir / "repositories"
        self.indexes_dir = self.base_dir / "indexes"
        self.metadata_dir = self.base_dir / "metadata"
        
        # Create directory structure
        self._init_directories()
        
        # Initialize indexes
        self._init_indexes()
        
        print(f"📂 File inventory initialized at: {self.base_dir}")
    
    def _init_directories(self):
        """Create the directory structure if it doesn't exist."""
        self.repos_dir.mkdir(parents=True, exist_ok=True)
        self.indexes_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
    
    def _init_indexes(self):
        """Initialize index files if they don't exist."""
        # URL to UUID mapping
        url_index_path = self.indexes_dir / "url_to_uuid.json"
        if not url_index_path.exists():
            self._save_json(url_index_path, {})
        
        # Status index
        status_index_path = self.indexes_dir / "status_index.json"
        if not status_index_path.exists():
            self._save_json(status_index_path, {})
        
        # Tag index
        tag_index_path = self.indexes_dir / "tag_index.json"
        if not tag_index_path.exists():
            self._save_json(tag_index_path, {})
    
    def _get_repository_path(self, discovery_date: str) -> Path:
        """
        Generate hierarchical path for repository file based on discovery date.
        
        Uses year/month structure to organize files:
        - repositories/2024/01/  (January 2024)
        - repositories/2024/02/  (February 2024)
        - repositories/2025/01/  (January 2025)
        
        Args:
            discovery_date: ISO date string (e.g., "2024-01-15T10:30:00Z")
            
        Returns:
            Path to the directory for this date
        """
        # Parse the date
        try:
            date_obj = datetime.fromisoformat(discovery_date.replace('Z', '+00:00'))
        except ValueError:
            # Fallback to current date if parsing fails
            date_obj = datetime.now()
        
        # Create year/month path
        year = date_obj.strftime("%Y")
        month = date_obj.strftime("%m")
        
        path = self.repos_dir / year / month
        path.mkdir(parents=True, exist_ok=True)
        
        return path
    
    def _generate_uuid_filename(self, repo_url: str) -> tuple[str, str]:
        """
        Generate a UUID-based filename for a repository.
        
        We use a combination of random UUID and URL hash to ensure uniqueness
        while maintaining some deterministic aspect for debugging.
        
        Args:
            repo_url: Repository URL
            
        Returns:
            Tuple of (filename, proper_uuid)
        """
        # Create a deterministic component based on URL
        url_hash = hashlib.sha256(repo_url.encode()).hexdigest()[:8]
        
        # Create a full UUID component
        full_uuid = str(uuid.uuid4()).upper()
        
        # Remove hyphens for filename (but keep them for UUID storage)
        filename_uuid = full_uuid.replace('-', '')
        
        # Combine for unique filename
        filename = f"{filename_uuid}_{url_hash}.json"
        
        return filename, full_uuid
    
    def _url_to_key(self, repo_url: str) -> str:
        """
        Convert repository URL to a standardized key.
        
        Args:
            repo_url: Repository URL
            
        Returns:
            Standardized URL key
        """
        # Normalize URL (remove .git suffix, ensure https)
        url = repo_url.lower().strip()
        if url.endswith('.git'):
            url = url[:-4]
        if url.startswith('git@github.com:'):
            url = url.replace('git@github.com:', 'https://github.com/')
        if not url.startswith('https://'):
            url = 'https://github.com/' + url
        
        return url
    
    def _load_json(self, file_path: Path) -> Dict[str, Any]:
        """Safely load JSON from file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_json(self, file_path: Path, data: Dict[str, Any]):
        """Safely save JSON to file."""
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write with pretty formatting
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)
    
    def add_repository(self, repo_data: Dict[str, Any], notes: str = "") -> str:
        """
        Add a new repository to the inventory.
        
        Args:
            repo_data: Repository information
            notes: Optional notes about the repository
            
        Returns:
            UUID of the created repository record
        """
        # Normalize URL
        repo_url = self._url_to_key(repo_data.get('clone_url', ''))
        
        # Check if repository already exists
        existing_uuid = self._get_uuid_by_url(repo_url)
        if existing_uuid:
            print(f"⚠️  Repository already exists: {repo_url}")
            return existing_uuid
        
        # Generate UUID filename
        filename, uuid_part = self._generate_uuid_filename(repo_url)
        
        # Create repository record
        now = datetime.now().isoformat()
        
        # Get hierarchical path based on discovery date
        repo_path = self._get_repository_path(now)
        
        # Determine initial status based on fork analysis
        initial_status = 'discovered'
        fork_notes = ""
        
        # Check if this is a fork with minimal changes
        if repo_data.get('is_fork', False):
            fork_analysis = repo_data.get('fork_analysis', '')
            if 'minimal changes' in fork_analysis.lower():
                initial_status = 'fork_ignored'
                fork_notes = f"Fork of {repo_data.get('parent_repo', 'unknown')} - {fork_analysis}"
            elif 'significant changes' in fork_analysis.lower():
                fork_notes = f"Fork of {repo_data.get('parent_repo', 'unknown')} with substantial modifications - {fork_analysis}"
            else:
                fork_notes = f"Fork of {repo_data.get('parent_repo', 'unknown')} - {fork_analysis}"
        
        # Combine notes
        combined_notes = f"{notes}. {fork_notes}" if fork_notes else notes
        
        # Store relative path for cross-references
        relative_path = repo_path.relative_to(self.repos_dir) / filename
        
        record = {
            "uuid": uuid_part,
            "repository_url": repo_url,
            "metadata": {
                "full_name": repo_data.get('full_name', ''),
                "description": repo_data.get('description', ''),
                "stars": repo_data.get('stars', 0),
                "forks": repo_data.get('forks', 0),
                "language": repo_data.get('language', ''),
                "size": repo_data.get('size', 0),
                "topics": repo_data.get('topics', []),
                "license": repo_data.get('license', ''),
                "created_at": repo_data.get('created_at', ''),
                "updated_at": repo_data.get('updated_at', ''),
                "archived": repo_data.get('archived', False)
            },
            "fork_info": {
                "is_fork": repo_data.get('is_fork', False),
                "parent_repo": repo_data.get('parent_repo'),
                "fork_analysis": repo_data.get('fork_analysis', '')
            },
            "curation": {
                "status": initial_status,
                "notes": combined_notes,
                "evaluation_notes": "",
                "decision_reason": "",
                "future_actions": "",
                "tags": []
            },
            "system": {
                "discovered_date": now,
                "last_updated": now,
                "filename": filename,
                "relative_path": str(relative_path),
                "original_data": repo_data  # Preserve original for reference
            }
        }
        
        # Save repository record in hierarchical structure
        repo_file = repo_path / filename
        self._save_json(repo_file, record)
        
        # Update indexes
        self._update_indexes(uuid_part, repo_url, initial_status, [], str(relative_path))
        
        # Update master CSV
        self._update_master_csv()
        
        print(f"✅ Added repository: {repo_data.get('full_name', repo_url)}")
        return uuid_part
    
    def _get_uuid_by_url(self, repo_url: str) -> Optional[str]:
        """Get UUID for a repository by URL."""
        url_index = self._load_json(self.indexes_dir / "url_to_uuid.json")
        entry = url_index.get(repo_url)
        if isinstance(entry, dict):
            return entry.get('uuid')
        else:
            # Handle legacy format
            return entry
    
    def _update_indexes(self, uuid_val: str, repo_url: str, status: str, tags: List[str], relative_path: str = None):
        """Update all index files."""
        # Update URL index with UUID and path information
        url_index = self._load_json(self.indexes_dir / "url_to_uuid.json")
        url_index[repo_url] = {
            "uuid": uuid_val,
            "path": relative_path
        }
        self._save_json(self.indexes_dir / "url_to_uuid.json", url_index)
        
        # Update status index
        status_index = self._load_json(self.indexes_dir / "status_index.json")
        if status not in status_index:
            status_index[status] = []
        if uuid_val not in status_index[status]:
            status_index[status].append(uuid_val)
        self._save_json(self.indexes_dir / "status_index.json", status_index)
        
        # Update tag index
        tag_index = self._load_json(self.indexes_dir / "tag_index.json")
        for tag in tags:
            if tag not in tag_index:
                tag_index[tag] = []
            if uuid_val not in tag_index[tag]:
                tag_index[tag].append(uuid_val)
        self._save_json(self.indexes_dir / "tag_index.json", tag_index)
    
    def _update_master_csv(self):
        """
        Update the master CSV file with all repositories in alphabetical order.
        
        The CSV contains: URL, UUID, Path, Status, Full Name
        This provides a quick lookup table that's easy to browse and search.
        """
        csv_path = self.indexes_dir / "master_index.csv"
        
        # Collect all repository data
        url_index = self._load_json(self.indexes_dir / "url_to_uuid.json")
        csv_data = []
        
        for url, info in url_index.items():
            uuid_val = info.get('uuid') if isinstance(info, dict) else info
            path = info.get('path', '') if isinstance(info, dict) else ''
            
            # Get repository record for additional info
            repo_record = self._get_repository_by_uuid(uuid_val)
            if repo_record:
                full_name = repo_record.get('metadata', {}).get('full_name', '')
                status = repo_record.get('curation', {}).get('status', '')
                stars = repo_record.get('metadata', {}).get('stars', 0)
                language = repo_record.get('metadata', {}).get('language', '')
                
                csv_data.append({
                    'url': url,
                    'uuid': uuid_val,
                    'path': path,
                    'status': status,
                    'full_name': full_name,
                    'stars': stars,
                    'language': language
                })
        
        # Sort by URL alphabetically
        csv_data.sort(key=lambda x: x['url'].lower())
        
        # Write CSV file
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['url', 'uuid', 'path', 'status', 'full_name', 'stars', 'language']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            writer.writerows(csv_data)
    
    def get_repository(self, repo_url: str) -> Optional[Dict[str, Any]]:
        """
        Get repository record by URL.
        
        Args:
            repo_url: Repository URL
            
        Returns:
            Repository record or None if not found
        """
        url_key = self._url_to_key(repo_url)
        uuid_val = self._get_uuid_by_url(url_key)
        
        if not uuid_val:
            return None
        
        return self._get_repository_by_uuid(uuid_val)
    
    def _get_repository_by_uuid(self, uuid_val: str) -> Optional[Dict[str, Any]]:
        """Get repository record by UUID."""
        # Search through hierarchical structure
        for file_path in self.repos_dir.rglob(f"{uuid_val}_*.json"):
            return self._load_json(file_path)
        return None
    
    def update_repository(self, repo_url: str, **updates) -> bool:
        """
        Update repository information.
        
        Args:
            repo_url: Repository URL
            **updates: Fields to update
            
        Returns:
            True if successful, False otherwise
        """
        record = self.get_repository(repo_url)
        if not record:
            return False
        
        now = datetime.now().isoformat()
        
        # Update curation fields
        if 'status' in updates:
            record['curation']['status'] = updates['status']
        if 'notes' in updates:
            record['curation']['notes'] = updates['notes']
        if 'evaluation_notes' in updates:
            record['curation']['evaluation_notes'] = updates['evaluation_notes']
        if 'decision_reason' in updates:
            record['curation']['decision_reason'] = updates['decision_reason']
        if 'future_actions' in updates:
            record['curation']['future_actions'] = updates['future_actions']
        if 'tags' in updates:
            record['curation']['tags'] = updates['tags']
        
        # Update system timestamp
        record['system']['last_updated'] = now
        
        # Save updated record using the stored relative path
        relative_path = record['system'].get('relative_path', record['system']['filename'])
        repo_file = self.repos_dir / relative_path
        self._save_json(repo_file, record)
        
        # Update indexes if status or tags changed
        if 'status' in updates or 'tags' in updates:
            self._update_indexes(
                record['uuid'],
                record['repository_url'],
                record['curation']['status'],
                record['curation']['tags']
            )
        
        # Update master CSV if any changes were made
        self._update_master_csv()
        
        return True
    
    def get_repositories_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get all repositories with a specific status."""
        status_index = self._load_json(self.indexes_dir / "status_index.json")
        uuid_list = status_index.get(status, [])
        
        repositories = []
        for uuid_val in uuid_list:
            repo = self._get_repository_by_uuid(uuid_val)
            if repo:
                repositories.append(repo)
        
        return repositories
    
    def search_repositories(self, query: str) -> List[Dict[str, Any]]:
        """Search repositories by text query."""
        query_lower = query.lower()
        results = []
        
        # Search through all repository files in hierarchical structure
        for file_path in self.repos_dir.rglob("*.json"):
            record = self._load_json(file_path)
            if not record:
                continue
            
            # Search in various fields
            searchable_text = " ".join([
                record.get('metadata', {}).get('full_name', ''),
                record.get('metadata', {}).get('description', ''),
                record.get('curation', {}).get('notes', ''),
                record.get('curation', {}).get('evaluation_notes', ''),
                record.get('fork_info', {}).get('fork_analysis', ''),
                " ".join(record.get('curation', {}).get('tags', []))
            ]).lower()
            
            if query_lower in searchable_text:
                results.append(record)
        
        return results
    
    def get_summary(self) -> Dict[str, Any]:
        """Get inventory summary statistics."""
        status_index = self._load_json(self.indexes_dir / "status_index.json")
        
        total_repos = sum(len(uuid_list) for uuid_list in status_index.values())
        
        return {
            "total_repositories": total_repos,
            "by_status": {status: len(uuid_list) for status, uuid_list in status_index.items()},
            "storage_location": str(self.base_dir.absolute()),
            "last_updated": datetime.now().isoformat()
        }
    
    def export_for_ai(self, status: str = None) -> List[Dict[str, Any]]:
        """Export repository data in AI-friendly format."""
        if status:
            repositories = self.get_repositories_by_status(status)
        else:
            repositories = []
            for file_path in self.repos_dir.rglob("*.json"):
                record = self._load_json(file_path)
                if record:
                    repositories.append(record)
        
        # Convert to AI-friendly format
        ai_data = []
        for repo in repositories:
            metadata = repo.get('metadata', {})
            curation = repo.get('curation', {})
            fork_info = repo.get('fork_info', {})
            
            ai_data.append({
                'repo_name': metadata.get('full_name', ''),
                'repository_url': repo.get('repository_url', ''),
                'description': metadata.get('description', ''),
                'stars': metadata.get('stars', 0),
                'language': metadata.get('language', ''),
                'status': curation.get('status', ''),
                'notes': curation.get('notes', ''),
                'evaluation_notes': curation.get('evaluation_notes', ''),
                'decision_reason': curation.get('decision_reason', ''),
                'future_actions': curation.get('future_actions', ''),
                'tags': curation.get('tags', []),
                'is_fork': fork_info.get('is_fork', False),
                'parent_repo': fork_info.get('parent_repo'),
                'fork_analysis': fork_info.get('fork_analysis', ''),
                'discovered_date': repo.get('system', {}).get('discovered_date', ''),
                'last_updated': repo.get('system', {}).get('last_updated', '')
            })
        
        return ai_data


def main():
    """CLI interface for file inventory."""
    import argparse
    
    parser = argparse.ArgumentParser(description='DXT File Inventory Manager')
    parser.add_argument('--summary', action='store_true', help='Show inventory summary')
    parser.add_argument('--search', help='Search repositories')
    parser.add_argument('--status', help='Show repositories by status')
    parser.add_argument('--export', help='Export to JSON file')
    
    args = parser.parse_args()
    
    inventory = FileInventory()
    
    if args.summary:
        summary = inventory.get_summary()
        print(json.dumps(summary, indent=2))
    
    elif args.search:
        results = inventory.search_repositories(args.search)
        print(f"Found {len(results)} repositories:")
        for repo in results:
            print(f"  {repo['metadata']['full_name']} ({repo['curation']['status']})")
    
    elif args.status:
        results = inventory.get_repositories_by_status(args.status)
        print(f"Repositories with status '{args.status}': {len(results)}")
        for repo in results:
            print(f"  {repo['metadata']['full_name']}")
    
    elif args.export:
        data = inventory.export_for_ai()
        with open(args.export, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Exported {len(data)} repositories to {args.export}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()