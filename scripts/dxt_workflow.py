#!/usr/bin/env python3
"""
DXT Mirror Workflow Script

Complete automation script for discovering, evaluating, and mirroring DXT repositories.
Supports configurable limits for both examination and mirroring phases.

Usage:
    python scripts/dxt_workflow.py --max-repos-to-examine 50 --max-repos-to-mirror 10
    python scripts/dxt_workflow.py --max-repos-to-examine 0 --max-repos-to-mirror 5   # Skip discovery, only mirror approved
    python scripts/dxt_workflow.py --max-repos-to-examine 100 --max-repos-to-mirror 0 # Only examine, no mirroring

Features:
- Configurable discovery and mirroring limits
- AI-powered repository evaluation
- Inventory system integration
- GitHub search result capture
- Complete workflow automation
"""

import argparse
import json
import sys
import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path so we can import the modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from dxt_curator.core.discovery import StrategicGitHubSearch
from dxt_curator.core.evaluator import AIEvaluator
from dxt_curator.core.mirror import GitHubMirrorManager
from dxt_curator.core.inventory import SimpleInventory
from dxt_curator.utils.config import get_config


def main():
    parser = argparse.ArgumentParser(
        description='Complete DXT repository discovery, evaluation, and mirroring workflow',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --max-repos-to-examine 50 --max-repos-to-mirror 10
    Discover and examine up to 50 repositories, mirror up to 10 approved ones
    
  %(prog)s --max-repos-to-examine 0 --max-repos-to-mirror 5
    Skip discovery phase, only mirror up to 5 already-approved repositories
    
  %(prog)s --max-repos-to-examine 100 --max-repos-to-mirror 0
    Only examine up to 100 repositories, don't create any mirrors
    
  %(prog)s --max-repos-to-examine 20 --max-repos-to-mirror 5 --search-terms "claude dxt,anthropic"
    Custom search terms with limits
        """
    )
    
    # Core workflow arguments
    parser.add_argument('--max-repos-to-examine', type=int, default=20,
                       help='Maximum number of repositories to discover and examine (0 to skip discovery)')
    parser.add_argument('--max-repos-to-mirror', type=int, default=5,
                       help='Maximum number of repositories to mirror (0 to skip mirroring)')
    
    # Discovery configuration
    parser.add_argument('--search-terms', default='claude desktop extension,claude mcp,anthropic claude,claude api',
                       help='Comma-separated search terms for GitHub discovery')
    parser.add_argument('--min-stars', type=int, default=1,
                       help='Minimum stars for repositories to consider')
    parser.add_argument('--max-age-days', type=int, default=730,
                       help='Maximum age in days for repositories to consider')
    
    # Operation modes
    parser.add_argument('--force-reeval', action='store_true',
                       help='Re-evaluate repositories even if already evaluated')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without doing it')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Suppress output except errors and final summary')
    parser.add_argument('--mirror-root', metavar='PATH',
                       help='Root directory for local mirror repositories (e.g., /Users/kurt/GitHub/DXT-Mirror/)')
    
    args = parser.parse_args()
    
    # Initialize components
    try:
        config = get_config()
        inventory = SimpleInventory()
        
        github_token = os.getenv('GITHUB_MIRROR_TOKEN') or os.getenv('GITHUB_TOKEN')
        if not github_token:
            print("❌ Error: No GITHUB_MIRROR_TOKEN or GITHUB_TOKEN found")
            return 1
        
        discovery = StrategicGitHubSearch(github_token)
        evaluator = AIEvaluator()
        mirror_manager = GitHubMirrorManager(github_token, "DXT-Mirror")
        
        if not args.quiet:
            print("🚀 DXT Mirror Workflow Started")
            print(f"📊 Configuration:")
            print(f"   Max repos to examine: {args.max_repos_to_examine}")
            print(f"   Max repos to mirror: {args.max_repos_to_mirror}")
            if args.max_repos_to_examine > 0:
                print(f"   Search terms: {args.search_terms}")
            print()
        
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return 1
    
    # Phase 1: Discovery and Examination
    if args.max_repos_to_examine > 0:
        try:
            discovered_count, examined_count = run_discovery_phase(
                discovery, evaluator, inventory, args
            )
            if not args.quiet:
                print(f"📋 Discovery Phase Complete:")
                print(f"   Discovered: {discovered_count} repositories")
                print(f"   Examined: {examined_count} repositories")
                print()
        except Exception as e:
            print(f"❌ Discovery phase failed: {e}")
            return 1
    else:
        if not args.quiet:
            print("⏩ Skipping discovery phase (--max-repos-to-examine 0)")
            print()
    
    # Phase 2: Mirroring
    if args.max_repos_to_mirror > 0:
        try:
            mirrored_count = run_mirroring_phase(
                mirror_manager, inventory, args
            )
            if not args.quiet:
                print(f"🪞 Mirroring Phase Complete:")
                print(f"   Mirrored: {mirrored_count} repositories")
                print()
        except Exception as e:
            print(f"❌ Mirroring phase failed: {e}")
            return 1
    else:
        if not args.quiet:
            print("⏩ Skipping mirroring phase (--max-repos-to-mirror 0)")
            print()
    
    # Final summary
    if not args.quiet:
        print_final_summary(inventory, args)
    
    return 0


def run_discovery_phase(discovery: StrategicGitHubSearch, evaluator: AIEvaluator, 
                       inventory: SimpleInventory, args) -> tuple[int, int]:
    """Run the discovery and examination phase."""
    
    if not args.quiet:
        print("🔍 Phase 1: Discovery and Examination")
        print("=" * 50)
    
    discovered_count = 0
    examined_count = 0
    
    # Parse search terms
    search_terms = [term.strip() for term in args.search_terms.split(',')]
    
    for search_term in search_terms:
        if not args.quiet:
            print(f"🔎 Searching for: {search_term}")
        
        try:
            # Discover repositories  
            discovered_repos = discovery.search_repositories(
                query=search_term,
                min_stars=args.min_stars,
                max_results=args.max_repos_to_examine - discovered_count
            )
            
            if args.verbose:
                print(f"   Found {len(discovered_repos)} repositories")
            
            for repo in discovered_repos:
                discovered_count += 1
                
                # Extract owner and name from full_name
                owner, name = repo.full_name.split('/', 1)
                
                # Add to inventory as basic entry if not already present
                repo_key = repo.full_name
                existing = inventory.get_repo(repo_key)
                
                if not existing:
                    # Create basic inventory entry from SearchResult
                    repo_data = {
                        'full_name': repo.full_name,
                        'clone_url': repo.clone_url,
                        'html_url': f"https://github.com/{repo.full_name}",
                        'description': repo.description,
                        'stargazers_count': repo.stars,
                        'forks_count': repo.forks,
                        'language': repo.language,
                        'topics': repo.topics,
                        'created_at': repo.created_at,
                        'updated_at': repo.updated_at,
                        'owner': {'login': owner},
                        'name': name
                    }
                    
                    inventory.add_repo(repo_data, f"Discovered via search: {search_term}")
                    
                    if args.verbose:
                        print(f"   📝 Added to inventory: {repo_key}")
                
                # Check if we should evaluate this repository
                should_evaluate = False
                
                if existing:
                    current_status = existing.status
                    if current_status == 'discovered' or args.force_reeval:
                        should_evaluate = True
                else:
                    should_evaluate = True
                
                # Evaluate repository if needed
                if should_evaluate and examined_count < args.max_repos_to_examine:
                    if args.verbose:
                        print(f"   🤖 Evaluating: {repo_key}")
                    
                    if not args.dry_run:
                        try:
                            # Convert SearchResult to dict format expected by evaluator
                            repo_data = {
                                'full_name': repo.full_name,
                                'clone_url': repo.clone_url,
                                'html_url': f"https://github.com/{repo.full_name}",
                                'description': repo.description,
                                'stargazers_count': repo.stars,
                                'forks_count': repo.forks,
                                'language': repo.language,
                                'topics': repo.topics,
                                'created_at': repo.created_at,
                                'updated_at': repo.updated_at,
                                'owner': {'login': owner},
                                'name': name
                            }
                            
                            # Run AI evaluation
                            evaluation_result = evaluator.evaluate_repo(repo_data)
                            
                            # Update inventory with evaluation result
                            if evaluation_result.get('decision') == 'mirror':
                                inventory.update_repo(repo_key, status='approved')
                                if args.verbose:
                                    print(f"   ✅ Approved for mirroring")
                            else:
                                inventory.update_repo(repo_key, status='rejected')
                                if args.verbose:
                                    print(f"   ❌ Rejected - {evaluation_result.get('reason', 'No reason provided')}")
                            
                            examined_count += 1
                            
                        except Exception as e:
                            print(f"   ⚠️ Evaluation failed for {repo_key}: {e}")
                            inventory.update_repo(repo_key, status='error')
                    else:
                        print(f"   🔍 Would evaluate: {repo_key}")
                        examined_count += 1
                
                # Check if we've hit our discovery limit
                if discovered_count >= args.max_repos_to_examine:
                    break
            
            # Check if we've hit our discovery limit
            if discovered_count >= args.max_repos_to_examine:
                break
                
        except Exception as e:
            print(f"⚠️ Error searching for '{search_term}': {e}")
            continue
    
    return discovered_count, examined_count


def run_mirroring_phase(mirror_manager: GitHubMirrorManager, inventory: SimpleInventory, args) -> int:
    """Run the mirroring phase."""
    
    if not args.quiet:
        print("🪞 Phase 2: Repository Mirroring")
        print("=" * 50)
    
    # Get all approved repositories that haven't been mirrored yet
    approved_repos = []
    
    try:
        # Get all repositories with 'approved' status
        approved_entries = inventory.get_repos_by_status('approved')
        
        for entry in approved_entries:
            # Check if already mirrored by looking at notes or status
            if 'mirrored' not in entry.notes.lower():
                approved_repos.append((entry.full_name, entry))
        
        if not approved_repos:
            if not args.quiet:
                print("📋 No approved repositories found that need mirroring")
            return 0
        
        if not args.quiet:
            print(f"📋 Found {len(approved_repos)} approved repositories to mirror")
            print(f"🎯 Will mirror up to {args.max_repos_to_mirror} repositories")
            print()
        
        mirrored_count = 0
        
        for repo_key, repo_entry in approved_repos[:args.max_repos_to_mirror]:
            if not args.quiet:
                print(f"🪞 Mirroring: {repo_key}")
            
            try:
                if not args.dry_run:
                    # Convert RepoEntry metadata to dict format for mirror manager
                    if isinstance(repo_entry.metadata, str):
                        repo_metadata = json.loads(repo_entry.metadata) if repo_entry.metadata else {}
                    else:
                        # Metadata is already a dict or None
                        repo_metadata = repo_entry.metadata if repo_entry.metadata else {}
                    
                    # Create mirror repository and sync content
                    mirror_result = mirror_manager.clone_and_mirror(
                        original_repo=repo_metadata
                    )
                    
                    if args.verbose:
                        print(f"   📊 Mirror result: {mirror_result}")
                    
                    if mirror_result and mirror_result.get('status') == 'success':
                        # Update inventory with mirror status
                        inventory.update_repo(
                            repo_key, 
                            status='mirror',
                            notes=f"{repo_entry.notes} | Mirrored on {time.strftime('%Y-%m-%d')}"
                        )
                        
                        if args.verbose:
                            print(f"   ✅ Mirror created: {mirror_result.get('mirror_url')}")
                        
                        mirrored_count += 1
                    else:
                        print(f"   ❌ Failed to create mirror - Result: {mirror_result}")
                        inventory.update_repo(repo_key, status='mirror_failed')
                else:
                    print(f"   🔍 Would create mirror for: {repo_key}")
                    mirrored_count += 1
                
            except Exception as e:
                print(f"   ❌ Error mirroring {repo_key}: {e}")
                if not args.dry_run:
                    inventory.update_repo(repo_key, status='mirror_failed')
        
        return mirrored_count
        
    except Exception as e:
        print(f"❌ Error in mirroring phase: {e}")
        return 0


def sync_repository_content(repo_key: str, args) -> bool:
    """Sync repository content using the simple_sync script."""
    try:
        import subprocess
        script_path = Path(__file__).parent / "simple_sync.py"
        
        cmd = ['python', str(script_path), repo_key]
        if not args.verbose:
            cmd.append('--quiet')
        if args.mirror_root:
            cmd.extend(['--mirror-root', args.mirror_root])
        
        result = subprocess.run(cmd, capture_output=not args.verbose)
        return result.returncode == 0
        
    except Exception as e:
        if args.verbose:
            print(f"   Sync error: {e}")
        return False


def print_final_summary(inventory: SimpleInventory, args):
    """Print final workflow summary."""
    print("📊 Final Workflow Summary")
    print("=" * 50)
    
    try:
        # Get summary from inventory
        summary = inventory.get_summary()
        
        # Print status breakdown
        for status, count in summary.get('status_counts', {}).items():
            icon = {
                'discovered': '🔍',
                'approved': '✅',
                'rejected': '❌',
                'mirror': '🪞',
                'mirror_failed': '💥',
                'error': '⚠️'
            }.get(status, '📋')
            
            print(f"   {icon} {status.title()}: {count}")
        
        print(f"\n📈 Total repositories in inventory: {summary.get('total_repos', 0)}")
        
        # Show recent activity by checking notes for today's date
        today = time.strftime('%Y-%m-%d')
        all_repos = inventory.get_all_repos()
        
        mirrored_today = 0
        discovered_today = 0
        
        for entry in all_repos:
            if today in entry.notes:
                if 'Mirrored' in entry.notes:
                    mirrored_today += 1
                if 'Discovered' in entry.notes:
                    discovered_today += 1
        
        if mirrored_today > 0 or discovered_today > 0:
            print(f"\n📅 Today's Activity:")
            if discovered_today > 0:
                print(f"   🔍 Discovered: {discovered_today}")
            if mirrored_today > 0:
                print(f"   🪞 Mirrored: {mirrored_today}")
        
    except Exception as e:
        print(f"⚠️ Error generating summary: {e}")
    
    print("\n✨ Workflow Complete!")


if __name__ == '__main__':
    exit(main())