#!/usr/bin/env python3
"""
Quick start script for DXT Curator.

This script provides an interactive setup and demo of DXT Curator functionality.
"""

import os
import sys
import json
from pathlib import Path


def banner():
    """Display welcome banner."""
    print("🎯 DXT Curator Quick Start")
    print("=" * 50)
    print("This script will help you get started with DXT Curator")
    print("and run a quick demo of the functionality.")
    print()


def check_prerequisites():
    """Check if prerequisites are met."""
    print("🔍 Checking prerequisites...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    
    # Check if package is installed
    try:
        import dxt_curator
        print("✅ DXT Curator installed")
    except ImportError:
        print("❌ DXT Curator not installed. Run: pip install -e .")
        return False
    
    # Check API keys
    github_token = os.getenv('GITHUB_TOKEN')
    ai_key = os.getenv('OPENAI_API_KEY') or os.getenv('ANTHROPIC_API_KEY')
    
    if not github_token:
        print("⚠️  No GitHub token - discovery will be limited")
    else:
        print("✅ GitHub token configured")
    
    if not ai_key:
        print("⚠️  No AI API key - evaluation will not work")
        return False
    else:
        print("✅ AI API key configured")
    
    return True


def setup_demo_config():
    """Set up demo configuration."""
    print("\n⚙️  Setting up demo configuration...")
    
    demo_config = {
        "workflow": {
            "default_discovery_limit": 5,
            "clone_timeout": 30
        },
        "github": {
            "rate_limit_delay": 2.0,
            "max_search_results": 10
        },
        "ai": {
            "provider": "openai" if os.getenv('OPENAI_API_KEY') else "anthropic",
            "max_tokens": 500,
            "temperature": 0.1
        }
    }
    
    config_path = Path("dxt_curator_config.json.demo")
    with open(config_path, 'w') as f:
        json.dump(demo_config, f, indent=2)
    
    print(f"✅ Demo configuration created: {config_path}")
    return config_path


def run_discovery_demo():
    """Run a discovery demo."""
    print("\n🔍 Running discovery demo...")
    print("This will discover 5 repositories as a demonstration.")
    
    try:
        from dxt_curator.core import StrategicGitHubSearch
        
        searcher = StrategicGitHubSearch()
        print("🎯 Starting strategic search...")
        
        # Run a small discovery
        results = searcher.discover_dxt_repositories(max_total=5)
        
        print(f"📊 Found {len(results)} repositories:")
        for repo in results[:3]:  # Show first 3
            print(f"  • {repo.full_name} ({repo.stars} stars)")
        
        if len(results) > 3:
            print(f"  ... and {len(results) - 3} more")
        
        return results
        
    except Exception as e:
        print(f"❌ Discovery demo failed: {e}")
        return []


def run_evaluation_demo(repos):
    """Run an evaluation demo."""
    if not repos:
        print("⏭️  Skipping evaluation demo - no repositories found")
        return
    
    print("\n🤖 Running evaluation demo...")
    print("This will evaluate one repository with AI.")
    
    try:
        from dxt_curator.core import AIEvaluator
        
        # Get AI provider
        provider = "openai" if os.getenv('OPENAI_API_KEY') else "anthropic"
        evaluator = AIEvaluator(api_provider=provider)
        
        # Evaluate the first repository
        repo = repos[0]
        print(f"🔍 Evaluating: {repo.full_name}")
        
        repo_data = {
            'full_name': repo.full_name,
            'clone_url': repo.clone_url,
            'description': repo.description,
            'stars': repo.stars,
            'language': repo.language
        }
        
        decision = evaluator.evaluate_repo(repo_data)
        
        print(f"📋 Evaluation Results:")
        print(f"  Decision: {decision['decision'].upper()}")
        print(f"  Reason: {decision['reason']}")
        print(f"  Notes: {decision['notes']}")
        
    except Exception as e:
        print(f"❌ Evaluation demo failed: {e}")


def run_inventory_demo():
    """Run an inventory demo."""
    print("\n📊 Running inventory demo...")
    
    try:
        from dxt_curator import SimpleInventory
        
        inventory = SimpleInventory()
        summary = inventory.get_summary()
        
        print(f"📈 Inventory Summary:")
        print(f"  Total repositories: {summary.get('total_repos', 0)}")
        
        if summary.get('by_status'):
            print(f"  By status:")
            for status, count in summary['by_status'].items():
                print(f"    {status}: {count}")
        
        # Show a few recent repositories
        recent = inventory.get_recent_repos(limit=3)
        if recent:
            print(f"  Recent repositories:")
            for repo in recent:
                print(f"    • {repo.full_name} ({repo.status})")
        
    except Exception as e:
        print(f"❌ Inventory demo failed: {e}")


def show_next_steps():
    """Show next steps for the user."""
    print("\n🚀 Next Steps:")
    print("1. Run full discovery:")
    print("   dxt-curator discover 25")
    print()
    print("2. Check status:")
    print("   dxt-curator status")
    print()
    print("3. See what's ready to mirror:")
    print("   dxt-curator ready")
    print()
    print("4. Search inventory:")
    print("   dxt-curator search 'automation'")
    print()
    print("📚 Documentation:")
    print("  • README.md - Complete documentation")
    print("  • EXAMPLES.md - Usage examples")
    print("  • make help - See all available commands")


def main():
    """Main demo function."""
    banner()
    
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please fix the issues above.")
        return False
    
    # Set up demo configuration
    setup_demo_config()
    
    # Run demos
    repos = run_discovery_demo()
    run_evaluation_demo(repos)
    run_inventory_demo()
    
    # Show next steps
    show_next_steps()
    
    print("\n🎉 Demo complete! DXT Curator is ready to use.")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)