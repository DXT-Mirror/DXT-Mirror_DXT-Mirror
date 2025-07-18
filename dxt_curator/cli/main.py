"""
Main CLI entry point for DXT Curator.

This module provides the primary command-line interface for all
DXT Curator functionality.
"""

import argparse
import sys
from typing import List, Optional
from datetime import datetime

from ..core.workflow import SimpleDXTWorkflow
from ..utils.logging import setup_logging


def main(args: Optional[List[str]] = None) -> None:
    """
    Main CLI entry point.
    
    Args:
        args: Optional list of command line arguments
    """
    parser = argparse.ArgumentParser(
        description='DXT Curator: AI-Powered Repository Discovery and Curation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  dxt-curator discover 25                    # Discover and evaluate 25 repositories
  dxt-curator status                         # Show current inventory status
  dxt-curator ready                          # Show repositories ready to mirror
  dxt-curator mirror                         # Mirror all approved repositories
  dxt-curator mirror --limit 5              # Mirror up to 5 repositories
  dxt-curator sync                           # Sync existing mirror repositories
  dxt-curator retry status                   # Show retry queue status and daily limits
  dxt-curator retry process                  # Process retry queue when daily limit resets
  dxt-curator retry list                     # List repositories in retry queue
  dxt-curator blocklist list                # Show blocked URL patterns
  dxt-curator blocklist add "github.com/baduser/*"  # Block a user's repositories
  dxt-curator blocklist check "https://github.com/user/repo"  # Check if URL is blocked
  dxt-curator search "claude automation"     # Search inventory
  dxt-curator recheck                        # Recheck repositories marked for later
  dxt-curator export                         # Export inventory for AI analysis

For more information, visit: https://github.com/DXT-Mirror/dxt-curator
        """
    )
    
    # Global options
    parser.add_argument('--api', choices=['openai', 'anthropic'], default='openai',
                       help='AI API provider to use')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='Logging level')
    parser.add_argument('--log-file', help='Log file path')
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Discover command
    discover_parser = subparsers.add_parser('discover', help='Discover and evaluate repositories')
    discover_parser.add_argument('limit', type=int, help='Number of repositories to process')
    discover_parser.add_argument('--min-stars', type=int, default=0,
                               help='Minimum stars filter')
    discover_parser.add_argument('--days', type=int, default=365,
                               help='Only consider repos updated in last N days')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show current inventory status')
    
    # Ready command
    ready_parser = subparsers.add_parser('ready', help='Show repositories ready to mirror')
    
    # Mirror command
    mirror_parser = subparsers.add_parser('mirror', help='Mirror approved repositories')
    mirror_parser.add_argument('--limit', type=int, help='Maximum number of repositories to mirror')
    mirror_parser.add_argument('--org', default='DXT-Mirror', help='Mirror organization')
    mirror_parser.add_argument('--temp-dir', help='Custom temporary directory for cloning')
    
    # Sync command
    sync_parser = subparsers.add_parser('sync', help='Sync existing mirror repositories')
    sync_parser.add_argument('--limit', type=int, help='Maximum number of repositories to sync')
    sync_parser.add_argument('--org', default='DXT-Mirror', help='Mirror organization')
    sync_parser.add_argument('--temp-dir', help='Custom temporary directory for cloning')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search through inventory')
    search_parser.add_argument('query', help='Search query')
    
    # Recheck command
    recheck_parser = subparsers.add_parser('recheck', help='Recheck repositories marked for later')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export inventory for AI analysis')
    export_parser.add_argument('--output', default='inventory_for_ai.json',
                              help='Output filename')
    
    # Blocklist command
    blocklist_parser = subparsers.add_parser('blocklist', help='Manage mirror blocklist')
    blocklist_subparsers = blocklist_parser.add_subparsers(dest='blocklist_action', help='Blocklist actions')
    
    # Blocklist list
    blocklist_list_parser = blocklist_subparsers.add_parser('list', help='List blocklist patterns')
    
    # Blocklist add
    blocklist_add_parser = blocklist_subparsers.add_parser('add', help='Add pattern to blocklist')
    blocklist_add_parser.add_argument('pattern', help='URL pattern to block (supports wildcards)')
    
    # Blocklist remove
    blocklist_remove_parser = blocklist_subparsers.add_parser('remove', help='Remove pattern from blocklist')
    blocklist_remove_parser.add_argument('pattern', help='URL pattern to remove')
    
    # Blocklist check
    blocklist_check_parser = blocklist_subparsers.add_parser('check', help='Check if URL is blocked')
    blocklist_check_parser.add_argument('url', help='URL to check')
    
    # Retry queue command
    retry_parser = subparsers.add_parser('retry', help='Manage retry queue')
    retry_subparsers = retry_parser.add_subparsers(dest='retry_action', help='Retry actions')
    
    # Retry queue list
    retry_list_parser = retry_subparsers.add_parser('list', help='List repositories in retry queue')
    
    # Retry queue process
    retry_process_parser = retry_subparsers.add_parser('process', help='Process retry queue')
    retry_process_parser.add_argument('--limit', type=int, help='Maximum number of repositories to process')
    
    # Retry queue clear
    retry_clear_parser = retry_subparsers.add_parser('clear', help='Clear retry queue')
    
    # Retry queue status
    retry_status_parser = retry_subparsers.add_parser('status', help='Show retry queue status')
    
    # Parse arguments
    parsed_args = parser.parse_args(args)
    
    # Setup logging
    setup_logging(parsed_args.log_level, parsed_args.log_file)
    
    # Check if command was provided
    if not parsed_args.command:
        parser.print_help()
        return
    
    # Initialize workflow
    try:
        mirror_org = getattr(parsed_args, 'org', 'DXT-Mirror')
        temp_dir = getattr(parsed_args, 'temp_dir', None)
        workflow = SimpleDXTWorkflow(ai_provider=parsed_args.api, mirror_org=mirror_org, temp_dir=temp_dir)
    except Exception as e:
        print(f"❌ Failed to initialize workflow: {e}")
        print("Make sure you have set GITHUB_MIRROR_TOKEN (or GITHUB_TOKEN) and OPENAI_API_KEY or ANTHROPIC_API_KEY")
        sys.exit(1)
    
    # Execute command
    try:
        if parsed_args.command == 'discover':
            filters = {}
            if parsed_args.min_stars:
                filters['min_stars'] = parsed_args.min_stars
            if parsed_args.days:
                filters['days'] = parsed_args.days
            
            workflow.discover_and_evaluate(parsed_args.limit, filters)
        
        elif parsed_args.command == 'status':
            workflow.show_status()
        
        elif parsed_args.command == 'ready':
            workflow.show_ready_to_mirror()
        
        elif parsed_args.command == 'mirror':
            workflow.mirror_approved_repositories(parsed_args.limit)
        
        elif parsed_args.command == 'sync':
            workflow.sync_mirrors(parsed_args.limit)
        
        elif parsed_args.command == 'search':
            workflow.search_inventory(parsed_args.query)
        
        elif parsed_args.command == 'recheck':
            workflow.recheck_later_repos()
        
        elif parsed_args.command == 'export':
            workflow.export_for_ai_analysis(parsed_args.output)
        
        elif parsed_args.command == 'blocklist':
            if not workflow.mirror_manager:
                print("❌ Error: Mirror manager not available. Check GitHub token.")
                return
            
            if parsed_args.blocklist_action == 'list':
                print(f"🚫 Blocklist patterns ({len(workflow.mirror_manager.blocklist)}):")
                for i, pattern in enumerate(workflow.mirror_manager.blocklist, 1):
                    print(f"  {i}. {pattern}")
            
            elif parsed_args.blocklist_action == 'add':
                workflow.mirror_manager.add_to_blocklist(parsed_args.pattern)
            
            elif parsed_args.blocklist_action == 'remove':
                workflow.mirror_manager.remove_from_blocklist(parsed_args.pattern)
            
            elif parsed_args.blocklist_action == 'check':
                if workflow.mirror_manager.is_blocked(parsed_args.url):
                    reason = workflow.mirror_manager.get_blocked_reason(parsed_args.url)
                    print(f"🚫 URL is blocked: {reason}")
                else:
                    print(f"✅ URL is not blocked: {parsed_args.url}")
            
            else:
                blocklist_parser.print_help()
        
        elif parsed_args.command == 'retry':
            if not workflow.mirror_manager:
                print("❌ Error: Mirror manager not available. Check GitHub token.")
                return
            
            if parsed_args.retry_action == 'list':
                queue = workflow.mirror_manager.get_retry_queue()
                if not queue:
                    print("📭 Retry queue is empty")
                else:
                    print(f"📝 Retry queue ({len(queue)} repositories):")
                    for i, item in enumerate(queue, 1):
                        retry_count = item.get('retry_count', 0)
                        added_date = item.get('added_date', 'Unknown')
                        print(f"  {i}. {item['full_name']}")
                        print(f"     Added: {added_date}")
                        print(f"     Reason: {item.get('reason', 'Unknown')}")
                        print(f"     Retries: {retry_count}")
                        print()
            
            elif parsed_args.retry_action == 'process':
                workflow.process_retry_queue(parsed_args.limit)
            
            elif parsed_args.retry_action == 'clear':
                workflow.mirror_manager.clear_retry_queue()
            
            elif parsed_args.retry_action == 'status':
                queue = workflow.mirror_manager.get_retry_queue()
                remaining = workflow.mirror_manager.get_remaining_daily_mirrors()
                daily_count = workflow.mirror_manager.get_daily_mirror_count()
                daily_limit = workflow.mirror_manager.daily_limit
                
                print(f"📊 Retry Queue Status:")
                print(f"   📝 Queue size: {len(queue)} repositories")
                print(f"   📊 Daily mirrors: {daily_count}/{daily_limit}")
                print(f"   📈 Remaining today: {remaining}")
                print(f"   📅 Date: {datetime.now().strftime('%Y-%m-%d')}")
            
            else:
                retry_parser.print_help()
    
    except KeyboardInterrupt:
        print("\\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()