# DXT Curator Inventory Format

## 📊 Overview

DXT Curator uses a **SQLite database** with a natural language approach to store repository information. This design prioritizes AI-readability and human understanding over rigid database schemas.

## 🗄️ Database Structure

### **Primary Table: `repos`**

The inventory uses a single table approach for simplicity and AI-friendliness:

```sql
CREATE TABLE repos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT UNIQUE NOT NULL,       -- GitHub repo identifier (owner/repo)
    clone_url TEXT NOT NULL,              -- URL for cloning
    description TEXT,                     -- Repository description
    stars INTEGER,                        -- Star count for popularity
    language TEXT,                        -- Primary programming language
    discovered_date TEXT NOT NULL,        -- When we found this repo
    status TEXT NOT NULL,                 -- Current processing status
    notes TEXT,                           -- Human-readable notes
    evaluation_notes TEXT,                -- AI evaluation results
    decision_reason TEXT,                 -- Why we made this decision
    future_actions TEXT,                  -- What to do next
    last_updated TEXT,                    -- Last modification time
    metadata TEXT                         -- JSON blob for extra data
);
```

### **Indexes**
- `idx_status` - For querying by status
- `idx_full_name` - For repository lookups
- `idx_discovered_date` - For time-based queries

## 📋 Data Fields Explained

### **Core Repository Information**
- **`full_name`** - GitHub repository identifier (e.g., "microsoft/vscode")
- **`clone_url`** - HTTPS URL for cloning the repository
- **`description`** - Original repository description from GitHub
- **`stars`** - Star count (used for popularity ranking)
- **`language`** - Primary programming language

### **Tracking Information**
- **`discovered_date`** - ISO timestamp when we first found this repository
- **`last_updated`** - ISO timestamp when entry was last modified
- **`status`** - Current processing status (see Status Values below)

### **Natural Language Fields**
- **`notes`** - Human-readable notes about the repository
- **`evaluation_notes`** - AI evaluation results and reasoning
- **`decision_reason`** - Why we made the current decision
- **`future_actions`** - What should be done next (in natural language)

### **Metadata**
- **`metadata`** - JSON blob containing original GitHub API data plus extended information

## 🏷️ Status Values

The inventory uses these status values to track repository processing:

| Status | Description | Example Use |
|--------|-------------|-------------|
| `discovered` | Newly found repository | Just discovered via GitHub search |
| `evaluating` | Currently being evaluated by AI | AI evaluation in progress |
| `mirror` | Approved for mirroring | High-quality, DXT-relevant repository |
| `reject` | Rejected for mirroring | Not DXT-related or low quality |
| `check_later` | Promising but needs more development | Early-stage project worth revisiting |
| `fork_ignored` | Fork without significant changes | Fork of existing repo, no new content |
| `archived` | Repository is archived/inactive | No longer maintained |
| `private` | Repository became private | Cannot access for evaluation |

## 📝 Sample Inventory Entry

```json
{
  "id": 1,
  "full_name": "microsoft/vscode-claude-extension",
  "clone_url": "https://github.com/microsoft/vscode-claude-extension.git",
  "description": "VS Code extension for Claude AI integration",
  "stars": 342,
  "language": "TypeScript",
  "discovered_date": "2024-01-15T10:30:00Z",
  "status": "mirror",
  "notes": "Found through strategic search for 'claude vscode extension'",
  "evaluation_notes": "High-quality VS Code extension with comprehensive Claude integration. Well-documented, actively maintained, and provides real value to developers.",
  "decision_reason": "Excellent code quality, clear DXT relevance, active development, and strong community engagement",
  "future_actions": "Mirror immediately and consider featuring in DXT showcase",
  "last_updated": "2024-01-15T10:35:00Z",
  "metadata": {
    "original_github_data": {
      "id": 123456789,
      "node_id": "MDEwOlJlcG9zaXRvcnkxMjM0NTY3ODk=",
      "owner": {
        "login": "microsoft",
        "id": 6154722,
        "type": "Organization"
      },
      "html_url": "https://github.com/microsoft/vscode-claude-extension",
      "created_at": "2023-06-15T14:20:00Z",
      "updated_at": "2024-01-14T09:15:00Z",
      "pushed_at": "2024-01-14T09:15:00Z",
      "size": 2048,
      "open_issues_count": 5,
      "topics": ["claude", "vscode", "ai", "extension"],
      "license": {
        "key": "mit",
        "name": "MIT License"
      }
    },
    "fork_info": {
      "is_fork": false,
      "parent_repo": null,
      "fork_analysis": "Original repository, not a fork"
    },
    "evaluation_metadata": {
      "evaluation_date": "2024-01-15T10:35:00Z",
      "ai_provider": "openai",
      "security_warnings": [],
      "confidence_score": 0.95
    }
  }
}
```

## 🍴 Fork Detection and Handling

The system includes sophisticated fork detection to avoid duplicating effort:

### **Fork Detection Process**
1. **GitHub API Analysis** - Check `fork` field and `parent` information
2. **Commit Analysis** - Compare commit histories between fork and parent
3. **Content Comparison** - Analyze unique contributions in the fork
4. **Activity Assessment** - Check if fork has independent development

