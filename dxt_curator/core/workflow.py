"""
Simple AI-powered workflow orchestration for DXT repository curation.

This module provides a high-level interface that coordinates the discovery,
evaluation, and inventory management processes. It represents the culmination
of our AI-first approach to repository curation.

Key Design Principles:
1. Simplicity: Hide complexity behind simple, intuitive interfaces
2. Flexibility: Support various workflow patterns and use cases
3. Transparency: Provide clear visibility into the curation process
4. Extensibility: Easy to add new workflow steps and customizations

The workflow orchestrates three main components:
1. Strategic Discovery: Finding relevant repositories
2. AI Evaluation: Intelligent analysis and decision making
3. Inventory Management: Natural language tracking and organization

This creates a complete pipeline from raw GitHub data to curated,
decision-ready repository collections.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

from .discovery import StrategicGitHubSearch
from .evaluator import AIEvaluator
from .inventory import SimpleInventory
from .file_inventory import FileInventory
from .mirror import GitHubMirrorManager


class SimpleDXTWorkflow:
    """
    Main workflow orchestrator for DXT repository curation.
    
    This class provides a simple, high-level interface for the entire
    curation process. It coordinates the discovery, evaluation, and
    inventory management components to create a seamless experience.
    
    The workflow is designed to be:
    - Easy to use: Simple method calls for complex operations
    - Flexible: Support different workflow patterns
    - Transparent: Clear reporting of what's happening
    - Reliable: Robust error handling and recovery
    """
    
    def __init__(self, github_token: str = None, ai_provider: str = "openai", mirror_org: str = "DXT-Mirror", mirror_blocklist: List[str] = None, temp_dir: str = None):
        """
        Initialize the workflow orchestrator.
        
        Args:
            github_token: GitHub API token for discovery (optional)
            ai_provider: AI service provider ("openai" or "anthropic")
            mirror_org: GitHub organization for mirror repositories
            mirror_blocklist: List of URL patterns to block from mirroring
            temp_dir: Custom temporary directory for cloning (optional)
        """
        # Get API keys from environment if not provided
        self.github_token = github_token or os.getenv('GITHUB_MIRROR_TOKEN') or os.getenv('GITHUB_TOKEN')
        self.ai_key = os.getenv('OPENAI_API_KEY') or os.getenv('ANTHROPIC_API_KEY')
        self.mirror_org = mirror_org
        self.mirror_blocklist = mirror_blocklist or []
        self.temp_dir = temp_dir
        
        # Validate configuration
        if not self.github_token:
            print("⚠️  Warning: No GITHUB_MIRROR_TOKEN or GITHUB_TOKEN found. Discovery will be limited by rate limits.")
        
        if not self.ai_key:
            print("❌ Error: No AI API key found. Set OPENAI_API_KEY or ANTHROPIC_API_KEY")
            return
        
        # Initialize components
        self.searcher = StrategicGitHubSearch(self.github_token)
        self.evaluator = AIEvaluator(api_provider=ai_provider)
        self.inventory = FileInventory()  # Use file-based inventory
        self.mirror_manager = GitHubMirrorManager(self.github_token, mirror_org, self.mirror_blocklist, temp_dir=temp_dir) if self.github_token else None
        
        print("🚀 DXT Workflow ready!")
        print(f"   GitHub API: {'✓' if self.github_token else '✗'}")
        print(f"   AI API: ✓ ({ai_provider.upper()})")
        print(f"   Mirror Org: {mirror_org}")
        print(f"   Mirroring: {'✓' if self.mirror_manager else '✗'}")
        if self.mirror_manager:
            print(f"   Blocklist: {len(self.mirror_manager.blocklist)} patterns")
    
    def discover_and_evaluate(self, limit: int = 50, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Run the complete discovery and evaluation workflow.
        
        This method executes the full pipeline:
        1. Strategic discovery of repositories
        2. Quality filtering and relevance ranking
        3. AI-powered evaluation of each repository
        4. Inventory updates with natural language decisions
        
        Args:
            limit: Maximum number of repositories to process
            filters: Optional filters for discovery (min_stars, days, etc.)
            
        Returns:
            Dictionary with workflow results and summary
        """
        print(f"\\n🔍 Starting discovery and evaluation workflow (limit: {limit})...")
        
        # Set default filters
        if filters is None:
            filters = {}
        
        # Phase 1: Discovery
        print("\\n📡 Phase 1: Strategic Repository Discovery")
        results = self.searcher.discover_dxt_repositories()
        
        # Apply filters
        if filters.get('days'):
            results = self.searcher.filter_by_recency(results, filters['days'])
            print(f"📅 After recency filter: {len(results)} repositories")
        
        if filters.get('min_stars'):
            results = self.searcher.filter_by_activity(results, filters['min_stars'])
            print(f"⭐ After stars filter: {len(results)} repositories")
        
        # Rank by relevance and apply limit
        results = self.searcher.rank_by_relevance(results)
        if limit:
            results = results[:limit]
            print(f"🔢 Processing top {len(results)} repositories by relevance")
        
        # Convert to evaluation format
        repo_data = []
        for result in results:
            repo_data.append({
                'full_name': result.full_name,
                'clone_url': result.clone_url,
                'description': result.description,
                'stars': result.stars,
                'language': result.language,
                'updated_at': result.updated_at,
                'size': result.size,
                'topics': result.topics
            })
        
        # Save discovered repositories
        with open('discovered_repos.json', 'w') as f:
            json.dump(repo_data, f, indent=2)
        print(f"📁 Discovered repositories saved to discovered_repos.json")
        
        # Phase 2: AI Evaluation
        print("\\n🤖 Phase 2: AI-Powered Evaluation")
        evaluation_results = self.evaluator.process_discovered_repos('discovered_repos.json')
        
        # Generate summary
        summary = {
            'workflow_completed_at': datetime.now().isoformat(),
            'total_discovered': len(repo_data),
            'total_evaluated': sum(len(repos) for repos in evaluation_results.values()),
            'results': evaluation_results,
            'inventory_summary': self.inventory.get_summary()
        }
        
        # Display results
        print(f"\\n📊 Workflow Results:")
        print(f"  Discovered: {summary['total_discovered']} repositories")
        print(f"  Evaluated: {summary['total_evaluated']} repositories")
        print(f"  Ready to Mirror: {len(evaluation_results['mirror'])}")
        print(f"  Rejected: {len(evaluation_results['reject'])}")
        print(f"  Check Later: {len(evaluation_results['check_later'])}")
        
        # Show examples of each category
        self._show_result_examples(evaluation_results)
        
        return summary
    
    def mirror_approved_repositories(self, limit: int = None) -> Dict[str, Any]:
        """
        Mirror all repositories approved for mirroring.
        
        Args:
            limit: Maximum number of repositories to mirror (optional)
            
        Returns:
            Mirror operation results
        """
        if not self.mirror_manager:
            print("❌ Error: Mirror manager not initialized. Check GitHub token.")
            return {'error': 'Mirror manager not available'}
        
        print(f"\n🪞 Starting mirror operation...")
        
        # Get repositories ready for mirroring
        ready_repos = self.inventory.get_repositories_by_status('mirror')
        
        if not ready_repos:
            print("ℹ️  No repositories ready for mirroring.")
            return {'mirrored': 0, 'message': 'No repositories ready for mirroring'}
        
        if limit:
            ready_repos = ready_repos[:limit]
        
        print(f"📋 Found {len(ready_repos)} repositories ready for mirroring")
        
        mirrored_count = 0
        failed_count = 0
        blocked_count = 0
        rate_limited_count = 0
        results = []
        
        for repo in ready_repos:
            try:
                repo_url = repo['repository_url']
                full_name = repo['metadata']['full_name']
                print(f"\n🔄 Processing {full_name}...")
                
                # Check if repository is blocked
                if self.mirror_manager.is_blocked(repo_url):
                    blocked_reason = self.mirror_manager.get_blocked_reason(repo_url)
                    print(f"🚫 Repository blocked: {blocked_reason}")
                    
                    # Update inventory with blocked status
                    self.inventory.update_repository(repo_url, 
                                                   status='blocked',
                                                   notes=f"Blocked from mirroring: {blocked_reason}")
                    blocked_count += 1
                    continue
                
                # Check if already mirrored
                existing_mirror = self.mirror_manager.get_mirror_info(full_name)
                if existing_mirror:
                    print(f"ℹ️  Repository already mirrored: {existing_mirror['html_url']}")
                    # Update status to mirrored
                    self.inventory.update_repository(repo_url, 
                                                   status='mirrored', 
                                                   notes=f"Mirror exists at {existing_mirror['html_url']}")
                    mirrored_count += 1
                    continue
                
                # Mirror the repository
                result = self.mirror_manager.clone_and_mirror(repo['metadata'])
                
                # Handle blocked result from mirror manager
                if result.get('status') == 'blocked':
                    print(f"🚫 Repository blocked: {result.get('error')}")
                    self.inventory.update_repository(repo_url, 
                                                   status='blocked',
                                                   notes=f"Blocked from mirroring: {result.get('error')}")
                    blocked_count += 1
                    continue
                
                # Handle rate-limited result
                if result.get('status') == 'rate_limited':
                    print(f"⏸️  Repository rate-limited: {result.get('error')}")
                    self.inventory.update_repository(repo_url, 
                                                   status='rate_limited',
                                                   notes=f"Rate limited - added to retry queue: {result.get('error')}",
                                                   future_actions="Will retry tomorrow when daily limit resets")
                    rate_limited_count += 1
                    continue
                
                # Update inventory with mirror information
                self.inventory.update_repository(repo_url, 
                                               status='mirrored',
                                               notes=f"Successfully mirrored to {result['mirror_url']}",
                                               future_actions=f"Monitor for updates from {repo_url}")
                
                results.append(result)
                mirrored_count += 1
                
            except Exception as e:
                print(f"❌ Failed to mirror {full_name}: {e}")
                # Update inventory with error
                self.inventory.update_repository(repo_url, 
                                               status='mirror_failed',
                                               notes=f"Mirror failed: {str(e)}")
                failed_count += 1
                continue
        
        print(f"\n🎉 Mirror operation completed!")
        print(f"   ✅ Successfully mirrored: {mirrored_count}")
        print(f"   🚫 Blocked: {blocked_count}")
        print(f"   ⏸️  Rate limited: {rate_limited_count}")
        print(f"   ❌ Failed: {failed_count}")
        
        if rate_limited_count > 0:
            remaining = self.mirror_manager.get_remaining_daily_mirrors()
            print(f"   📊 Daily mirrors remaining: {remaining}")
            print(f"   📝 Rate-limited repositories added to retry queue")
        
        return {
            'mirrored': mirrored_count,
            'blocked': blocked_count,
            'rate_limited': rate_limited_count,
            'failed': failed_count,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
    
    def sync_mirrors(self, limit: int = None) -> Dict[str, Any]:
        """
        Sync existing mirror repositories with their originals.
        
        Args:
            limit: Maximum number of repositories to sync (optional)
            
        Returns:
            Sync operation results
        """
        if not self.mirror_manager:
            print("❌ Error: Mirror manager not initialized. Check GitHub token.")
            return {'error': 'Mirror manager not available'}
        
        print(f"\n🔄 Starting sync operation...")
        
        # Get mirrored repositories
        mirrored_repos = self.inventory.get_repositories_by_status('mirrored')
        
        if not mirrored_repos:
            print("ℹ️  No mirrored repositories found.")
            return {'synced': 0, 'message': 'No mirrored repositories found'}
        
        if limit:
            mirrored_repos = mirrored_repos[:limit]
        
        print(f"📋 Found {len(mirrored_repos)} mirrored repositories")
        
        synced_count = 0
        failed_count = 0
        results = []
        
        for repo in mirrored_repos:
            try:
                repo_name = repo['metadata']['full_name']
                print(f"\n🔄 Syncing {repo_name}...")
                
                # Get mirror info
                mirror_info = self.mirror_manager.get_mirror_info(repo_name)
                if not mirror_info:
                    print(f"⚠️  Mirror repository not found for {repo_name}")
                    continue
                
                # Sync repository
                result = self.mirror_manager.sync_repository(repo['metadata'], mirror_info)
                
                # Update inventory
                self.inventory.update_repository(repo['repository_url'], 
                                               notes=f"Synced at {result['timestamp']}")
                
                results.append(result)
                synced_count += 1
                
            except Exception as e:
                print(f"❌ Failed to sync {repo['metadata']['full_name']}: {e}")
                failed_count += 1
                continue
        
        print(f"\n🎉 Sync operation completed!")
        print(f"   ✅ Successfully synced: {synced_count}")
        print(f"   ❌ Failed: {failed_count}")
        
        return {
            'synced': synced_count,
            'failed': failed_count,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
    
    def process_retry_queue(self, limit: int = None) -> Dict[str, Any]:
        """
        Process repositories in the retry queue.
        
        Args:
            limit: Maximum number of repositories to process
            
        Returns:
            Processing results
        """
        if not self.mirror_manager:
            print("❌ Error: Mirror manager not initialized. Check GitHub token.")
            return {'error': 'Mirror manager not available'}
        
        print(f"\n📝 Processing retry queue...")
        
        # Get queue status
        queue = self.mirror_manager.get_retry_queue()
        remaining_daily = self.mirror_manager.get_remaining_daily_mirrors()
        
        print(f"📊 Queue size: {len(queue)} repositories")
        print(f"📊 Daily mirrors remaining: {remaining_daily}")
        
        if not queue:
            print("📭 Retry queue is empty")
            return {
                'processed': 0,
                'queue_size': 0,
                'remaining_daily': remaining_daily,
                'message': 'Queue is empty'
            }
        
        if remaining_daily == 0:
            print("⏸️  Cannot process retry queue - daily limit reached")
            return {
                'processed': 0,
                'queue_size': len(queue),
                'remaining_daily': 0,
                'message': 'Daily limit reached'
            }
        
        # Process the queue
        result = self.mirror_manager.process_retry_queue(limit)
        
        # Update inventory for successfully processed repositories
        for repo_result in result.get('results', []):
            if repo_result.get('status') == 'success':
                repo_url = f"https://github.com/{repo_result['original_repo']}.git"
                self.inventory.update_repository(repo_url, 
                                               status='mirrored',
                                               notes=f"Successfully mirrored from retry queue to {repo_result['mirror_url']}",
                                               future_actions=f"Monitor for updates from {repo_url}")
        
        return result
    
    def _show_result_examples(self, results: Dict[str, List[str]]) -> None:
        """
        Display examples from each evaluation category.
        
        This helps users understand what types of repositories were found
        and why they were categorized as they were.
        """
        if results['mirror']:
            print(f"\\n✅ Ready to Mirror (showing first 3):")
            for repo_name in results['mirror'][:3]:
                # Convert repo_name to URL format for file inventory
                repo_url = f"https://github.com/{repo_name}.git"
                entry = self.inventory.get_repository(repo_url)
                if entry:
                    stars = entry.get('metadata', {}).get('stars', 0)
                    reasoning = entry.get('curation', {}).get('evaluation_notes', '')
                    print(f"  {repo_name} ({stars} ⭐)")
                    print(f"    AI Reasoning: {reasoning}")
        
        if results['check_later']:
            print(f"\\n⏰ Check Later (showing first 3):")
            for repo_name in results['check_later'][:3]:
                repo_url = f"https://github.com/{repo_name}.git"
                entry = self.inventory.get_repository(repo_url)
                if entry:
                    stars = entry.get('metadata', {}).get('stars', 0)
                    reasoning = entry.get('curation', {}).get('evaluation_notes', '')
                    print(f"  {repo_name} ({stars} ⭐)")
                    print(f"    AI Reasoning: {reasoning}")
        
        if results['reject']:
            print(f"\\n❌ Rejected (showing first 2):")
            for repo_name in results['reject'][:2]:
                repo_url = f"https://github.com/{repo_name}.git"
                entry = self.inventory.get_repository(repo_url)
                if entry:
                    reasoning = entry.get('curation', {}).get('evaluation_notes', '')
                    print(f"  {repo_name}")
                    print(f"    AI Reasoning: {reasoning}")
    
    def show_status(self) -> None:
        """
        Display current inventory status.
        
        This provides a quick overview of the current state of the
        repository curation process.
        """
        print("\\n📋 Current Inventory Status:")
        summary = self.inventory.get_summary()
        
        print(f"Total repositories: {summary['total_repositories']}")
        print(f"Storage location: {summary['storage_location']}")
        
        if summary['total_repositories'] > 0:
            print("\\nBy status:")
            for status, count in summary['by_status'].items():
                print(f"  {status}: {count}")
        else:
            print("No repositories in inventory yet.")
    
    def show_ready_to_mirror(self) -> None:
        """
        Display repositories that are ready for mirroring.
        
        This shows detailed information about repositories that the AI
        has determined are valuable and ready for mirroring.
        """
        mirror_repos = self.inventory.get_repositories_by_status('mirror')
        
        if not mirror_repos:
            print("\\n📝 No repositories currently ready to mirror.")
            print("Run discovery and evaluation workflow first.")
            return
        
        print(f"\\n🪞 Ready to Mirror ({len(mirror_repos)} repositories):")
        print("=" * 60)
        
        for repo in mirror_repos:
            metadata = repo.get('metadata', {})
            curation = repo.get('curation', {})
            
            print(f"\\n{metadata.get('full_name', 'Unknown')} ({metadata.get('stars', 0)} ⭐)")
            print(f"Description: {metadata.get('description', 'No description')}")
            print(f"Language: {metadata.get('language', 'Unknown')}")
            print(f"AI Evaluation: {curation.get('evaluation_notes', 'No evaluation')}")
            if curation.get('notes'):
                print(f"Notes: {curation.get('notes')}")
            if curation.get('future_actions'):
                print(f"Future Actions: {curation.get('future_actions')}")
            print("-" * 40)
    
    def recheck_later_repos(self) -> Dict[str, Any]:
        """
        Recheck repositories marked for later review.
        
        This is useful for repositories that were in early development
        or showed promise but weren't ready for mirroring at the time
        of initial evaluation.
        
        Returns:
            Dictionary with recheck results
        """
        print("\\n🔄 Rechecking repositories marked for later review...")
        
        check_later_repos = self.inventory.get_repositories_by_status('check_later')
        
        if not check_later_repos:
            print("No repositories marked for later review.")
            return {'rechecked': 0, 'results': {}}
        
        print(f"Found {len(check_later_repos)} repositories to recheck:")
        for repo in check_later_repos:
            metadata = repo.get('metadata', {})
            curation = repo.get('curation', {})
            print(f"  {metadata.get('full_name', 'Unknown')} - {curation.get('evaluation_notes', 'No evaluation')}")
        
        # Execute recheck
        results = self.evaluator.recheck_repos()
        
        # Display results
        print(f"\\n📊 Recheck Results:")
        print(f"Rechecked: {results['rechecked']} repositories")
        
        if results['results']:
            for decision, repos in results['results'].items():
                if repos:
                    print(f"  {decision.title()}: {len(repos)}")
                    for repo_name in repos[:3]:  # Show first 3 examples
                        # Convert repo_name to URL format for file inventory
                        repo_url = f"https://github.com/{repo_name}.git"
                        entry = self.inventory.get_repository(repo_url)
                        if entry:
                            evaluation_notes = entry.get('curation', {}).get('evaluation_notes', 'No evaluation')
                            print(f"    {repo_name} - {evaluation_notes}")
        
        return results
    
    def search_inventory(self, query: str) -> None:
        """
        Search through the inventory using natural language.
        
        This demonstrates the power of storing information in natural
        language format - we can search across all text fields to find
        relevant repositories.
        
        Args:
            query: Search terms to look for
        """
        print(f"\\n🔍 Searching inventory for: '{query}'")
        
        repos = self.inventory.search_repositories(query)
        
        if not repos:
            print("No repositories found matching query.")
            return
        
        print(f"Found {len(repos)} repositories:")
        print("=" * 50)
        
        for repo in repos:
            metadata = repo.get('metadata', {})
            curation = repo.get('curation', {})
            
            print(f"\\n{metadata.get('full_name', 'Unknown')} ({curation.get('status', 'unknown')}) - {metadata.get('stars', 0)} ⭐")
            if metadata.get('description'):
                print(f"Description: {metadata.get('description')}")
            if curation.get('evaluation_notes'):
                print(f"AI Evaluation: {curation.get('evaluation_notes')}")
            if curation.get('notes'):
                print(f"Notes: {curation.get('notes')}")
            print("-" * 30)
    
    def export_for_ai_analysis(self, filename: str = "inventory_for_ai.json") -> None:
        """
        Export inventory in AI-friendly format for further analysis.
        
        This creates a comprehensive export that can be used for:
        - AI-powered analysis of patterns and trends
        - Bulk operations on repository sets
        - Integration with other tools and workflows
        
        Args:
            filename: Output filename
        """
        print(f"\\n📤 Exporting inventory for AI analysis...")
        
        data = self.inventory.export_for_ai()
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"📁 Exported {len(data)} repositories to {filename}")
        print("\\nYou can now use this data for:")
        print("- AI-powered pattern analysis")
        print("- Bulk repository operations")
        print("- Integration with other tools")
        print("- Custom reporting and analytics")
    
    def get_workflow_suggestions(self) -> List[str]:
        """
        Get AI-powered suggestions for next steps.
        
        This method analyzes the current inventory state and provides
        intelligent suggestions for what to do next.
        
        Returns:
            List of suggested actions
        """
        summary = self.inventory.get_summary()
        suggestions = []
        
        if summary['total_repos'] == 0:
            suggestions.append("Run discovery workflow to find DXT repositories")
        
        mirror_count = summary['by_status'].get('mirror', 0)
        check_later_count = summary['by_status'].get('check_later', 0)
        
        if mirror_count > 0:
            suggestions.append(f"Set up mirroring for {mirror_count} approved repositories")
        
        if check_later_count > 0:
            suggestions.append(f"Recheck {check_later_count} repositories marked for later review")
        
        if summary['total_repos'] > 0:
            suggestions.append("Export inventory for AI analysis and pattern recognition")
        
        return suggestions


def main():
    """
    CLI interface for the workflow orchestrator.
    
    This provides a simple command-line interface for running the
    complete DXT curation workflow.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='DXT Repository Curation Workflow')
    parser.add_argument('--discover', type=int, metavar='N', 
                       help='Discover and evaluate N repositories')
    parser.add_argument('--status', action='store_true', 
                       help='Show current inventory status')
    parser.add_argument('--ready', action='store_true', 
                       help='Show repositories ready to mirror')
    parser.add_argument('--recheck', action='store_true', 
                       help='Recheck repositories marked for later')
    parser.add_argument('--search', metavar='QUERY', 
                       help='Search through inventory')
    parser.add_argument('--export', action='store_true', 
                       help='Export inventory for AI analysis')
    parser.add_argument('--api', choices=['openai', 'anthropic'], default='openai',
                       help='AI API provider')
    parser.add_argument('--min-stars', type=int, default=0,
                       help='Minimum stars filter for discovery')
    parser.add_argument('--days', type=int, default=365,
                       help='Only consider repos updated in last N days')
    
    args = parser.parse_args()
    
    # Initialize workflow
    try:
        workflow = SimpleDXTWorkflow(ai_provider=args.api)
    except Exception as e:
        print(f"❌ Failed to initialize workflow: {e}")
        return
    
    # Execute requested action
    if args.discover:
        filters = {}
        if args.min_stars:
            filters['min_stars'] = args.min_stars
        if args.days:
            filters['days'] = args.days
        
        workflow.discover_and_evaluate(args.discover, filters)
    
    elif args.status:
        workflow.show_status()
    
    elif args.ready:
        workflow.show_ready_to_mirror()
    
    elif args.recheck:
        workflow.recheck_later_repos()
    
    elif args.search:
        workflow.search_inventory(args.search)
    
    elif args.export:
        workflow.export_for_ai_analysis()
    
    else:
        # Show help and suggestions
        parser.print_help()
        print("\\n💡 Suggested next steps:")
        suggestions = workflow.get_workflow_suggestions()
        for suggestion in suggestions:
            print(f"  - {suggestion}")
        
        print("\\n📖 Example usage:")
        print("  python -m dxt_curator.core.workflow --discover 20")
        print("  python -m dxt_curator.core.workflow --status")
        print("  python -m dxt_curator.core.workflow --ready")


if __name__ == "__main__":
    main()