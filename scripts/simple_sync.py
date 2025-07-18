#!/usr/bin/env python3
"""
Simple Mirror Sync Script

This script syncs a mirror repository with its upstream using the MCP-Mirror pattern.
It can work with any repository pair, not just ones in our inventory.

Usage:
    python scripts/simple_sync.py owner/repo
    python scripts/simple_sync.py milisp/awesome-claude-dxt

The script:
1. Clones the original repository 
2. Adds the mirror remote (predictable naming: DXT-Mirror/owner_repo)
3. Fetches from origin with prune
4. Pushes to mirror with --mirror flag
"""

import argparse
import subprocess
import tempfile
import shutil
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description='Sync a DXT mirror repository with its upstream source',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  %(prog)s milisp/awesome-claude-dxt

This will sync DXT-Mirror/milisp_awesome-claude-dxt with github.com/milisp/awesome-claude-dxt
        """
    )
    
    parser.add_argument('repo', metavar='OWNER/REPO',
                       help='Repository to sync (e.g., milisp/awesome-claude-dxt)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without doing it')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Suppress output except errors')
    
    args = parser.parse_args()
    
    # Validate repository format
    if '/' not in args.repo:
        print("❌ Error: Repository must be in format 'owner/repo'")
        return 1
    
    owner, repo_name = args.repo.split('/', 1)
    
    # Construct URLs
    original_url = f"https://github.com/{owner}/{repo_name}.git"
    mirror_name = f"{owner}_{repo_name}"
    
    # Get GitHub token
    github_token = os.getenv('GITHUB_MIRROR_TOKEN') or os.getenv('GITHUB_TOKEN')
    if not github_token:
        print("❌ Error: No GITHUB_MIRROR_TOKEN or GITHUB_TOKEN found")
        print("   Set one of these environment variables with your GitHub token")
        return 1
    
    mirror_url = f"https://{github_token}@github.com/DXT-Mirror/{mirror_name}.git"
    
    if not args.quiet:
        print(f"🔄 Syncing {args.repo}...")
        print(f"   Original: {original_url}")
        print(f"   Mirror: https://github.com/DXT-Mirror/{mirror_name}")
    
    if args.dry_run:
        print("🔍 Dry run - would perform sync but taking no action")
        return 0
    
    # Create temporary directory
    with tempfile.TemporaryDirectory(prefix="dxt_sync_") as temp_dir:
        repo_path = Path(temp_dir) / repo_name
        
        try:
            # Step 1: Clone original repository
            if args.verbose:
                print(f"📥 Cloning {original_url}...")
            
            subprocess.run([
                'git', 'clone', original_url, str(repo_path)
            ], check=True, capture_output=not args.verbose)
            
            # Step 2: Add mirror remote
            if args.verbose:
                print(f"🔧 Adding mirror remote...")
            
            subprocess.run([
                'git', '-C', str(repo_path), 'remote', 'add', 'mirror', mirror_url
            ], check=True, capture_output=not args.verbose)
            
            # Step 3: Fetch from origin with prune
            if args.verbose:
                print(f"📡 Fetching from origin with prune...")
            
            subprocess.run([
                'git', '-C', str(repo_path), 'fetch', '-p', 'origin'
            ], check=True, capture_output=not args.verbose)
            
            # Step 4: Push to mirror with --mirror
            if args.verbose:
                print(f"📤 Pushing to mirror with --mirror...")
            
            subprocess.run([
                'git', '-C', str(repo_path), 'push', '--mirror', 'mirror'
            ], check=True, capture_output=not args.verbose)
            
            if not args.quiet:
                print(f"✅ Successfully synced {args.repo}")
            
            if args.verbose:
                # Show remote configuration
                print(f"\n📋 Remote configuration:")
                result = subprocess.run([
                    'git', '-C', str(repo_path), 'remote', '-v'
                ], capture_output=True, text=True)
                print(result.stdout)
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Sync failed: {e}")
            if e.stderr:
                print(f"   Error details: {e.stderr.decode()}")
            return 1
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return 1
    
    return 0


if __name__ == '__main__':
    exit(main())