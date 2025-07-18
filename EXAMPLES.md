# DXT Curator Examples

This document provides practical examples of using DXT Curator for various use cases.

## 🚀 Basic Usage

### Command Line Examples

```bash
# Quick discovery of 10 repositories
dxt-curator discover 10

# Discover repositories with specific criteria
dxt-curator discover 25 --min-stars 5 --days 180

# Check current inventory status
dxt-curator status

# Show repositories ready for mirroring
dxt-curator ready

# Search for specific types of repositories
dxt-curator search "automation"
dxt-curator search "claude api"
dxt-curator search "early development"

# Recheck repositories marked for later
dxt-curator recheck

# Export for analysis
dxt-curator export --output my_analysis.json
```

### Python API Examples

```python
from dxt_curator import SimpleDXTWorkflow, SimpleInventory

# Basic workflow
workflow = SimpleDXTWorkflow(ai_provider="openai")
results = workflow.discover_and_evaluate(limit=20)

# Custom discovery with filters
results = workflow.discover_and_evaluate(
    limit=50,
    filters={'min_stars': 3, 'days': 90}
)

# Working with inventory
inventory = SimpleInventory()
mirror_ready = inventory.get_repos_by_status('mirror')
for repo in mirror_ready:
    print(f"{repo.full_name}: {repo.evaluation_notes}")
```

## 🔍 Advanced Discovery

### Custom Search Strategies

```python
from dxt_curator.core import StrategicGitHubSearch

# Initialize with custom settings
searcher = StrategicGitHubSearch(github_token="your_token")

# Discover repositories
results = searcher.discover_dxt_repositories()

# Apply custom filters
recent_results = searcher.filter_by_recency(results, days=30)
popular_results = searcher.filter_by_activity(results, min_stars=10)

# Custom ranking
ranked_results = searcher.rank_by_relevance(results)

# Export for further processing
searcher.export_results(ranked_results, "custom_discovery.json")
```

### Targeted Discovery

```python
# Focus on specific types of repositories
high_quality_repos = [r for r in results if r.stars > 20 and r.language == 'Python']

# Filter by topics
ai_repos = [r for r in results if 'ai' in r.topics or 'claude' in r.topics]

# Filter by size (avoid empty repos)
substantial_repos = [r for r in results if r.size > 100]
```

## 🤖 AI Evaluation Examples

### Basic Evaluation

```python
from dxt_curator.core import AIEvaluator

# Initialize evaluator
evaluator = AIEvaluator(api_provider="anthropic")

# Evaluate a single repository
repo_data = {
    'full_name': 'user/claude-tool',
    'clone_url': 'https://github.com/user/claude-tool.git',
    'description': 'A tool for Claude automation',
    'stars': 15,
    'language': 'Python'
}

decision = evaluator.evaluate_repo(repo_data)
print(f"Decision: {decision['decision']}")
print(f"Reason: {decision['reason']}")
```

### Batch Evaluation

```python
# Process multiple repositories from discovery
with open('discovered_repos.json', 'r') as f:
    repos = json.load(f)

results = evaluator.process_discovered_repos('discovered_repos.json')

print(f"Mirror: {len(results['mirror'])}")
print(f"Reject: {len(results['reject'])}")
print(f"Check Later: {len(results['check_later'])}")
```

### Recheck Later Repositories

```python
# Check for repositories due for review
results = evaluator.recheck_repos()

print(f"Rechecked {results['rechecked']} repositories")
for status, repos in results['results'].items():
    print(f"{status}: {len(repos)} repositories")
```

## 📊 Inventory Management

### Working with Natural Language Data

```python
from dxt_curator import SimpleInventory

inventory = SimpleInventory()

# Add a repository with custom notes
repo_data = {
    'full_name': 'example/claude-helper',
    'clone_url': 'https://github.com/example/claude-helper.git',
    'description': 'Helper utilities for Claude',
    'stars': 8,
    'language': 'JavaScript'
}

inventory.add_repo(repo_data, "Found through manual search - looks promising")

# Update with AI evaluation results
inventory.update_repo(
    'example/claude-helper',
    status='mirror',
    evaluation_notes='High-quality JavaScript utilities with good documentation',
    decision_reason='Provides valuable Claude integration helpers',
    future_actions='Mirror immediately and consider for featured collection'
)
```

### Advanced Searching

```python
# Search across all natural language fields
automation_repos = inventory.search_repos('automation')
early_dev_repos = inventory.search_repos('early development')
python_repos = inventory.search_repos('python')

# Get repositories by specific status
ready_to_mirror = inventory.get_repos_by_status('mirror')
need_review = inventory.get_repos_by_status('check_later')
rejected = inventory.get_repos_by_status('reject')

# Export for AI analysis
ai_data = inventory.export_for_ai()
with open('ai_analysis.json', 'w') as f:
    json.dump(ai_data, f, indent=2)
```

## 🔄 Workflow Automation

### Scheduled Discovery

```python
import schedule
import time

def daily_discovery():
    """Run daily discovery of new repositories."""
    workflow = SimpleDXTWorkflow()
    
    # Focus on recently updated repositories
    results = workflow.discover_and_evaluate(
        limit=30,
        filters={'days': 7, 'min_stars': 1}
    )
    
    print(f"Daily discovery found {results['total_discovered']} repositories")

# Schedule daily discovery
schedule.every().day.at("09:00").do(daily_discovery)

# Run scheduler
while True:
    schedule.run_pending()
    time.sleep(3600)  # Check every hour
```

