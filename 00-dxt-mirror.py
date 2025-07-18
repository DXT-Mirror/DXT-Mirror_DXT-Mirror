#!/usr/bin/env python3
"""
DXT Mirror System - Main Entrypoint Script

Easy-to-use interface for DXT repository mirroring operations.
This script provides shortcuts to the most common workflows.

Quick Start Examples:
    ./00-dxt-mirror.py discover --limit 20          # Discover and evaluate 20 repos
    ./00-dxt-mirror.py mirror --limit 5             # Mirror 5 approved repos  
    ./00-dxt-mirror.py workflow --discover 50 --mirror 10  # Full workflow
    ./00-dxt-mirror.py sync owner/repo               # Sync specific repository
    ./00-dxt-mirror.py status                        # Show system status

Author: DXT Mirror System
"""

import argparse
import os
import sys
import subprocess
from pathlib import Path

# Configuration
DEFAULT_MIRROR_ROOT = "/Users/kurt/GitHub/DXT-Mirror"
SCRIPT_DIR = Path(__file__).parent / "scripts"


def main():
    parser = argparse.ArgumentParser(
        description='DXT Mirror System - Easy repository mirroring',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Common Usage Patterns:

  # Quick Discovery & Mirroring
  %(prog)s workflow --discover 20 --mirror 5
  
  # Discovery Only (no mirroring)
  %(prog)s discover --limit 30
  
  # Mirror Only (skip discovery)
  %(prog)s mirror --limit 10
  
  # Sync Specific Repository
  %(prog)s sync milisp/awesome-claude-dxt
  
  # Bulk Operations
  %(prog)s bulk --sync-all
  %(prog)s bulk --list
  
  # System Status
  %(prog)s status
  %(prog)s inventory
  
  # Re-evaluate Inventory
  %(prog)s reeval                    # Re-evaluate all repositories
  %(prog)s reeval --status rejected  # Re-evaluate only rejected ones
  %(prog)s reeval --limit 20         # Re-evaluate first 20 repositories

Environment Variables:
  DXT_MIRROR_ROOT     Default mirror root directory
  GITHUB_MIRROR_TOKEN GitHub API token
        """
    )
    
    # Global options
    parser.add_argument('--mirror-root', default=os.getenv('DXT_MIRROR_ROOT', DEFAULT_MIRROR_ROOT),
                       help=f'Mirror root directory (default: {DEFAULT_MIRROR_ROOT})')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without doing it')
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Workflow command (most common)
    workflow_parser = subparsers.add_parser('workflow', help='Complete discovery + mirroring workflow')
    workflow_parser.add_argument('--discover', type=int, default=20, metavar='N',
                                help='Max repositories to discover and evaluate (default: 20)')
    workflow_parser.add_argument('--mirror', type=int, default=5, metavar='N',
                                help='Max repositories to mirror (default: 5)')
    workflow_parser.add_argument('--search-terms', default='claude,anthropic,mcp,dxt,claude-desktop,claude-api,claude-tools,awesome-claude,awesome-dxt,claude-template,universal-dtx-builder',
                                help='Comma-separated search terms')
    workflow_parser.add_argument('--force-reeval', action='store_true',
                                help='Re-evaluate repositories even if already evaluated')
    workflow_parser.add_argument('--dry-run', action='store_true',
                                help='Show what would be done without doing it')
    workflow_parser.add_argument('--verbose', '-v', action='store_true',
                                help='Enable verbose output')
    
    # Discovery command
    discover_parser = subparsers.add_parser('discover', help='Discover and evaluate repositories')
    discover_parser.add_argument('--limit', type=int, default=20, metavar='N',
                                help='Max repositories to discover (default: 20)')
    discover_parser.add_argument('--search-terms', default='claude,anthropic,mcp,dxt,claude-desktop,claude-api,claude-tools,awesome-claude,awesome-dxt,claude-template,universal-dtx-builder',
                                help='Comma-separated search terms')
    discover_parser.add_argument('--force-reeval', action='store_true',
                                help='Re-evaluate repositories even if already evaluated')
    discover_parser.add_argument('--dry-run', action='store_true',
                                help='Show what would be done without doing it')
    discover_parser.add_argument('--verbose', '-v', action='store_true',
                                help='Enable verbose output')
    
    # Mirror command
    mirror_parser = subparsers.add_parser('mirror', help='Mirror approved repositories')
    mirror_parser.add_argument('--limit', type=int, default=5, metavar='N',
                               help='Max repositories to mirror (default: 5)')
    mirror_parser.add_argument('--dry-run', action='store_true',
                              help='Show what would be done without doing it')
    mirror_parser.add_argument('--verbose', '-v', action='store_true',
                              help='Enable verbose output')
    
    # Sync command
    sync_parser = subparsers.add_parser('sync', help='Sync specific repository')
    sync_parser.add_argument('repo', metavar='OWNER/REPO',
                            help='Repository to sync (e.g., milisp/awesome-claude-dxt)')
    sync_parser.add_argument('--dry-run', action='store_true',
                            help='Show what would be done without doing it')
    sync_parser.add_argument('--verbose', '-v', action='store_true',
                            help='Enable verbose output')
    
    # Bulk operations
    bulk_parser = subparsers.add_parser('bulk', help='Bulk operations on existing mirrors')
    bulk_group = bulk_parser.add_mutually_exclusive_group(required=True)
    bulk_group.add_argument('--list', action='store_true',
                           help='List all mirrors with upstream URLs')
    bulk_group.add_argument('--sync-all', action='store_true',
                           help='Sync all mirrors with upstream')
    bulk_group.add_argument('--fix', action='store_true',
                           help='Fix mirrors missing upstream URLs')
    bulk_group.add_argument('--export', metavar='FILE',
                           help='Export mirror data to JSON file')
    bulk_parser.add_argument('--filter', metavar='TERM',
                            help='Filter mirrors by name containing term')
    bulk_parser.add_argument('--limit', type=int, metavar='N',
                            help='Limit number of mirrors to process')
    
    # Status commands
    status_parser = subparsers.add_parser('status', help='Show system status')
    
    inventory_parser = subparsers.add_parser('inventory', help='Show inventory summary')
    inventory_parser.add_argument('--verbose', '-v', action='store_true',
                                 help='Show detailed inventory information')
    
    # Re-evaluate command
    reeval_parser = subparsers.add_parser('reeval', help='Re-evaluate all repositories in inventory')
    reeval_parser.add_argument('--limit', type=int, metavar='N',
                              help='Limit number of repositories to re-evaluate')
    reeval_parser.add_argument('--status', choices=['discovered', 'rejected', 'approved', 'all'], default='all',
                              help='Only re-evaluate repositories with specific status (default: all)')
    reeval_parser.add_argument('--dry-run', action='store_true',
                              help='Show what would be done without doing it')
    reeval_parser.add_argument('--verbose', '-v', action='store_true',
                              help='Enable verbose output')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Show help if no command provided
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute the appropriate command
    try:
        if args.command == 'workflow':
            return run_workflow(args)
        elif args.command == 'discover':
            return run_discover(args)
        elif args.command == 'mirror':
            return run_mirror(args)
        elif args.command == 'sync':
            return run_sync(args)
        elif args.command == 'bulk':
            return run_bulk(args)
        elif args.command == 'status':
            return run_status(args)
        elif args.command == 'inventory':
            return run_inventory(args)
        elif args.command == 'reeval':
            return run_reeval(args)
        else:
            print(f"❌ Unknown command: {args.command}")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏸️  Operation interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


def run_workflow(args):
    """Run the complete discovery + mirroring workflow."""
    print(f"🚀 Running DXT Mirror Workflow")
    print(f"   📊 Discover: {args.discover} repos")
    print(f"   🪞 Mirror: {args.mirror} repos")
    print(f"   📁 Mirror Root: {args.mirror_root}")
    print()
    
    cmd = [
        'python', str(SCRIPT_DIR / 'dxt_workflow.py'),
        '--max-repos-to-examine', str(args.discover),
        '--max-repos-to-mirror', str(args.mirror),
        '--search-terms', args.search_terms,
        '--mirror-root', args.mirror_root
    ]
    
    if hasattr(args, 'verbose') and args.verbose:
        cmd.append('--verbose')
    if hasattr(args, 'dry_run') and args.dry_run:
        cmd.append('--dry-run')
    if hasattr(args, 'force_reeval') and args.force_reeval:
        cmd.append('--force-reeval')
    
    return subprocess.run(cmd).returncode


def run_discover(args):
    """Run discovery and evaluation only."""
    print(f"🔍 Discovering DXT Repositories")
    print(f"   📊 Limit: {args.limit} repos")
    print(f"   🔎 Search Terms: {args.search_terms}")
    print()
    
    cmd = [
        'python', str(SCRIPT_DIR / 'dxt_workflow.py'),
        '--max-repos-to-examine', str(args.limit),
        '--max-repos-to-mirror', '0',
        '--search-terms', args.search_terms,
        '--mirror-root', args.mirror_root
    ]
    
    if hasattr(args, 'verbose') and args.verbose:
        cmd.append('--verbose')
    if hasattr(args, 'dry_run') and args.dry_run:
        cmd.append('--dry-run')
    if hasattr(args, 'force_reeval') and args.force_reeval:
        cmd.append('--force-reeval')
    
    return subprocess.run(cmd).returncode


def run_mirror(args):
    """Run mirroring only (skip discovery)."""
    print(f"🪞 Mirroring Approved Repositories")
    print(f"   📊 Limit: {args.limit} repos")
    print(f"   📁 Mirror Root: {args.mirror_root}")
    print()
    
    cmd = [
        'python', str(SCRIPT_DIR / 'dxt_workflow.py'),
        '--max-repos-to-examine', '0',
        '--max-repos-to-mirror', str(args.limit),
        '--mirror-root', args.mirror_root
    ]
    
    if hasattr(args, 'verbose') and args.verbose:
        cmd.append('--verbose')
    if hasattr(args, 'dry_run') and args.dry_run:
        cmd.append('--dry-run')
    
    return subprocess.run(cmd).returncode


def run_sync(args):
    """Sync a specific repository."""
    print(f"🔄 Syncing Repository: {args.repo}")
    print(f"   📁 Mirror Root: {args.mirror_root}")
    print()
    
    cmd = [
        'python', str(SCRIPT_DIR / 'simple_sync.py'),
        args.repo,
        '--mirror-root', args.mirror_root
    ]
    
    if hasattr(args, 'verbose') and args.verbose:
        cmd.append('--verbose')
    if hasattr(args, 'dry_run') and args.dry_run:
        cmd.append('--dry-run')
    
    return subprocess.run(cmd).returncode


def run_bulk(args):
    """Run bulk operations on existing mirrors."""
    if args.list:
        action = '--list'
        print("📋 Listing All Mirrors")
    elif args.sync_all:
        action = '--sync'
        print("🔄 Syncing All Mirrors")
    elif args.fix:
        action = '--fix'
        print("🔧 Fixing Missing Upstream URLs")
    elif args.export:
        action = '--export'
        print(f"📤 Exporting Mirror Data to {args.export}")
    
    print(f"   📁 Mirror Root: {args.mirror_root}")
    print()
    
    cmd = [
        'python', str(SCRIPT_DIR / 'discover_mirrors.py'),
        action
    ]
    
    if args.export:
        cmd.append(args.export)
    
    if args.filter:
        cmd.extend(['--filter', args.filter])
    if args.limit:
        cmd.extend(['--limit', str(args.limit)])
    if hasattr(args, 'verbose') and args.verbose:
        cmd.append('--verbose')
    if hasattr(args, 'dry_run') and args.dry_run:
        cmd.append('--dry-run')
    
    # Add mirror-root for sync operations
    if args.sync_all:
        cmd.extend(['--mirror-root', args.mirror_root])
    
    return subprocess.run(cmd).returncode


def run_status(args):
    """Show system status."""
    print("📊 DXT Mirror System Status")
    print("=" * 50)
    
    # Check environment
    github_token = os.getenv('GITHUB_MIRROR_TOKEN') or os.getenv('GITHUB_TOKEN')
    openai_key = os.getenv('OPENAI_API_KEY')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    
    print(f"📁 Mirror Root: {args.mirror_root}")
    print(f"🔑 GitHub Token: {'✅ Set' if github_token else '❌ Missing'}")
    print(f"🤖 OpenAI API Key: {'✅ Set' if openai_key else '❌ Missing'}")
    print(f"🤖 Anthropic API Key: {'✅ Set' if anthropic_key else '❌ Missing'}")
    
    # Check mirror root directory
    mirror_root = Path(args.mirror_root)
    if mirror_root.exists():
        repos = list(mirror_root.glob('*_*'))
        print(f"📂 Local Mirrors: {len(repos)} repositories")
        
        if repos and args.verbose:
            print("\n📋 Local Repositories:")
            for repo in sorted(repos)[:10]:  # Show first 10
                print(f"   📁 {repo.name}")
            if len(repos) > 10:
                print(f"   ... and {len(repos) - 10} more")
    else:
        print(f"📂 Local Mirrors: Directory doesn't exist yet")
    
    # Check scripts
    required_scripts = ['dxt_workflow.py', 'simple_sync.py', 'discover_mirrors.py']
    print(f"\n🔧 Scripts:")
    for script in required_scripts:
        script_path = SCRIPT_DIR / script
        status = "✅" if script_path.exists() else "❌"
        print(f"   {status} {script}")
    
    return 0


def run_inventory(args):
    """Show inventory summary."""
    print("📋 Running Inventory Summary...")
    print()
    
    # Try to import and show inventory stats
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from dxt_curator.core.inventory import SimpleInventory
        
        inventory = SimpleInventory()
        summary = inventory.get_summary()
        
        print("📊 Inventory Statistics:")
        print("=" * 30)
        
        print(f"📈 Total Repositories: {summary.get('total_repos', 0)}")
        
        status_counts = summary.get('status_counts', {})
        for status, count in sorted(status_counts.items()):
            icon = {
                'discovered': '🔍',
                'approved': '✅', 
                'rejected': '❌',
                'mirror': '🪞',
                'mirror_failed': '💥',
                'error': '⚠️'
            }.get(status, '📋')
            print(f"{icon} {status.title()}: {count}")
        
        if args.verbose:
            # Show recent repositories
            all_repos = inventory.get_all_repos()
            if all_repos:
                print(f"\n📋 Recent Repositories:")
                for repo in all_repos[:5]:  # Just show first 5
                    print(f"   {repo.status:>10} | {repo.full_name}")
        
    except Exception as e:
        print(f"❌ Error accessing inventory: {e}")
        return 1
    
    return 0


def run_reeval(args):
    """Re-evaluate all repositories in inventory with updated criteria."""
    print(f"🔄 Re-evaluating Repository Inventory")
    print(f"   📊 Status Filter: {args.status}")
    if args.limit:
        print(f"   📝 Limit: {args.limit} repositories")
    print(f"   📁 Mirror Root: {args.mirror_root}")
    print()
    
    try:
        # Initialize components
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from dxt_curator.core.inventory import SimpleInventory
        from dxt_curator.core.evaluator import AIEvaluator
        
        inventory = SimpleInventory()
        evaluator = AIEvaluator()
        
        # Get repositories to re-evaluate
        if args.status == 'all':
            repos_to_eval = inventory.get_all_repos()
        else:
            repos_to_eval = inventory.get_repos_by_status(args.status)
        
        if not repos_to_eval:
            print("📋 No repositories found to re-evaluate")
            return 0
        
        # Apply limit if specified
        if args.limit:
            repos_to_eval = repos_to_eval[:args.limit]
        
        print(f"📊 Found {len(repos_to_eval)} repositories to re-evaluate")
        
        if args.dry_run:
            print("🔍 Dry run - showing what would be re-evaluated:")
            for repo in repos_to_eval:
                print(f"   {repo.status:>10} | {repo.full_name}")
            return 0
        
        # Re-evaluate each repository
        approved_count = 0
        rejected_count = 0
        error_count = 0
        
        for i, repo_entry in enumerate(repos_to_eval, 1):
            repo_key = repo_entry.full_name
            
            if args.verbose:
                print(f"🤖 Re-evaluating {i}/{len(repos_to_eval)}: {repo_key}")
            elif not args.verbose and i % 10 == 0:
                print(f"   Progress: {i}/{len(repos_to_eval)} repositories")
            
            try:
                # Convert repo entry to format expected by evaluator
                if isinstance(repo_entry.metadata, str):
                    repo_metadata = json.loads(repo_entry.metadata) if repo_entry.metadata else {}
                else:
                    # Metadata is already a dict or None
                    repo_metadata = repo_entry.metadata if repo_entry.metadata else {}
                
                # Create repo_data in expected format
                repo_data = {
                    'full_name': repo_key,
                    'clone_url': repo_metadata.get('clone_url', f"https://github.com/{repo_key}.git"),
                    'html_url': repo_metadata.get('html_url', f"https://github.com/{repo_key}"),
                    'description': repo_metadata.get('description', ''),
                    'stargazers_count': repo_metadata.get('stars', 0),
                    'forks_count': repo_metadata.get('forks', 0),
                    'language': repo_metadata.get('language', ''),
                    'topics': repo_metadata.get('topics', []),
                    'created_at': repo_metadata.get('created_at', ''),
                    'updated_at': repo_metadata.get('updated_at', ''),
                    'owner': {'login': repo_key.split('/')[0]},
                    'name': repo_key.split('/')[1]
                }
                
                # Run AI evaluation
                evaluation_result = evaluator.evaluate_repo(repo_data)
                
                # Update inventory with new evaluation result
                old_status = repo_entry.status
                if evaluation_result.get('decision') == 'mirror':
                    inventory.update_repo(repo_key, status='approved')
                    approved_count += 1
                    if args.verbose:
                        print(f"   ✅ Approved (was {old_status})")
                else:
                    inventory.update_repo(repo_key, status='rejected')
                    rejected_count += 1
                    if args.verbose:
                        reason = evaluation_result.get('reason', 'No reason provided')
                        print(f"   ❌ Rejected (was {old_status}) - {reason}")
                
            except Exception as e:
                error_count += 1
                inventory.update_repo(repo_key, status='error')
                if args.verbose:
                    print(f"   ⚠️ Error: {e}")
        
        print(f"\n📊 Re-evaluation Complete:")
        print(f"   ✅ Approved: {approved_count}")
        print(f"   ❌ Rejected: {rejected_count}")
        print(f"   ⚠️ Errors: {error_count}")
        print(f"   📈 Total processed: {len(repos_to_eval)}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Re-evaluation failed: {e}")
        return 1


if __name__ == '__main__':
    exit(main())