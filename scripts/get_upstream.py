#!/usr/bin/env python3
"""
Get Upstream URL Script

This script extracts the upstream repository URL from a DXT mirror repository.
Works with both local clones and remote repositories.

Usage:
    python scripts/get_upstream.py                           # Current directory
    python scripts/get_upstream.py /path/to/mirror/repo      # Local repository
    python scripts/get_upstream.py DXT-Mirror/owner_repo     # Remote repository
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path

# Add parent directory to path so we can import the modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from dxt_curator.core.mirror import GitHubMirrorManager


def main():
    parser = argparse.ArgumentParser(
        description='Get upstream URL from a DXT mirror repository',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Current directory
  %(prog)s /path/to/mirror/repo               # Local repository
  %(prog)s DXT-Mirror/milisp_awesome-claude-dxt  # Remote repository
        """
    )
    
    parser.add_argument('target', nargs='?', default='.',
                       help='Local path or remote repository (DXT-Mirror/name)')
    parser.add_argument('--setup', action='store_true',
                       help='Add upstream remote after finding URL')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    upstream_url = None
    
    # Check if target is a local path
    if os.path.exists(args.target):
        if args.verbose:
            print(f"🔍 Checking local repository: {args.target}")
        upstream_url = get_upstream_from_local(args.target, args.verbose)
    
    # Check if target looks like a GitHub repo (contains /)
    elif '/' in args.target:
        if args.verbose:
            print(f"🔍 Checking remote repository: {args.target}")
        upstream_url = get_upstream_from_remote(args.target, args.verbose)
    
    else:
        print("❌ Error: Target must be a local path or GitHub repository (DXT-Mirror/name)")
        return 1
    
    if not upstream_url:
        print("❌ Could not find upstream URL")
        return 1
    
    print(f"🎯 Upstream URL: {upstream_url}")
    
    # Optionally set up remote
    if args.setup and os.path.exists(args.target):
        setup_upstream_remote(args.target, upstream_url, args.verbose)
    
    return 0


def get_upstream_from_local(repo_path, verbose=False):
    """Get upstream URL from local repository git config."""
    try:
        # Check git config for stored upstream URL
        result = subprocess.run([
            'git', '-C', repo_path, 'config', 'mirror.upstream-url'
        ], capture_output=True, text=True, check=False)
        
        if result.returncode == 0:
            url = result.stdout.strip()
            if verbose:
                print(f"✅ Found upstream URL in git config: {url}")
            return url
        
        # Fallback: check remote URLs for patterns
        result = subprocess.run([
            'git', '-C', repo_path, 'remote', '-v'
        ], capture_output=True, text=True, check=True)
        
        for line in result.stdout.split('\n'):
            if 'upstream' in line and '(fetch)' in line:
                url = line.split()[1]
                if verbose:
                    print(f"✅ Found upstream remote: {url}")
                return url
        
        # Try to infer from origin if it's a DXT-Mirror
        for line in result.stdout.split('\n'):
            if 'origin' in line and '(fetch)' in line and 'DXT-Mirror' in line:
                origin_url = line.split()[1]
                # Convert DXT-Mirror/owner_repo to github.com/owner/repo
                if 'DXT-Mirror/' in origin_url:
                    parts = origin_url.split('DXT-Mirror/')[-1]
                    if '_' in parts:
                        repo_part = parts.replace('.git', '')
                        owner, repo = repo_part.split('_', 1)
                        inferred_url = f"https://github.com/{owner}/{repo}.git"
                        if verbose:
                            print(f"🔍 Inferred upstream URL: {inferred_url}")
                        return inferred_url
        
        return None
        
    except subprocess.CalledProcessError as e:
        if verbose:
            print(f"❌ Git command failed: {e}")
        return None


def get_upstream_from_remote(repo_name, verbose=False):
    """Get upstream URL from remote DXT-Mirror repository."""
    try:
        github_token = os.getenv('GITHUB_MIRROR_TOKEN') or os.getenv('GITHUB_TOKEN')
        if not github_token:
            if verbose:
                print("⚠️  No GitHub token found, trying public API...")
        
        mirror_manager = GitHubMirrorManager(github_token, "DXT-Mirror")
        
        # Get repository info
        url = f"https://api.github.com/repos/{repo_name}"
        response = mirror_manager.session.get(url)
        
        if response.status_code != 200:
            if verbose:
                print(f"❌ Repository not found: {repo_name}")
            return None
        
        repo_data = response.json()
        
        # Check description for upstream URL
        description = repo_data.get('description', '')
        if 'Upstream:' in description:
            # Extract URL from "Mirror of X | Upstream: URL"
            upstream_part = description.split('Upstream:')[-1].strip()
            if verbose:
                print(f"✅ Found upstream URL in description: {upstream_part}")
            return upstream_part
        
        # Check homepage
        homepage = repo_data.get('homepage')
        if homepage and 'github.com' in homepage:
            if verbose:
                print(f"✅ Found upstream URL in homepage: {homepage}")
            return homepage
        
        # Infer from repository name
        if repo_name.startswith('DXT-Mirror/') and '_' in repo_name:
            repo_part = repo_name.split('/')[-1]
            if '_' in repo_part:
                owner, repo = repo_part.split('_', 1)
                inferred_url = f"https://github.com/{owner}/{repo}"
                if verbose:
                    print(f"🔍 Inferred upstream URL: {inferred_url}")
                return inferred_url
        
        return None
        
    except Exception as e:
        if verbose:
            print(f"❌ API request failed: {e}")
        return None


def setup_upstream_remote(repo_path, upstream_url, verbose=False):
    """Add upstream remote to local repository."""
    try:
        print(f"🔧 Setting up upstream remote...")
        
        # Check if upstream remote already exists
        result = subprocess.run([
            'git', '-C', repo_path, 'remote'
        ], capture_output=True, text=True, check=True)
        
        if 'upstream' in result.stdout:
            print("ℹ️  Upstream remote already exists")
            if verbose:
                subprocess.run(['git', '-C', repo_path, 'remote', '-v'])
            return
        
        # Add upstream remote
        subprocess.run([
            'git', '-C', repo_path, 'remote', 'add', 'upstream', upstream_url
        ], check=True)
        
        print(f"✅ Added upstream remote: {upstream_url}")
        
        if verbose:
            print("\n📋 Current remotes:")
            subprocess.run(['git', '-C', repo_path, 'remote', '-v'])
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to set up upstream remote: {e}")


if __name__ == '__main__':
    exit(main())