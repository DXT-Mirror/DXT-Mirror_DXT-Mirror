#!/usr/bin/env python3
"""
Test setup script for DXT Curator.

This script validates that the installation is working correctly
and runs a basic test workflow.
"""

import os
import sys
import json
from pathlib import Path


def test_imports():
    """Test that all modules can be imported."""
    print("🔍 Testing imports...")
    
    try:
        from dxt_curator import SimpleDXTWorkflow, SimpleInventory
        from dxt_curator.core import StrategicGitHubSearch, AIEvaluator
        from dxt_curator.utils import Config, get_sanitizer
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_configuration():
    """Test configuration loading."""
    print("🔧 Testing configuration...")
    
    try:
        from dxt_curator.utils.config import Config
        config = Config()
        print("✅ Configuration loaded successfully")
        return True
    except Exception as e:
        print(f"❌ Configuration failed: {e}")
        return False


def test_inventory():
    """Test inventory functionality."""
    print("📊 Testing inventory...")
    
    try:
        from dxt_curator import SimpleInventory
        inventory = SimpleInventory()
        
        # Test basic operations
        summary = inventory.get_summary()
        print(f"✅ Inventory working - {summary.get('total_repos', 0)} repos")
        return True
    except Exception as e:
        print(f"❌ Inventory test failed: {e}")
        return False


def test_security():
    """Test security components."""
    print("🛡️  Testing security...")
    
    try:
        from dxt_curator.utils.security import get_sanitizer
        sanitizer = get_sanitizer()
        
        # Test content sanitization
        test_content = "This is a test README file"
        result = sanitizer.sanitize_content(test_content)
        
        if result['content'] and not result['is_suspicious']:
            print("✅ Security components working")
            return True
        else:
            print("❌ Security test failed")
            return False
    except Exception as e:
        print(f"❌ Security test failed: {e}")
        return False


def test_api_keys():
    """Test API key configuration."""
    print("🔑 Testing API keys...")
    
    github_token = os.getenv('GITHUB_TOKEN')
    openai_key = os.getenv('OPENAI_API_KEY')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    
    if not github_token:
        print("⚠️  No GITHUB_TOKEN found - discovery will be limited")
    else:
        print("✅ GitHub token configured")
    
    if not openai_key and not anthropic_key:
        print("⚠️  No AI API key found - evaluation will not work")
        return False
    elif openai_key:
        print("✅ OpenAI API key configured")
    elif anthropic_key:
        print("✅ Anthropic API key configured")
    
    return True


def test_cli():
    """Test CLI functionality."""
    print("🖥️  Testing CLI...")
    
    try:
        import subprocess
        result = subprocess.run(['dxt-curator', '--help'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ CLI working")
            return True
        else:
            print(f"❌ CLI failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ CLI test failed: {e}")
        return False


def create_test_config():
    """Create a test configuration file."""
    print("⚙️  Creating test configuration...")
    
    test_config = {
        "ai": {
            "provider": "openai",
            "max_tokens": 500,
            "temperature": 0.1
        },
        "github": {
            "rate_limit_delay": 2.0,
            "max_search_results": 10
        },
        "workflow": {
            "default_discovery_limit": 5,
            "clone_timeout": 30
        }
    }
    
    config_path = Path("dxt_curator_config.json.test")
    with open(config_path, 'w') as f:
        json.dump(test_config, f, indent=2)
    
    print(f"✅ Test configuration created: {config_path}")
    return config_path


def main():
    """Run all tests."""
    print("🧪 DXT Curator Setup Test")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_configuration,
        test_inventory,
        test_security,
        test_api_keys,
        test_cli
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
        print()
    
    print("=" * 40)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! DXT Curator is ready to use.")
        print("\n🚀 Next steps:")
        print("1. Run: dxt-curator discover 5")
        print("2. Run: dxt-curator status")
        print("3. Check the README.md for more examples")
        return True
    else:
        print("❌ Some tests failed. Please check the configuration.")
        print("\n🔧 Common fixes:")
        print("- Copy .env.example to .env and add your API keys")
        print("- Run: pip install -e '.[dev]' to install dependencies")
        print("- Check that Python 3.8+ is installed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)