### Weekly Recheck

```python
def weekly_recheck():
    """Weekly recheck of repositories marked for later."""
    workflow = SimpleDXTWorkflow()
    results = workflow.recheck_later_repos()
    
    print(f"Weekly recheck processed {results['rechecked']} repositories")

schedule.every().monday.at("10:00").do(weekly_recheck)
```

## 📈 Analytics and Reporting

### Repository Analysis

```python
from dxt_curator import SimpleInventory
from collections import Counter

inventory = SimpleInventory()
all_repos = inventory.get_all_repos()

# Language distribution
languages = Counter(repo.language for repo in all_repos if repo.language)
print("Top languages:", languages.most_common(5))

# Status distribution
statuses = Counter(repo.status for repo in all_repos)
print("Status distribution:", dict(statuses))

# Popular repositories
popular = sorted(all_repos, key=lambda r: r.stars, reverse=True)[:10]
print("Most popular repositories:")
for repo in popular:
    print(f"  {repo.full_name} ({repo.stars} stars)")
```

### AI Decision Analysis

```python
# Analyze AI decision patterns
mirror_repos = inventory.get_repos_by_status('mirror')
reject_repos = inventory.get_repos_by_status('reject')

print("Mirror decisions analysis:")
for repo in mirror_repos[:5]:
    print(f"  {repo.full_name}: {repo.evaluation_notes}")

print("\nRejection reasons analysis:")
for repo in reject_repos[:5]:
    print(f"  {repo.full_name}: {repo.evaluation_notes}")
```

## 🔧 Custom Workflows

### High-Quality Repository Focus

```python
def find_high_quality_repos():
    """Focus on high-quality repositories only."""
    workflow = SimpleDXTWorkflow()
    
    # Use strict filters
    results = workflow.discover_and_evaluate(
        limit=100,
        filters={
            'min_stars': 10,
            'days': 180
        }
    )
    
    # Additional filtering
    inventory = SimpleInventory()
    mirror_ready = inventory.get_repos_by_status('mirror')
    
    # Filter for substantial repositories
    substantial = [r for r in mirror_ready if r.stars > 20]
    
    return substantial
```

### Early Stage Project Monitoring

```python
def monitor_early_projects():
    """Monitor early-stage projects for development progress."""
    inventory = SimpleInventory()
    check_later = inventory.get_repos_by_status('check_later')
    
    # Recheck projects that were too early
    evaluator = AIEvaluator()
    
    progress_made = []
    for repo in check_later:
        if "early development" in repo.evaluation_notes.lower():
            # Recheck this repository
            repo_data = repo.metadata
            decision = evaluator.evaluate_repo(repo_data)
            
            if decision['decision'] == 'mirror':
                progress_made.append(repo.full_name)
    
    return progress_made
```

## 🎯 Integration Examples

### Mirror Setup Integration

```python
def setup_mirrors():
    """Set up actual mirrors for approved repositories."""
    inventory = SimpleInventory()
    mirror_ready = inventory.get_repos_by_status('mirror')
    
    for repo in mirror_ready:
        print(f"Setting up mirror for {repo.full_name}")
        print(f"  Clone URL: {repo.clone_url}")
        print(f"  Reason: {repo.evaluation_notes}")
        print(f"  Actions: {repo.future_actions}")
        
        # Here you would integrate with your actual mirroring system
        # setup_git_mirror(repo.clone_url, f"DXT-Mirror/{repo.full_name}")
```

### Notification Integration

```python
def send_notifications():
    """Send notifications for new discoveries."""
    inventory = SimpleInventory()
    
    # Get recently discovered repositories
    from datetime import datetime, timedelta
    recent = datetime.now() - timedelta(days=1)
    
    all_repos = inventory.get_all_repos()
    new_repos = [r for r in all_repos if r.discovered_date > recent.isoformat()]
    
    if new_repos:
        print(f"Found {len(new_repos)} new repositories:")
        for repo in new_repos:
            print(f"  {repo.full_name} - {repo.status}")
            # send_slack_notification(repo) or send_email(repo)
```

## 🧪 Testing and Validation

### Validation Workflow

```python
def validate_decisions():
    """Validate AI decisions for quality assurance."""
    inventory = SimpleInventory()
    mirror_repos = inventory.get_repos_by_status('mirror')
    
    # Check for potential issues
    issues = []
    
    for repo in mirror_repos:
        # Check for empty repositories
        if repo.stars == 0 and not repo.evaluation_notes:
            issues.append(f"{repo.full_name}: Low confidence decision")
        
        # Check for archived repositories
        if 'archived' in repo.evaluation_notes.lower():
            issues.append(f"{repo.full_name}: May be archived")
    
    return issues
```

### Quality Metrics

```python
def calculate_quality_metrics():
    """Calculate quality metrics for the curation process."""
    inventory = SimpleInventory()
    summary = inventory.get_summary()
    
    total = summary['total_repos']
    mirror_count = summary['by_status'].get('mirror', 0)
    reject_count = summary['by_status'].get('reject', 0)
    
    if total > 0:
        precision = mirror_count / total
        efficiency = (mirror_count + reject_count) / total
        
        return {
            'total_evaluated': total,
            'precision': precision,
            'efficiency': efficiency,
            'mirror_rate': mirror_count / total if total > 0 else 0
        }
```

These examples demonstrate the flexibility and power of DXT Curator's natural language approach to repository curation. The system adapts to your specific needs while maintaining transparency and explainability in all decisions.