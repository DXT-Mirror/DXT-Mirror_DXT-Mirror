# DXT Mirror Scripts

This directory contains utility scripts for managing DXT repository mirrors using the proven MCP-Mirror pattern.

## 🚀 Quick Start Scripts

### `dxt_workflow.py` - Complete DXT Workflow Automation
**Full automation for discovery, evaluation, and mirroring**

```bash
# Discover up to 50 repos, mirror up to 10 approved ones
python scripts/dxt_workflow.py --max-repos-to-examine 50 --max-repos-to-mirror 10

# Skip discovery, only mirror 5 already-approved repositories
python scripts/dxt_workflow.py --max-repos-to-examine 0 --max-repos-to-mirror 5

# Only examine 100 repos, don't create mirrors
python scripts/dxt_workflow.py --max-repos-to-examine 100 --max-repos-to-mirror 0

# Custom search with specific terms
python scripts/dxt_workflow.py --max-repos-to-examine 20 --max-repos-to-mirror 5 --search-terms "claude dxt,anthropic"

# Dry run to see what would happen
python scripts/dxt_workflow.py --max-repos-to-examine 10 --max-repos-to-mirror 3 --dry-run --verbose

# Use persistent mirror directory
python scripts/dxt_workflow.py --max-repos-to-examine 20 --max-repos-to-mirror 5 --mirror-root /Users/kurt/GitHub/DXT-Mirror
```

**What it does:**
1. **Discovery Phase**: Strategic GitHub search for DXT-related repositories
2. **AI Evaluation**: Uses OpenAI/Anthropic to evaluate repository relevance
3. **Inventory Management**: Tracks repositories and their status in SQLite database
4. **Mirroring Phase**: Creates GitHub mirrors and syncs content
5. **Progress Tracking**: Provides detailed status reports and summaries

**Key Features:**
- ✅ Configurable discovery and mirroring limits
- ✅ AI-powered repository evaluation
- ✅ Zero-value options for selective operation
- ✅ GitHub search result capture in inventory
- ✅ Complete workflow automation
- ✅ Dry-run support for testing

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

# Use persistent mirror directory
python scripts/simple_sync.py owner/repo --mirror-root /Users/kurt/GitHub/DXT-Mirror
```

**What it does:**
1. Clones the original repository (origin → upstream) OR updates existing local copy
2. Adds mirror remote (mirror → DXT-Mirror/owner_repo)  
3. Stores upstream URL in git config (`mirror.upstream-url`)
4. Fetches from origin with prune
5. Pushes to mirror with `--mirror` flag (pure upstream content only)

**With `--mirror-root`:**
- Creates persistent local repositories in specified directory
- Reuses existing clones for efficiency (no re-downloading)
- Perfect for managing multiple repositories in organized structure

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

# Use persistent mirror directory for sync operations
python scripts/discover_mirrors.py --sync --mirror-root /Users/kurt/GitHub/DXT-Mirror
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

## 📁 Mirror Root Directory

All scripts support `--mirror-root PATH` for persistent local repository management:

```bash
# Recommended setup for managing multiple repositories
export DXT_MIRROR_ROOT="/Users/kurt/GitHub/DXT-Mirror"

# All scripts can use this directory
python scripts/simple_sync.py owner/repo --mirror-root $DXT_MIRROR_ROOT
python scripts/dxt_workflow.py --max-repos-to-examine 20 --max-repos-to-mirror 5 --mirror-root $DXT_MIRROR_ROOT
python scripts/discover_mirrors.py --sync --mirror-root $DXT_MIRROR_ROOT
```

**Benefits of Mirror Root:**
- ✅ **Persistent Storage** - Repositories stay on disk between operations
- ✅ **Efficiency** - No re-downloading for subsequent syncs
- ✅ **Organized Structure** - All mirrors in one directory tree
- ✅ **Reusable for Evaluation** - Same repo can be used for AI analysis and mirroring
- ✅ **Easy Management** - Browse, edit, and work with repositories locally

**Directory Structure:**
```
/Users/kurt/GitHub/DXT-Mirror/
├── owner1_repo1/          # Mirror of github.com/owner1/repo1
├── owner2_repo2/          # Mirror of github.com/owner2/repo2
└── anthropic_claude-api/  # Mirror of github.com/anthropic/claude-api
```

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