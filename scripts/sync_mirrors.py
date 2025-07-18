#!/usr/bin/env python3
"""
DXT Mirror Sync Script

This script syncs mirror repositories with their upstream sources using the
proven MCP-Mirror pattern:

1. Clone original repository (origin → upstream)
2. Add mirror remote (mirror → our mirror)  
3. Fetch from origin with prune
4. Push with --mirror to sync everything

Usage:
    python scripts/sync_mirrors.py --all                    # Sync all mirrors
    python scripts/sync_mirrors.py --repo owner/repo        # Sync specific repo
    python scripts/sync_mirrors.py --limit 5                # Sync first 5 mirrors
    python scripts/sync_mirrors.py --check                  # Check sync status only
"""

import argparse
import sys
import os
from pathlib import Path

# Add parent directory to path so we can import the modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from dxt_curator.core.workflow import SimpleDXTWorkflow


def main():
    parser = argparse.ArgumentParser(
        description='Sync DXT mirror repositories with their upstream sources',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --all                     # Sync all mirror repositories
  %(prog)s --repo milisp/awesome-claude-dxt  # Sync specific repository
  %(prog)s --limit 5                 # Sync first 5 repositories
  %(prog)s --check                   # Check which repos need syncing
  %(prog)s --status                  # Show current mirror status
        """
    )
    
    # Action arguments (mutually exclusive)
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument('--all', action='store_true',
                             help='Sync all mirror repositories')
    action_group.add_argument('--repo', metavar='OWNER/REPO',
                             help='Sync specific repository (e.g., milisp/awesome-claude-dxt)')
    action_group.add_argument('--check', action='store_true',
                             help='Check sync status without performing sync')
    action_group.add_argument('--status', action='store_true',
                             help='Show current inventory status')
    
    # Optional arguments
    parser.add_argument('--limit', type=int, metavar='N',
                       help='Limit number of repositories to sync (for --all)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be synced without doing it')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Initialize workflow
    try:
        print("🚀 Initializing DXT Mirror Sync...")
        workflow = SimpleDXTWorkflow()
        
        if not workflow.mirror_manager:
            print("❌ Error: Mirror manager not available. Check GITHUB_MIRROR_TOKEN.")
            return 1
            
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return 1
    
    # Execute requested action
    try:
        if args.status:
            show_status(workflow)
            
        elif args.check:
            check_sync_status(workflow)
            
        elif args.repo:
            sync_specific_repo(workflow, args.repo, args.dry_run, args.verbose)
            
        elif args.all:
            sync_all_repos(workflow, args.limit, args.dry_run, args.verbose)
            
    except KeyboardInterrupt:
        print("\n⏸️  Sync interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Sync failed: {e}")
        return 1
    
    return 0


def show_status(workflow):
    """Show current inventory status."""
    workflow.show_status()
    
    # Show mirrored repositories
    mirrored_repos = workflow.inventory.get_repositories_by_status('mirrored')
    if mirrored_repos:
        print(f"\n🪞 Mirrored Repositories ({len(mirrored_repos)}):")
        print("=" * 60)
        for repo in mirrored_repos:
            metadata = repo.get('metadata', {})
            print(f"  {metadata.get('full_name', 'Unknown')} ({metadata.get('stars', 0)} ⭐)")


def check_sync_status(workflow):
    """Check which repositories might need syncing."""
    print("🔍 Checking sync status...")
    
    mirrored_repos = workflow.inventory.get_repositories_by_status('mirrored')
    if not mirrored_repos:
        print("📭 No mirrored repositories found.")
        return
    
    print(f"📋 Found {len(mirrored_repos)} mirrored repositories:")
    print("=" * 70)
    
    for repo in mirrored_repos:
        metadata = repo.get('metadata', {})
        full_name = metadata.get('full_name', 'Unknown')
        
        # Check if mirror exists
        mirror_info = workflow.mirror_manager.get_mirror_info(full_name)
        if mirror_info:
            print(f"✅ {full_name}")
            print(f"   Mirror: {mirror_info['html_url']}")
            print(f"   Original: {repo['repository_url']}")
        else:
            print(f"⚠️  {full_name} - Mirror not found!")
        print()


def sync_specific_repo(workflow, repo_spec, dry_run=False, verbose=False):
    """Sync a specific repository."""
    print(f"🎯 Syncing specific repository: {repo_spec}")
    
    # Find the repository in inventory
    repo_url = f"https://github.com/{repo_spec}.git"
    repo = workflow.inventory.get_repository(repo_url)
    
    if not repo:
        print(f"❌ Repository {repo_spec} not found in inventory.")
        print("💡 Tip: Run discovery first to add it to inventory.")
        return
    
    if repo['curation']['status'] != 'mirrored':
        print(f"❌ Repository {repo_spec} is not marked as mirrored (status: {repo['curation']['status']})")
        return
    
    if dry_run:
        print(f"🔍 Would sync: {repo_spec}")
        return
    
    # Get mirror info
    mirror_info = workflow.mirror_manager.get_mirror_info(repo_spec)
    if not mirror_info:
        print(f"❌ Mirror repository not found for {repo_spec}")
        return
    
    # Perform sync
    try:
        result = workflow.mirror_manager.sync_repository(repo['metadata'], mirror_info)
        
        # Update inventory
        workflow.inventory.update_repository(repo_url, 
                                           notes=f"Synced at {result['timestamp']}")
        
        print(f"✅ Successfully synced {repo_spec}")
        if verbose:
            print(f"   Original: {repo['repository_url']}")
            print(f"   Mirror: {mirror_info['html_url']}")
            print(f"   Timestamp: {result['timestamp']}")
            
    except Exception as e:
        print(f"❌ Failed to sync {repo_spec}: {e}")


def sync_all_repos(workflow, limit=None, dry_run=False, verbose=False):
    """Sync all mirrored repositories."""
    print("🔄 Syncing all mirror repositories...")
    
    if dry_run:
        mirrored_repos = workflow.inventory.get_repositories_by_status('mirrored')
        if limit:
            mirrored_repos = mirrored_repos[:limit]
        
        print(f"🔍 Would sync {len(mirrored_repos)} repositories:")
        for repo in mirrored_repos:
            metadata = repo.get('metadata', {})
            print(f"  - {metadata.get('full_name', 'Unknown')}")
        return
    
    # Perform actual sync
    result = workflow.sync_mirrors(limit=limit)
    
    print(f"\n📊 Sync Summary:")
    print(f"   ✅ Synced: {result['synced']}")
    print(f"   ❌ Failed: {result['failed']}")
    
    if verbose and result.get('results'):
        print(f"\n📝 Detailed Results:")
        for sync_result in result['results']:
            print(f"   {sync_result['original_repo']} → {sync_result['status']}")


if __name__ == '__main__':
    exit(main())