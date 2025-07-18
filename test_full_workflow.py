#!/usr/bin/env python3
"""
Full end-to-end test of the DXT Curator workflow.

This script will:
1. Search GitHub for DXT-related repositories
2. Pick one repository to evaluate
3. Clone and analyze it
4. Show the complete evaluation process
5. Report what we find

This is a safe test that won't create any mirrors - just discovery and evaluation.
"""

import os
import sys
import json
from pathlib import Path

# Add the package to Python path
sys.path.insert(0, str(Path(__file__).parent))

from dxt_curator.core.workflow import SimpleDXTWorkflow
from dxt_curator.core.discovery import StrategicGitHubSearch
from dxt_curator.core.evaluator import AIEvaluator

def test_full_workflow():
    """Run a complete end-to-end test of the DXT Curator workflow."""
    
    print("🧪 DXT Curator Full Workflow Test")
    print("=" * 50)
    
    # Check prerequisites
    github_token = os.getenv('GITHUB_MIRROR_TOKEN') or os.getenv('GITHUB_TOKEN')
    ai_key = os.getenv('OPENAI_API_KEY') or os.getenv('ANTHROPIC_API_KEY')
    
    if not github_token:
        print("⚠️  No GitHub token found. Set GITHUB_MIRROR_TOKEN or GITHUB_TOKEN")
        print("   Discovery will be limited by rate limits.")
    
    if not ai_key:
        print("❌ No AI API key found. Set OPENAI_API_KEY or ANTHROPIC_API_KEY")
        print("   Cannot run evaluation without AI API key.")
        return False
    
    print(f"✅ GitHub token: {'Available' if github_token else 'Missing'}")
    print(f"✅ AI API key: {'Available' if ai_key else 'Missing'}")
    
    try:
        # Step 1: Initialize workflow
        print("\n📋 Step 1: Initialize Workflow")
        print("-" * 30)
        workflow = SimpleDXTWorkflow(ai_provider="openai", mirror_org="DXT-Mirror")
        
        # Step 2: Search for repositories
        print("\n🔍 Step 2: Search GitHub for DXT Repositories")
        print("-" * 30)
        
        # Use discovery component directly for more control
        searcher = StrategicGitHubSearch(github_token)
        
        # Search for Claude/DXT related repositories
        print("🔍 Searching for Claude Desktop Extension repositories...")
        
        # Use strategic search terms
        search_terms = [
            "claude desktop extension",
            "claude-desktop",
            "claude extension",
            "anthropic claude tool"
        ]
        
        all_repos = []
        for term in search_terms[:2]:  # Limit to first 2 terms for test
            print(f"   Searching for: '{term}'")
            repos = searcher.search_repositories(term, max_results=10)
            all_repos.extend(repos)
            print(f"   Found: {len(repos)} repositories")
        
        # Remove duplicates
        unique_repos = []
        seen_urls = set()
        for repo in all_repos:
            if repo.clone_url not in seen_urls:
                unique_repos.append(repo)
                seen_urls.add(repo.clone_url)
        
        print(f"\n📊 Total unique repositories found: {len(unique_repos)}")
        
        if not unique_repos:
            print("❌ No repositories found. Try different search terms.")
            return False
        
        # Step 3: Pick a repository to evaluate
        print("\n🎯 Step 3: Select Repository for Evaluation")
        print("-" * 30)
        
        # Show available repositories
        print("📋 Available repositories:")
        for i, repo in enumerate(unique_repos[:10]):  # Show first 10
            print(f"   {i+1}. {repo.full_name} ({repo.stars} ⭐) - {repo.description[:60]}...")
        
        # Pick the first one with a reasonable description
        selected_repo = None
        for repo in unique_repos:
            if repo.description and len(repo.description) > 20 and repo.stars > 0:
                selected_repo = repo
                break
        
        if not selected_repo:
            selected_repo = unique_repos[0]  # Fallback to first repo
        
        print(f"\n🎯 Selected repository: {selected_repo.full_name}")
        print(f"   Description: {selected_repo.description}")
        print(f"   Stars: {selected_repo.stars}")
        print(f"   Language: {selected_repo.language}")
        print(f"   Clone URL: {selected_repo.clone_url}")
        
        # Step 4: Add to inventory
        print("\n📝 Step 4: Add to Inventory")
        print("-" * 30)
        
        # Convert to dict format for inventory
        repo_data = {
            'full_name': selected_repo.full_name,
            'clone_url': selected_repo.clone_url,
            'description': selected_repo.description,
            'stars': selected_repo.stars,
            'forks': selected_repo.forks,
            'language': selected_repo.language,
            'size': selected_repo.size,
            'topics': selected_repo.topics,
            'license': selected_repo.license,
            'created_at': selected_repo.created_at,
            'updated_at': selected_repo.updated_at,
            'archived': selected_repo.archived
        }
        
        uuid_val = workflow.inventory.add_repository(repo_data, "Test discovery")
        print(f"✅ Repository added to inventory with UUID: {uuid_val}")
        
        # Step 5: AI Evaluation
        print("\n🤖 Step 5: AI Evaluation")
        print("-" * 30)
        
        evaluator = AIEvaluator(api_provider="openai")
        
        # Evaluate the repository
        print(f"🤖 Evaluating {selected_repo.full_name} with AI...")
        print("   This may take 10-30 seconds...")
        
        evaluation = evaluator.evaluate_repo(repo_data)
        
        print(f"\n📊 AI Evaluation Results:")
        print(f"   Status: {evaluation.get('status', 'Unknown')}")
        print(f"   Reasoning: {evaluation.get('reasoning', 'No reasoning provided')}")
        print(f"   Relevance Score: {evaluation.get('relevance_score', 'N/A')}")
        print(f"   Future Actions: {evaluation.get('future_actions', 'None specified')}")
        
        # Step 6: Update inventory with evaluation
        print("\n📋 Step 6: Update Inventory")
        print("-" * 30)
        
        workflow.inventory.update_repository(
            selected_repo.clone_url,
            status=evaluation.get('status', 'evaluated'),
            evaluation_notes=evaluation.get('reasoning', 'AI evaluation completed'),
            decision_reason=evaluation.get('reasoning', 'AI decision'),
            future_actions=evaluation.get('future_actions', 'Pending decision')
        )
        
        print("✅ Inventory updated with evaluation results")
        
        # Step 7: Show inventory status
        print("\n📊 Step 7: Inventory Status")
        print("-" * 30)
        
        summary = workflow.inventory.get_summary()
        print(f"📊 Inventory Summary:")
        print(f"   Total repositories: {summary.get('total_repositories', 0)}")
        print(f"   By status: {summary.get('by_status', {})}")
        
        # Step 8: Show the repository record
        print("\n📄 Step 8: Repository Record")
        print("-" * 30)
        
        repo_record = workflow.inventory.get_repository(selected_repo.clone_url)
        if repo_record:
            print("📄 Complete repository record:")
            print(json.dumps(repo_record, indent=2, default=str))
        
        # Step 9: Test mirror manager (without actually mirroring)
        print("\n🪞 Step 9: Mirror Manager Test")
        print("-" * 30)
        
        if workflow.mirror_manager:
            # Test blocklist check
            is_blocked = workflow.mirror_manager.is_blocked(selected_repo.clone_url)
            if is_blocked:
                reason = workflow.mirror_manager.get_blocked_reason(selected_repo.clone_url)
                print(f"🚫 Repository is blocked: {reason}")
            else:
                print(f"✅ Repository is not blocked and could be mirrored")
            
            # Show daily limits
            daily_count = workflow.mirror_manager.get_daily_mirror_count()
            daily_limit = workflow.mirror_manager.daily_limit
            print(f"📊 Daily mirror count: {daily_count}/{daily_limit}")
        
        print("\n🎉 Test completed successfully!")
        print("=" * 50)
        
        print("\n📋 Summary:")
        print(f"   ✅ Found {len(unique_repos)} unique repositories")
        print(f"   ✅ Selected and evaluated: {selected_repo.full_name}")
        print(f"   ✅ AI evaluation status: {evaluation.get('status', 'Unknown')}")
        print(f"   ✅ Repository added to inventory")
        print(f"   ✅ Mirror manager ready")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_full_workflow()
    sys.exit(0 if success else 1)