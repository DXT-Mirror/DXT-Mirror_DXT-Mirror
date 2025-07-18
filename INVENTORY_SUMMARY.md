# DXT Curator Inventory Summary

## 📊 Format & Storage

**Database Type**: SQLite (single file: `dxt_inventory.db`)  
**Schema**: Natural language optimized for AI processing  
**Export Formats**: JSON, CSV, AI-friendly exports  

## 🏗️ Data Structure

### **Core Repository Data**
- **Repository Identity**: `full_name`, `clone_url`, `description`
- **Popularity Metrics**: `stars`, `forks`, `language` 
- **Timestamps**: `discovered_date`, `last_updated`
- **Status Tracking**: Current processing state

### **Natural Language Fields**
- **`notes`**: Human-readable observations
- **`evaluation_notes`**: AI analysis results
- **`decision_reason`**: Why decisions were made
- **`future_actions`**: Next steps in plain English

### **Fork Intelligence**
- **`is_fork`**: Boolean fork detection
- **`parent_repo`**: Parent repository identifier
- **`fork_analysis`**: AI-generated fork assessment

## 🏷️ Repository Status Values

| Status | Description | Usage |
|--------|-------------|-------|
| `discovered` | Newly found | Initial state after discovery |
| `evaluating` | Being analyzed | AI evaluation in progress |
| `mirror` | Approved | Ready for mirroring |
| `reject` | Rejected | Not suitable for mirroring |
| `check_later` | Promising but early | Needs more development time |
| `fork_ignored` | Minimal fork | Fork without significant changes |
| `archived` | Inactive | Repository is archived |

## 🍴 Fork Detection & Analysis

### **Automatic Fork Detection**
- **Size Analysis**: Compares repository size to parent
- **Activity Tracking**: Monitors update frequency vs parent
- **Popularity Assessment**: Evaluates community engagement
- **Language Comparison**: Detects technology stack changes

### **Fork Classification**
- **Minimal Changes**: `fork_ignored` status, parent already covers content
- **Moderate Changes**: Evaluated normally with fork context noted
- **Significant Changes**: Treated as independent repository

### **Example Fork Analysis**
```json
{
  "fork_analysis": "Fork with minimal changes - similar size to parent, no community engagement, less recently updated",
  "parent_repo": "anthropic/claude-tools",
  "status": "fork_ignored"
}
```

## 📝 Sample Data Examples

### **High-Value Repository**
```json
{
  "full_name": "microsoft/vscode-claude-extension",
  "status": "mirror",
  "stars": 342,
  "evaluation_notes": "Excellent VS Code extension with comprehensive Claude integration",
  "decision_reason": "High-quality code, clear DXT relevance, active development",
  "future_actions": "Mirror immediately and feature in showcase",
  "is_fork": false
}
```

### **Early Stage Project**
```json
{
  "full_name": "developer/claude-automation-early",
  "status": "check_later",
  "stars": 3,
  "evaluation_notes": "Interesting concept but minimal implementation",
  "decision_reason": "Promising idea but needs more development before mirroring",
  "future_actions": "Recheck in 3 months for progress",
  "is_fork": false
}
```

### **Fork Without Changes**
```json
{
  "full_name": "user/claude-tools-fork",
  "status": "fork_ignored",
  "stars": 0,
  "notes": "Fork of anthropic/claude-tools with no significant changes",
  "evaluation_notes": "Fork detected. Minimal divergence from parent repository",
  "decision_reason": "No unique contributions - parent already evaluated",
  "future_actions": "Monitor for future changes",
  "is_fork": true,
  "parent_repo": "anthropic/claude-tools",
  "fork_analysis": "Fork with minimal changes - similar size to parent, no community engagement"
}
```

## 📊 Export & Query Options

### **Command Line**
```bash
# View inventory status
dxt-curator status

# Export specific data
dxt-curator export --status mirror --format json
dxt-curator export --format csv

# Search functionality
dxt-curator search "automation"
dxt-curator search "fork of"
```

### **Python API**
```python
from dxt_curator import SimpleInventory

inventory = SimpleInventory()

# Get repositories by status
mirror_ready = inventory.get_repos_by_status('mirror')
forks_ignored = inventory.get_repos_by_status('fork_ignored')

# Search across all fields
automation_repos = inventory.search_repos('automation')
fork_repos = inventory.search_repos('fork of')

# Export for analysis
ai_data = inventory.export_for_ai()
```

## 🎯 Key Benefits

### **AI-Optimized Design**
- Natural language storage for AI processing
- Human-readable decisions and reasoning
- Flexible schema that evolves with use cases

### **Fork Intelligence**
- Automatic detection of repository relationships
- Intelligent analysis of fork significance
- Prevents duplicate evaluation efforts

### **Complete Audit Trail**
- Every decision documented with reasoning
- Full history of repository processing
- Searchable natural language records

### **Flexible Export Options**
- Multiple formats for different use cases
- AI-friendly exports for analysis
- Easy integration with external tools

## 🔄 Workflow Integration

The inventory seamlessly integrates with DXT Curator's AI-powered workflow:

1. **Discovery** → Repositories found via strategic search
2. **Fork Analysis** → Automatic relationship detection
3. **AI Evaluation** → Intelligent assessment with reasoning
4. **Status Assignment** → Appropriate classification
5. **Documentation** → Complete audit trail
6. **Export** → Ready for mirroring or analysis

This approach ensures efficient processing while maintaining complete transparency in all decisions and relationships between repositories.