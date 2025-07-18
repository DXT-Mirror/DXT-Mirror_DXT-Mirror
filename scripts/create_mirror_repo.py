#!/usr/bin/env python3
"""
Create Mirror Repository Script

Creates a mirror repository in the DXT-Mirror organization for a given upstream repository.
This is useful when you want to create the GitHub repository before doing the first sync.

Usage:
    python scripts/create_mirror_repo.py owner/repo
    python scripts/create_mirror_repo.py milisp/awesome-claude-dxt
"""

import argparse
import sys
import os
from pathlib import Path

# Add parent directory to path so we can import the modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from dxt_curator.core.mirror import GitHubMirrorManager


def main():
    parser = argparse.ArgumentParser(
        description='Create a mirror repository in the DXT-Mirror organization',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  %(prog)s milisp/awesome-claude-dxt

This will create DXT-Mirror/milisp_awesome-claude-dxt
        """
    )
    
    parser.add_argument('repo', metavar='OWNER/REPO',
                       help='Repository to create mirror for (e.g., milisp/awesome-claude-dxt)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be created without doing it')
    
    args = parser.parse_args()
    
    # Validate repository format
    if '/' not in args.repo:
        print("❌ Error: Repository must be in format 'owner/repo'")
        return 1
    
    # Get GitHub token
    github_token = os.getenv('GITHUB_MIRROR_TOKEN') or os.getenv('GITHUB_TOKEN')
    if not github_token:
        print("❌ Error: No GITHUB_MIRROR_TOKEN or GITHUB_TOKEN found")
        return 1
    
    try:
        # Initialize mirror manager
        mirror_manager = GitHubMirrorManager(github_token, "DXT-Mirror")
        
        # Get original repository information
        print(f"🔍 Looking up repository: {args.repo}")
        repo_url = f"https://api.github.com/repos/{args.repo}"
        response = mirror_manager.session.get(repo_url)
        
        if response.status_code != 200:
            print(f"❌ Error: Repository {args.repo} not found or not accessible")
            return 1
        
        original_repo = response.json()
        owner, repo_name = args.repo.split('/', 1)
        mirror_name = f"{owner}_{repo_name}"
        
        print(f"📋 Repository Information:")
        print(f"   Original: {original_repo['html_url']}")
        print(f"   Mirror will be: https://github.com/DXT-Mirror/{mirror_name}")
        print(f"   Description: {original_repo.get('description', 'No description')}")
        print(f"   Stars: {original_repo.get('stargazers_count', 0)}")
        print(f"   Language: {original_repo.get('language', 'Unknown')}")
        
        if args.dry_run:
            print("🔍 Dry run - would create mirror repository but taking no action")
            return 0
        
        # Check if mirror already exists
        existing_mirror = mirror_manager.get_mirror_info(args.repo)
        if existing_mirror:
            print(f"ℹ️  Mirror repository already exists: {existing_mirror['html_url']}")
            return 0
        
        # Create mirror repository
        print(f"🔨 Creating mirror repository...")
        mirror_repo = mirror_manager.create_mirror_repository(original_repo)
        
        print(f"✅ Successfully created mirror repository!")
        print(f"   URL: {mirror_repo['html_url']}")
        print(f"   Clone URL: {mirror_repo['clone_url']}")
        
        print(f"\n💡 Next steps:")
        print(f"   1. Sync the repository: python scripts/simple_sync.py {args.repo}")
        print(f"   2. Or use the full workflow for ongoing management")
        
    except Exception as e:
        print(f"❌ Failed to create mirror repository: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())