#!/usr/bin/env python3
"""
Development setup script for DXT Curator.

This script sets up a complete development environment for DXT Curator,
including all dependencies and configuration.
"""

import os
import sys
import subprocess
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"⚙️  {description}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} is compatible")
    return True


def setup_environment():
    """Set up the development environment."""
    print("🚀 Setting up DXT Curator development environment...")
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Install package in development mode
    if not run_command("pip install -e .", "Installing DXT Curator in development mode"):
        return False
    
    # Install development dependencies
    if not run_command("pip install -e '.[dev]'", "Installing development dependencies"):
        return False
    
    # Create example configuration
    config_example = {
        "github": {
            "token": "your_github_token_here",
            "rate_limit_delay": 1.0,
            "max_search_results": 100
        },
        "ai": {
            "provider": "openai",
            "max_tokens": 1000,
            "temperature": 0.1
        },
        "workflow": {
            "default_discovery_limit": 50,
            "clone_timeout": 60
        }
    }
    
    config_path = Path("dxt_curator_config.json.example")
    if not config_path.exists():
        import json
        with open(config_path, 'w') as f:
            json.dump(config_example, f, indent=2)
        print(f"✅ Created example configuration file: {config_path}")
    
    # Create example environment file
    env_example = """# DXT Curator Environment Variables
# Copy this file to .env and fill in your API keys

# GitHub API token for repository discovery
GITHUB_TOKEN=your_github_token_here

# AI API key (choose one)
OPENAI_API_KEY=your_openai_key_here
# OR
ANTHROPIC_API_KEY=your_anthropic_key_here

# Optional: Logging configuration
LOG_LEVEL=INFO
LOG_FILE=dxt_curator.log
"""
    
    env_path = Path(".env.example")
    if not env_path.exists():
        with open(env_path, 'w') as f:
            f.write(env_example)
        print(f"✅ Created example environment file: {env_path}")
    
    print("\n🎉 Development environment setup complete!")
    print("\n📋 Next steps:")
    print("1. Copy .env.example to .env and add your API keys")
    print("2. Run: dxt-curator discover 10")
    print("3. Run: dxt-curator status")
    print("\n📚 Documentation:")
    print("- README.md: Complete documentation")
    print("- EXAMPLES.md: Usage examples")
    print("- pyproject.toml: Package configuration")
    
    return True


def main():
    """Main setup function."""
    if not setup_environment():
        print("❌ Setup failed")
        sys.exit(1)
    
    print("✅ Setup completed successfully!")


if __name__ == "__main__":
    main()