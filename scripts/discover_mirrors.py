#!/usr/bin/env python3
"""
Mirror Discovery Script

This script discovers all mirror repositories in the DXT-Mirror organization,
extracts their upstream URLs from various sources, and can perform bulk operations.

Usage:
    python scripts/discover_mirrors.py --list                    # List all mirrors
    python scripts/discover_mirrors.py --setup                   # Setup upstream for all
    python scripts/discover_mirrors.py --sync                    # Sync all mirrors
    python scripts/discover_mirrors.py --fix                     # Fix missing upstream URLs
    python scripts/discover_mirrors.py --export mirrors.json     # Export to JSON
"""

import argparse
import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path so we can import the modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from dxt_curator.core.mirror import GitHubMirrorManager


def main():
    parser = argparse.ArgumentParser(
        description='Discover and manage all DXT mirror repositories',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --list                     # List all mirrors with upstream URLs
  %(prog)s --setup                    # Setup upstream remotes for all mirrors  
  %(prog)s --sync                     # Sync all mirrors with upstream
  %(prog)s --fix                      # Fix mirrors missing upstream URLs
  %(prog)s --export mirrors.json      # Export mirror data to JSON
  %(prog)s --filter claude            # Filter mirrors containing 'claude'
        """
    )
    
    # Action arguments
    parser.add_argument('--list', action='store_true',
                       help='List all mirror repositories')
    parser.add_argument('--setup', action='store_true',
                       help='Setup upstream remotes for all mirrors')
    parser.add_argument('--sync', action='store_true',
                       help='Sync all mirrors with their upstream')
    parser.add_argument('--fix', action='store_true',
                       help='Fix mirrors missing upstream URLs')
    parser.add_argument('--export', metavar='FILE',
                       help='Export mirror data to JSON file')
    
    # Filter arguments
    parser.add_argument('--filter', metavar='TERM',
                       help='Filter mirrors by name containing term')
    parser.add_argument('--limit', type=int, metavar='N',
                       help='Limit number of mirrors to process')
    
    # Optional arguments
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without doing it')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Initialize mirror manager
    try:
        github_token = os.getenv('GITHUB_MIRROR_TOKEN') or os.getenv('GITHUB_TOKEN')
        if not github_token:
            print("❌ Error: No GITHUB_MIRROR_TOKEN or GITHUB_TOKEN found")
            return 1
        
        mirror_manager = GitHubMirrorManager(github_token, "DXT-Mirror")
        print("🔍 Discovering mirrors in DXT-Mirror organization...")
        
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return 1
    
    # Discover all mirrors
    try:
        mirrors = discover_all_mirrors(mirror_manager, args.verbose)
        
        # Apply filters
        if args.filter:
            mirrors = [m for m in mirrors if args.filter.lower() in m['name'].lower()]
            print(f"🔍 Filtered to {len(mirrors)} mirrors containing '{args.filter}'")
        
        if args.limit:
            mirrors = mirrors[:args.limit]
            print(f"📝 Limited to first {len(mirrors)} mirrors")
        
        print(f"📋 Found {len(mirrors)} mirror repositories")
        
    except Exception as e:
        print(f"❌ Failed to discover mirrors: {e}")
        return 1
    
    # Execute requested action
    try:
        if args.list or not any([args.setup, args.sync, args.fix, args.export]):
            list_mirrors(mirrors, args.verbose)
            
        if args.setup:
            setup_upstream_remotes(mirrors, args.dry_run, args.verbose)
            
        if args.sync:
            sync_all_mirrors(mirrors, args.dry_run, args.verbose)
            
        if args.fix:
            fix_missing_upstream(mirrors, mirror_manager, args.dry_run, args.verbose)
            
        if args.export:
            export_mirrors(mirrors, args.export, args.verbose)
            
    except KeyboardInterrupt:
        print("\n⏸️  Operation interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Operation failed: {e}")
        return 1
    
    return 0


def discover_all_mirrors(mirror_manager: GitHubMirrorManager, verbose: bool = False) -> List[Dict[str, Any]]:
    """Discover all repositories in the DXT-Mirror organization."""
    mirrors = []
    page = 1
    per_page = 100
    
    while True:
        if verbose:
            print(f"📄 Fetching page {page}...")
        
        # Get repositories from GitHub API
        url = f"https://api.github.com/orgs/DXT-Mirror/repos"
        params = {
            'page': page,
            'per_page': per_page,
            'sort': 'name',
            'type': 'public'
        }
        
        response = mirror_manager.session.get(url, params=params)
        response.raise_for_status()
        
        repos = response.json()
        if not repos:
            break
        
        for repo in repos:
            # Skip the main DXT-Mirror repository itself
            if repo['name'] == 'DXT-Mirror_DXT-Mirror':
                continue
                
            # Include all repositories except the main one (we'll filter mirrors later)
            mirror_info = extract_mirror_info(repo, verbose)
            mirrors.append(mirror_info)
        
        page += 1
    
    return mirrors


def extract_mirror_info(repo: Dict[str, Any], verbose: bool = False) -> Dict[str, Any]:
    """Extract mirror information and upstream URL from repository data."""
    name = repo['name']
    description = repo.get('description', '')
    homepage = repo.get('homepage', '')
    
    # Try to find upstream URL
    upstream_url = None
    source_method = None
    
    # Method 1: Parse description for "Upstream: URL"
    if 'Upstream:' in description:
        try:
            upstream_url = description.split('Upstream:')[-1].strip()
            source_method = 'description'
        except:
            pass
    
    # Method 2: Use homepage
    if not upstream_url and homepage and 'github.com' in homepage:
        upstream_url = homepage
        source_method = 'homepage'
    
    # Method 3: Infer from repository name
    if not upstream_url and '_' in name:
        try:
            owner, repo_name = name.split('_', 1)
            upstream_url = f"https://github.com/{owner}/{repo_name}"
            source_method = 'inferred'
        except:
            pass
    
    if verbose and upstream_url:
        print(f"  ✅ {name} → {upstream_url} ({source_method})")
    elif verbose:
        print(f"  ⚠️  {name} → No upstream URL found")
    
    return {
        'name': name,
        'full_name': repo['full_name'],
        'description': description,
        'homepage': homepage,
        'clone_url': repo['clone_url'],
        'ssh_url': repo['ssh_url'],
        'html_url': repo['html_url'],
        'upstream_url': upstream_url,
        'upstream_source': source_method,
        'stars': repo.get('stargazers_count', 0),
        'forks': repo.get('forks_count', 0),
        'updated_at': repo.get('updated_at'),
        'topics': repo.get('topics', [])
    }


def list_mirrors(mirrors: List[Dict[str, Any]], verbose: bool = False):
    """List all discovered mirrors with their upstream URLs."""
    print("\n📋 DXT Mirror Repositories:")
    print("=" * 80)
    
    for mirror in mirrors:
        name = mirror['name']
        upstream = mirror.get('upstream_url', 'Unknown')
        source = mirror.get('upstream_source', '')
        stars = mirror.get('stars', 0)
        
        status_icon = "✅" if upstream != 'Unknown' else "⚠️ "
        
        print(f"{status_icon} {name} ({stars} ⭐)")
        print(f"   Mirror: {mirror['html_url']}")
        print(f"   Upstream: {upstream}")
        
        if verbose:
            print(f"   Source: {source}")
            print(f"   Description: {mirror.get('description', 'No description')}")
            if mirror.get('topics'):
                print(f"   Topics: {', '.join(mirror['topics'])}")
        
        print()


def setup_upstream_remotes(mirrors: List[Dict[str, Any]], dry_run: bool = False, verbose: bool = False):
    """Setup upstream remotes for all mirrors."""
    print(f"\n🔧 Setting up upstream remotes for {len(mirrors)} mirrors...")
    
    if dry_run:
        print("🔍 Dry run - showing what would be done:")
        for mirror in mirrors:
            if mirror.get('upstream_url'):
                print(f"  Would setup upstream for {mirror['name']} → {mirror['upstream_url']}")
            else:
                print(f"  ⚠️  Cannot setup {mirror['name']} - no upstream URL")
        return
    
    success_count = 0
    error_count = 0
    
    for mirror in mirrors:
        name = mirror['name']
        upstream_url = mirror.get('upstream_url')
        
        if not upstream_url:
            print(f"⚠️  Skipping {name} - no upstream URL found")
            continue
        
        try:
            print(f"🔧 Setting up {name}...")
            
            # Clone mirror and setup upstream
            import tempfile
            import subprocess
            
            with tempfile.TemporaryDirectory() as temp_dir:
                repo_path = Path(temp_dir) / name
                
                # Clone mirror
                subprocess.run([
                    'git', 'clone', mirror['clone_url'], str(repo_path)
                ], check=True, capture_output=not verbose)
                
                # Add upstream remote if it doesn't exist
                result = subprocess.run([
                    'git', '-C', str(repo_path), 'remote'
                ], capture_output=True, text=True)
                
                if 'upstream' not in result.stdout:
                    subprocess.run([
                        'git', '-C', str(repo_path), 'remote', 'add', 'upstream', upstream_url
                    ], check=True, capture_output=not verbose)
                    
                    if verbose:
                        print(f"   ✅ Added upstream: {upstream_url}")
                else:
                    if verbose:
                        print(f"   ℹ️  Upstream already exists")
            
            success_count += 1
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            error_count += 1
    
    print(f"\n📊 Setup Results:")
    print(f"   ✅ Success: {success_count}")
    print(f"   ❌ Errors: {error_count}")


def sync_all_mirrors(mirrors: List[Dict[str, Any]], dry_run: bool = False, verbose: bool = False):
    """Sync all mirrors with their upstream repositories."""
    print(f"\n🔄 Syncing {len(mirrors)} mirrors with upstream...")
    
    if dry_run:
        print("🔍 Dry run - showing what would be synced:")
        for mirror in mirrors:
            if mirror.get('upstream_url'):
                print(f"  Would sync {mirror['name']} ← {mirror['upstream_url']}")
            else:
                print(f"  ⚠️  Cannot sync {mirror['name']} - no upstream URL")
        return
    
    # Use the simple_sync script for each mirror
    success_count = 0
    error_count = 0
    
    for mirror in mirrors:
        name = mirror['name']
        upstream_url = mirror.get('upstream_url')
        
        if not upstream_url:
            print(f"⚠️  Skipping {name} - no upstream URL")
            continue
        
        try:
            # Extract owner/repo from upstream URL
            if 'github.com' in upstream_url:
                parts = upstream_url.replace('https://github.com/', '').replace('.git', '')
                owner_repo = parts
                
                print(f"🔄 Syncing {name} ← {owner_repo}")
                
                # Use our simple_sync script
                import subprocess
                script_path = Path(__file__).parent / "simple_sync.py"
                
                cmd = ['python', str(script_path), owner_repo]
                if not verbose:
                    cmd.append('--quiet')
                
                result = subprocess.run(cmd, capture_output=not verbose)
                
                if result.returncode == 0:
                    success_count += 1
                    if verbose:
                        print(f"   ✅ Synced successfully")
                else:
                    error_count += 1
                    print(f"   ❌ Sync failed")
            else:
                print(f"   ⚠️  Skipping {name} - non-GitHub upstream")
                
        except Exception as e:
            print(f"   ❌ Error syncing {name}: {e}")
            error_count += 1
    
    print(f"\n📊 Sync Results:")
    print(f"   ✅ Success: {success_count}")
    print(f"   ❌ Errors: {error_count}")


def fix_missing_upstream(mirrors: List[Dict[str, Any]], mirror_manager: GitHubMirrorManager, 
                        dry_run: bool = False, verbose: bool = False):
    """Fix mirrors that are missing upstream URL information."""
    missing_upstream = [m for m in mirrors if not m.get('upstream_url')]
    
    if not missing_upstream:
        print("✅ All mirrors have upstream URLs")
        return
    
    print(f"\n🔧 Fixing {len(missing_upstream)} mirrors missing upstream URLs...")
    
    if dry_run:
        print("🔍 Dry run - showing what would be fixed:")
        for mirror in missing_upstream:
            # Try to infer upstream
            if '_' in mirror['name']:
                owner, repo = mirror['name'].split('_', 1)
                inferred_upstream = f"https://github.com/{owner}/{repo}"
                print(f"  Would fix {mirror['name']} → {inferred_upstream}")
            else:
                print(f"  ⚠️  Cannot infer upstream for {mirror['name']}")
        return
    
    fixed_count = 0
    
    for mirror in missing_upstream:
        name = mirror['name']
        
        # Try to infer upstream from name
        if '_' in name:
            owner, repo = name.split('_', 1)
            inferred_upstream = f"https://github.com/{owner}/{repo}"
            
            print(f"🔧 Fixing {name} → {inferred_upstream}")
            
            try:
                # Update repository description
                repo_data = {
                    "description": f"🪞 Mirror of {owner}/{repo} | Upstream: {inferred_upstream}"
                }
                
                url = f"https://api.github.com/repos/DXT-Mirror/{name}"
                response = mirror_manager.session.patch(url, json=repo_data)
                
                if response.status_code == 200:
                    print(f"   ✅ Updated description with upstream URL")
                    fixed_count += 1
                else:
                    print(f"   ❌ Failed to update: {response.text}")
                    
            except Exception as e:
                print(f"   ❌ Error fixing {name}: {e}")
        else:
            print(f"⚠️  Cannot infer upstream for {name} - unusual naming pattern")
    
    print(f"\n📊 Fix Results:")
    print(f"   ✅ Fixed: {fixed_count}")
    print(f"   ⚠️  Unfixable: {len(missing_upstream) - fixed_count}")


def export_mirrors(mirrors: List[Dict[str, Any]], filename: str, verbose: bool = False):
    """Export mirror data to JSON file."""
    print(f"📤 Exporting {len(mirrors)} mirrors to {filename}...")
    
    # Prepare export data
    export_data = {
        'export_timestamp': json.dumps(datetime.now().isoformat()),
        'total_mirrors': len(mirrors),
        'mirrors_with_upstream': len([m for m in mirrors if m.get('upstream_url')]),
        'mirrors': mirrors
    }
    
    try:
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, sort_keys=True)
        
        print(f"✅ Export completed: {filename}")
        
        if verbose:
            print(f"📊 Export Statistics:")
            print(f"   Total mirrors: {export_data['total_mirrors']}")
            print(f"   With upstream URLs: {export_data['mirrors_with_upstream']}")
            print(f"   Missing upstream: {export_data['total_mirrors'] - export_data['mirrors_with_upstream']}")
        
    except Exception as e:
        print(f"❌ Export failed: {e}")


if __name__ == '__main__':
    from datetime import datetime
    exit(main())