# 🪞 DXT Mirror System - Pure MCP-Mirror Pattern

This document describes the complete pure mirror system implementation.

## 🎯 Design Philosophy

**Pure Mirrors**: Mirror repositories contain **ONLY** upstream content, no modifications whatsoever.

**Traceability**: Upstream URLs are stored in git config and GitHub metadata, not as files in the repository.

**MCP-Mirror Pattern**: Follows the proven pattern used by MCP-Mirror for seamless maintenance.

## 🔧 System Components

### 1. **Mirror Creation & Sync**
- `scripts/create_mirror_repo.py` - Creates GitHub mirror repositories
- `scripts/simple_sync.py` - Syncs individual repositories 
- `scripts/sync_mirrors.py` - Bulk sync operations

### 2. **Upstream Discovery**
- `scripts/get_upstream.py` - Finds upstream URLs from multiple sources
- Git config storage: `mirror.upstream-url`
- GitHub metadata: Repository description and homepage
- Name inference: `DXT-Mirror/owner_repo` → `github.com/owner/repo`

### 3. **Repository Configuration**
- **GitHub Settings**: Issues/PRs/Wiki disabled (redirects to upstream)
- **Description**: `🪞 Mirror of owner/repo | Upstream: URL`
- **Homepage**: Points to upstream repository
- **Topics**: `["dxt-mirror", "claude-desktop", "mirror"]` + upstream topics

## 🚀 Workflows

### **Creating a New Mirror**

```bash
# Step 1: Create GitHub repository
python scripts/create_mirror_repo.py owner/repo

# Step 2: Sync with upstream content
python scripts/simple_sync.py owner/repo
```

### **Maintaining Mirrors**

```bash
# Sync all mirrors
python scripts/sync_mirrors.py --all

# Sync specific mirror
python scripts/simple_sync.py owner/repo

# Check what needs syncing
python scripts/sync_mirrors.py --check
```

### **Working with Mirrors (User Perspective)**

```bash
# Clone pure mirror
git clone git@github.com:DXT-Mirror/owner_repo.git
cd owner_repo

# Auto-setup upstream
python /path/to/scripts/get_upstream.py . --setup

# Manual setup
git remote add upstream https://github.com/owner/repo.git

# Get updates
git fetch upstream
```

## 🔍 Technical Implementation

### **MCP-Mirror Pattern**

1. **Clone Original**: `git clone original_url` (origin → upstream automatically)
2. **Add Mirror Remote**: `git remote add mirror mirror_url` (predictable naming)
3. **Store Metadata**: `git config mirror.upstream-url original_url`
4. **Complete Sync**: `git push --mirror mirror` (all refs, tags, branches)

### **Repository Naming**

- **Original**: `github.com/owner/repo`
- **Mirror**: `github.com/DXT-Mirror/owner_repo` (underscore separator)
- **Predictable**: Always discoverable from original name

### **Upstream Storage Methods**

1. **Git Config** (Primary): `git config mirror.upstream-url`
2. **GitHub Description**: `🪞 Mirror of X | Upstream: URL`
3. **GitHub Homepage**: Points to upstream
4. **Name Inference**: Decode from mirror name

## ✅ Benefits

### **For Users**
- ✅ Pure upstream content (no mirror pollution)
- ✅ Natural Git workflow with `origin` pointing to mirror
- ✅ Easy upstream setup with helper scripts
- ✅ Standard GitHub experience

### **For Maintainers**  
- ✅ Automated upstream discovery
- ✅ Simple sync operations
- ✅ Complete traceability
- ✅ Bulk operations support

### **For the Ecosystem**
- ✅ Perfect mirrors (bit-for-bit copies)
- ✅ No vendor lock-in (standard Git repositories)
- ✅ Discoverable upstream sources
- ✅ Reliable DXT repository access

## 🛡️ Quality Assurance

### **Purity Verification**
```bash
# Mirror should contain ONLY upstream content
git clone https://github.com/DXT-Mirror/owner_repo.git
cd owner_repo

# No mirror-specific files should exist
ls -la | grep -v "^total\|^drwx.*\.\.\?$" # Should show only upstream files

# Upstream URL should be discoverable
python /path/to/scripts/get_upstream.py . # Should return original URL
```

### **Sync Verification**
```bash
# Compare mirror with upstream
git clone https://github.com/DXT-Mirror/owner_repo.git mirror
git clone https://github.com/owner/repo.git upstream

# Compare commit hashes (should be identical)
cd mirror && git log --oneline -5
cd ../upstream && git log --oneline -5

# Compare file contents (should be identical)
diff -r mirror upstream --exclude='.git'
```

## 📋 Best Practices

### **Mirror Creation**
1. Always create repository first with `create_mirror_repo.py`
2. Then sync content with `simple_sync.py`
3. Verify purity with `get_upstream.py`

### **Regular Maintenance**
1. Run bulk sync operations regularly
2. Monitor for upstream changes
3. Handle rate limits gracefully
4. Maintain upstream URL accuracy

### **User Support**
1. Provide clear instructions in mirror descriptions
2. Include upstream links in all metadata
3. Make discovery tools easily accessible
4. Document the MCP-Mirror pattern

---

*This pure mirror system ensures DXT repositories remain accessible while maintaining perfect fidelity to their upstream sources.*