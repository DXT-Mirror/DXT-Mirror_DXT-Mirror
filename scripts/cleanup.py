#!/usr/bin/env python3
"""
Cleanup script for DXT Curator.

This script cleans up temporary files, logs, and cached data.
"""

import os
import shutil
import sys
from pathlib import Path


def clean_build_artifacts():
    """Clean build artifacts."""
    print("🧹 Cleaning build artifacts...")
    
    patterns = [
        "build/",
        "dist/",
        "*.egg-info/",
        ".pytest_cache/",
        "htmlcov/",
        ".coverage",
        "__pycache__/",
        "*.pyc",
        ".mypy_cache/",
        ".tox/"
    ]
    
    removed = 0
    for pattern in patterns:
        if pattern.endswith('/'):
            # Directory pattern
            for path in Path('.').rglob(pattern.rstrip('/')):
                if path.is_dir():
                    shutil.rmtree(path)
                    print(f"  Removed directory: {path}")
                    removed += 1
        else:
            # File pattern
            for path in Path('.').rglob(pattern):
                if path.is_file():
                    path.unlink()
                    print(f"  Removed file: {path}")
                    removed += 1
    
    print(f"✅ Removed {removed} build artifacts")
    return removed


def clean_temp_files():
    """Clean temporary files."""
    print("🗂️  Cleaning temporary files...")
    
    temp_files = [
        "temp_clones/",
        "dxt_curator.log*",
        "security.log*",
        "debug.log*",
        "*.tmp",
        "*.temp",
        ".DS_Store"
    ]
    
    removed = 0
    for pattern in temp_files:
        if pattern.endswith('/'):
            # Directory
            path = Path(pattern.rstrip('/'))
            if path.exists():
                shutil.rmtree(path)
                print(f"  Removed directory: {path}")
                removed += 1
        else:
            # File pattern
            for path in Path('.').glob(pattern):
                if path.is_file():
                    path.unlink()
                    print(f"  Removed file: {path}")
                    removed += 1
    
    print(f"✅ Removed {removed} temporary files")
    return removed


def clean_cache_files():
    """Clean cache files."""
    print("📦 Cleaning cache files...")
    
    cache_files = [
        "discovered_repos.json",
        "evaluation_results.json",
        "inventory_export.json",
        "debug_export.json",
        "*.json.demo",
        "*.json.test",
        "*.json.backup"
    ]
    
    removed = 0
    for pattern in cache_files:
        for path in Path('.').glob(pattern):
            if path.is_file():
                path.unlink()
                print(f"  Removed cache file: {path}")
                removed += 1
    
    print(f"✅ Removed {removed} cache files")
    return removed


def clean_database_temp():
    """Clean database temporary files."""
    print("🗄️  Cleaning database temporary files...")
    
    db_temp_files = [
        "dxt_inventory.db-wal",
        "dxt_inventory.db-shm",
        "dxt_inventory.db-journal"
    ]
    
    removed = 0
    for filename in db_temp_files:
        path = Path(filename)
        if path.exists():
            path.unlink()
            print(f"  Removed database temp file: {path}")
            removed += 1
    
    print(f"✅ Removed {removed} database temporary files")
    return removed


def show_disk_usage():
    """Show disk usage information."""
    print("💾 Disk usage:")
    
    try:
        import shutil
        total, used, free = shutil.disk_usage('.')
        print(f"  Total: {total // (1024**3):.1f} GB")
        print(f"  Used: {used // (1024**3):.1f} GB")
        print(f"  Free: {free // (1024**3):.1f} GB")
        
        # Show directory sizes
        for item in ['.', 'dxt_curator', 'temp_clones', '__pycache__']:
            path = Path(item)
            if path.exists():
                if path.is_dir():
                    size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
                    print(f"  {item}: {size // (1024**2):.1f} MB")
                else:
                    size = path.stat().st_size
                    print(f"  {item}: {size // (1024**2):.1f} MB")
    except Exception as e:
        print(f"  Could not calculate disk usage: {e}")


def main():
    """Main cleanup function."""
    print("🧽 DXT Curator Cleanup")
    print("=" * 30)
    
    # Check if we're in the right directory
    if not Path('dxt_curator').exists():
        print("❌ Not in DXT Curator directory")
        return False
    
    # Show initial disk usage
    show_disk_usage()
    print()
    
    # Confirm cleanup
    response = input("🤔 Proceed with cleanup? (y/N): ").lower()
    if response not in ['y', 'yes']:
        print("❌ Cleanup cancelled")
        return False
    
    print()
    
    # Run cleanup functions
    total_removed = 0
    total_removed += clean_build_artifacts()
    total_removed += clean_temp_files()
    total_removed += clean_cache_files()
    total_removed += clean_database_temp()
    
    print()
    print(f"🎉 Cleanup complete! Removed {total_removed} items")
    
    # Show final disk usage
    show_disk_usage()
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)