### **Fork Handling Logic**
```python
def analyze_fork(repo_data):
    """Analyze fork to determine if it adds value."""
    if not repo_data.get('fork'):
        return "not_fork"
    
    parent_repo = repo_data.get('parent', {}).get('full_name')
    
    # Check for significant divergence
    if repo_data.get('size', 0) > repo_data.get('parent', {}).get('size', 0) * 1.5:
        return "significant_changes"
    
    # Check for recent activity
    if repo_data.get('pushed_at') > repo_data.get('parent', {}).get('pushed_at'):
        return "more_recent_activity"
    
    # Check for unique stars/engagement
    if repo_data.get('stargazers_count', 0) > 10:
        return "community_engagement"
    
    return "minimal_changes"
```

### **Fork Status Examples**

#### **Fork with Minimal Changes**
```json
{
  "full_name": "user123/claude-tools-fork",
  "status": "fork_ignored",
  "notes": "Fork of anthropic/claude-tools with no significant changes",
  "evaluation_notes": "Fork detected. Parent repository: anthropic/claude-tools. Analysis shows minimal divergence with no unique contributions.",
  "decision_reason": "Fork without substantial modifications - parent repository already evaluated",
  "future_actions": "Monitor for significant changes in future scans",
  "metadata": {
    "fork_info": {
      "is_fork": true,
      "parent_repo": "anthropic/claude-tools",
      "fork_analysis": "Minimal changes detected",
      "commit_difference": 2,
      "size_difference": 0.1,
      "last_unique_commit": "2024-01-10T15:30:00Z"
    }
  }
}
```

#### **Fork with Significant Changes**
```json
{
  "full_name": "developer/claude-tools-enhanced",
  "status": "mirror",
  "notes": "Fork of anthropic/claude-tools with significant enhancements",
  "evaluation_notes": "Fork with substantial improvements including new features, better documentation, and additional integrations. Adds genuine value beyond parent repository.",
  "decision_reason": "Fork contains significant unique contributions that justify separate evaluation",
  "future_actions": "Mirror as independent repository due to substantial enhancements",
  "metadata": {
    "fork_info": {
      "is_fork": true,
      "parent_repo": "anthropic/claude-tools",
      "fork_analysis": "Significant enhancements detected",
      "commit_difference": 45,
      "size_difference": 2.3,
      "unique_features": ["new API endpoints", "enhanced documentation", "docker support"]
    }
  }
}
```

## 📤 Export Formats

The inventory can be exported in multiple formats:

### **1. AI-Friendly JSON Export**
```bash
dxt-curator export --format ai
```
Optimized for AI processing with natural language fields.

### **2. CSV Export**
```bash
dxt-curator export --format csv
```
Spreadsheet-compatible format for analysis.

### **3. GitHub Issues Export**
```bash
dxt-curator export --format github
```
Format suitable for creating GitHub issues for manual review.

### **4. Mirror List Export**
```bash
dxt-curator export --format mirror
```
Simple list of repositories ready for mirroring.

## 🔍 Querying the Inventory

### **Command Line Interface**
```bash
# Show all repositories
dxt-curator status

# Show repositories by status
dxt-curator ready                    # status = 'mirror'
dxt-curator status --status rejected # status = 'reject'

# Search natural language fields
dxt-curator search "automation"      # Full-text search
dxt-curator search "early development" # Find repos needing more time

# Export specific data
dxt-curator export --status mirror  # Only approved repos
```

### **Python API**
```python
from dxt_curator import SimpleInventory

inventory = SimpleInventory()

# Get all repositories
all_repos = inventory.get_all_repos()

# Get by status
mirror_ready = inventory.get_repos_by_status('mirror')
check_later = inventory.get_repos_by_status('check_later')

# Search natural language fields
automation_repos = inventory.search_repos('automation')
python_repos = inventory.search_repos('python')

# Get summary statistics
summary = inventory.get_summary()
print(f"Total repos: {summary['total_repos']}")
print(f"Ready to mirror: {summary['by_status'].get('mirror', 0)}")
```

## 💾 Database File Location

By default, the inventory is stored in:
- **File**: `dxt_inventory.db`
- **Location**: Current working directory
- **Format**: SQLite database

You can specify a different location:
```python
inventory = SimpleInventory(db_path="/path/to/my/inventory.db")
```

## 🔄 Backup and Migration

### **Backup**
```bash
# Simple file copy
cp dxt_inventory.db dxt_inventory.db.backup

# Or export to JSON
dxt-curator export --output full_backup.json
```

### **Migration**
```python
from dxt_curator import SimpleInventory
import json

# Export from old system
old_inventory = SimpleInventory("old_inventory.db")
data = old_inventory.export_for_ai()

# Import to new system
new_inventory = SimpleInventory("new_inventory.db")
for repo_data in data:
    new_inventory.add_repo(repo_data)
```

## 🎯 Design Philosophy

The inventory format reflects DXT Curator's AI-first philosophy:

1. **Natural Language First** - All reasoning and decisions stored in human-readable format
2. **AI-Friendly** - Structure optimized for AI processing and understanding
3. **Flexible Schema** - Can evolve without breaking existing data
4. **Complete Audit Trail** - Every decision recorded with full context
5. **Fork-Aware** - Intelligent handling of repository relationships

This approach makes the system both powerful and maintainable, with full transparency in all decisions and processes.