# DXT Mirror Scripts

This directory contains utility scripts for managing DXT repository mirrors using the proven MCP-Mirror pattern.

## 🚀 Quick Start Scripts

### `simple_sync.py` - Standalone Repository Sync
**Recommended for most users**

```bash
# Sync any repository with its mirror
python scripts/simple_sync.py owner/repo

# Example
python scripts/simple_sync.py milisp/awesome-claude-dxt

# With verbose output
python scripts/simple_sync.py owner/repo --verbose

# Dry run (see what would happen)
python scripts/simple_sync.py owner/repo --dry-run
```

**What it does:**
1. Clones the original repository (origin → upstream)
2. Adds mirror remote (mirror → DXT-Mirror/owner_repo)  
3. Stores upstream URL in git config (`mirror.upstream-url`)
4. Fetches from origin with prune
5. Pushes to mirror with `--mirror` flag (pure upstream content only)

### `create_mirror_repo.py` - Create Mirror Repository
**For creating GitHub repositories manually**

```bash
# Create mirror repository in DXT-Mirror organization
python scripts/create_mirror_repo.py owner/repo

# Example
python scripts/create_mirror_repo.py milisp/awesome-claude-dxt

# Dry run
python scripts/create_mirror_repo.py owner/repo --dry-run
```

### `get_upstream.py` - Find and Setup Upstream Remote
**For working with pure mirrors**

```bash
# Get upstream URL from current directory
python scripts/get_upstream.py

# Get upstream URL from local mirror
python scripts/get_upstream.py /path/to/mirror

# Get upstream URL from remote mirror
python scripts/get_upstream.py DXT-Mirror/owner_repo

# Auto-setup upstream remote
python scripts/get_upstream.py . --setup

# With verbose output
python scripts/get_upstream.py . --setup --verbose
```

### `discover_mirrors.py` - Bulk Mirror Management
**For managing all mirrors in the organization**

```bash
# List all mirrors with upstream URLs
python scripts/discover_mirrors.py --list

# Fix mirrors missing upstream URLs
python scripts/discover_mirrors.py --fix

# Sync all mirrors with upstream
python scripts/discover_mirrors.py --sync

# Export mirror data to JSON
python scripts/discover_mirrors.py --export mirrors.json

# Filter mirrors containing specific term
python scripts/discover_mirrors.py --list --filter claude

# Dry run (see what would be done)
python scripts/discover_mirrors.py --sync --dry-run
```

## 🔧 Advanced Scripts

### `sync_mirrors.py` - Inventory-Based Sync
**For managing multiple repositories with inventory tracking**

```bash
# Show current status
python scripts/sync_mirrors.py --status

# Check which repos need syncing
python scripts/sync_mirrors.py --check

# Sync all mirrored repositories
python scripts/sync_mirrors.py --all

# Sync specific repository
python scripts/sync_mirrors.py --repo owner/repo

# Sync with limits
python scripts/sync_mirrors.py --all --limit 5

# Dry run
python scripts/sync_mirrors.py --all --dry-run
```

## 🔄 MCP-Mirror Pattern

All scripts follow the proven MCP-Mirror pattern:

### For Mirror Maintainers:
```bash
# 1. Clone original
git clone https://github.com/original/repo.git
cd repo

# 2. Add mirror remote  
git remote add mirror https://github.com/DXT-Mirror/original_repo.git

# 3. Sync
git fetch -p origin
git push --mirror mirror
```

### For End Users:
```bash
# Clone the mirror normally
git clone https://github.com/DXT-Mirror/original_repo.git
cd original_repo

# Add upstream for updates
git remote add upstream https://github.com/original/repo.git

# Check remotes
git remote -v
# origin    https://github.com/DXT-Mirror/original_repo.git (fetch)
# origin    https://github.com/DXT-Mirror/original_repo.git (push)  
# upstream  https://github.com/original/repo.git (fetch)
# upstream  https://github.com/original/repo.git (push)
```

## 📋 Other Scripts

- `cleanup.py` - Clean up temporary files and old data
- `quick_start.py` - Set up development environment
- `test_setup.py` - Test environment configuration

## 🔑 Environment Variables

Set these environment variables for the scripts to work:

```bash
export GITHUB_MIRROR_TOKEN="your_github_token_here"
# OR
export GITHUB_TOKEN="your_github_token_here"

# For AI evaluation (optional)
export OPENAI_API_KEY="your_openai_key_here"
# OR  
export ANTHROPIC_API_KEY="your_anthropic_key_here"
```

## 💡 Usage Examples

### Daily Sync Workflow
```bash
# Check what needs syncing
python scripts/sync_mirrors.py --check

# Sync all repositories
python scripts/sync_mirrors.py --all --verbose

# Or sync specific ones
python scripts/simple_sync.py owner/repo1
python scripts/simple_sync.py owner/repo2
```

### Adding New Repository
```bash
# Option 1: Let simple_sync create and sync
python scripts/simple_sync.py new-owner/new-repo

# Option 2: Create first, then sync
python scripts/create_mirror_repo.py new-owner/new-repo
python scripts/simple_sync.py new-owner/new-repo
```

### Repository Naming
- **Original**: `github.com/owner/repo`
- **Mirror**: `github.com/DXT-Mirror/owner_repo` (underscore separator)

## 🛟 Troubleshooting

### Common Issues

1. **"Repository not found"**
   - Check if you have access to the original repository
   - Verify your GitHub token has the right permissions

2. **"Mirror already exists"**
   - Use `simple_sync.py` to sync existing mirrors
   - The create script will skip if mirror exists

3. **"Permission denied"**
   - Check your GitHub token
   - Ensure you have write access to DXT-Mirror organization

4. **"Git operation failed"**
   - Check internet connection
   - Verify repository URLs are correct
   - Try with `--verbose` for more details

### Getting Help
```bash
python scripts/script_name.py --help
```