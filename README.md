# DXT Curator: AI-Powered Repository Discovery and Curation

> **Paradigm Shift**: From rigid rule-based systems to natural language AI curation

DXT Curator is a revolutionary approach to repository discovery and curation that leverages AI's natural language processing capabilities instead of fighting them with rigid structures. Built specifically for discovering and curating DXT (Claude Desktop Extension) repositories, it represents a fundamental shift from traditional automation to AI-powered intelligence.

## 🧠 Philosophy: Why This Approach Works

### The Problem with Traditional Approaches

Traditional repository curation systems rely on:
- **Rigid schemas** that break when requirements change
- **Complex rule engines** that can't handle edge cases
- **Brittle pattern matching** that misses context
- **Manual configuration** for every new scenario

### The AI-First Solution

DXT Curator uses AI the way it's meant to be used:
- **Natural language storage** that AI can understand and process
- **Context-aware decisions** that consider nuance and intent
- **Human-readable reasoning** that explains every decision
- **Flexible adaptation** to new requirements without code changes

## 🚀 Key Features

### 🔍 **Strategic Discovery**
- Targeted GitHub search with DXT-specific queries
- Quality filtering to eliminate noise
- Relevance ranking based on multiple indicators
- Respectful rate limiting and API optimization

### 🤖 **AI-Powered Evaluation**
- Reads repositories like humans do (README, code, structure)
- Makes intelligent decisions with natural language reasoning
- Supports both OpenAI and Anthropic APIs
- Handles edge cases and context automatically

### 📝 **Natural Language Inventory**
- Stores all decisions and reasoning in human-readable format
- Enables powerful text-based searching and analysis
- Maintains complete audit trails
- Adapts to new information without schema changes

### 🔄 **Intelligent Workflow**
- Complete pipeline from discovery to decision
- Automatic handling of "check later" scenarios
- Batch processing with progress tracking
- Export capabilities for further AI analysis

## 🛠️ Installation

```bash
pip install dxt-curator
```

### Development Installation

```bash
git clone https://github.com/DXT-Mirror/dxt-curator.git
cd dxt-curator
pip install -e ".[dev]"
```

## ⚙️ Configuration

### Environment Variables

```bash
# Required: GitHub API token for discovery
export GITHUB_TOKEN="your_github_token_here"

# Required: AI API key (choose one)
export OPENAI_API_KEY="your_openai_key_here"
# OR
export ANTHROPIC_API_KEY="your_anthropic_key_here"
```

### Optional Configuration

Create `dxt_curator_config.json` for custom settings:

```json
{
  "ai": {
    "provider": "openai",
    "max_tokens": 1000,
    "temperature": 0.1
  },
  "github": {
    "rate_limit_delay": 1.0,
    "max_search_results": 100
  },
  "workflow": {
    "default_discovery_limit": 50,
    "clone_timeout": 60
  }
}
```

## 📚 Quick Start

### Command Line Interface

```bash
# Discover and evaluate 25 repositories
dxt-curator discover 25

# Show current inventory status
dxt-curator status

# Show repositories ready to mirror
dxt-curator ready

# Search through inventory
dxt-curator search "claude automation"

# Recheck repositories marked for later
dxt-curator recheck

# Export inventory for AI analysis
dxt-curator export
```

### Python API

```python
from dxt_curator import SimpleDXTWorkflow

# Initialize workflow
workflow = SimpleDXTWorkflow(ai_provider="openai")

# Discover and evaluate repositories
results = workflow.discover_and_evaluate(limit=25)

# Show repositories ready to mirror
workflow.show_ready_to_mirror()

# Search inventory
workflow.search_inventory("claude automation")
```

## 🔬 How It Works

### 1. Strategic Discovery

The system uses carefully crafted search queries to find DXT-related repositories:

```python
# High-priority searches
"claude desktop extension"
"claude mcp server" 
"claude computer use"

# Medium-priority searches
"anthropic claude tool"
"claude automation workflow"
"claude api integration"
```

Each query is designed to maximize precision while minimizing noise.

### 2. AI-Powered Evaluation

For each repository, the AI:

1. **Clones** the repository (shallow clone for efficiency)
2. **Reads** key files (README, config files, file structure)
3. **Analyzes** content using natural language processing
4. **Decides** on one of three actions:
   - **Mirror**: Ready for immediate mirroring
   - **Reject**: Not DXT-related or problematic
   - **Check Later**: Promising but needs more development

### 3. Natural Language Storage

All decisions are stored in human-readable format:

```json
{
  "repo_name": "owner/claude-automation-tool",
  "status": "mirror",
  "evaluation_notes": "Excellent Claude automation tool with comprehensive documentation and active development",
  "decision_reason": "Repository provides valuable Claude Desktop integration with well-structured code",
  "future_actions": "Mirror immediately - high-value addition to DXT ecosystem",
  "notes": "Popular repository with good community engagement"
}
```

## 🎯 Use Cases

### Repository Curation
- **Discover** new DXT-related repositories automatically
- **Evaluate** repositories using human-like intelligence
- **Track** all decisions with complete audit trails
- **Organize** repositories by relevance and quality

### Community Building
- **Identify** emerging DXT projects early
- **Connect** with active developers and maintainers
- **Monitor** ecosystem growth and trends
- **Curate** high-quality resource collections

### Development Intelligence
- **Analyze** patterns in DXT development
- **Identify** gaps in the ecosystem
- **Track** technology adoption trends
- **Inform** strategic development decisions

## 🏗️ Architecture

### Core Components

```
dxt_curator/
├── core/
│   ├── discovery.py      # Strategic GitHub search
│   ├── evaluator.py      # AI-powered evaluation
│   ├── inventory.py      # Natural language storage
│   └── workflow.py       # Orchestration
├── cli/
│   └── main.py          # Command-line interface
└── utils/
    ├── config.py        # Configuration management
    └── logging.py       # Logging utilities
```

### Data Flow

```
GitHub API → Strategic Search → Quality Filtering → AI Evaluation → Natural Language Storage
```

### Decision Matrix

| Confidence | Code Quality | Action | Reason |
|------------|--------------|---------|---------|
| High | Substantial | Mirror | Ready for immediate use |
| Medium | Minimal | Check Later | Early development |
| Low | Any | Reject | Not DXT-related |

## 🔍 Technical Details

### AI Prompt Engineering

The evaluation prompt is carefully crafted to:
- Provide clear context about DXT relevance
- Include all necessary repository information
- Specify expected output format
- Guide decision-making with examples

### Rate Limiting Strategy

GitHub API limits are managed through:
- **Strategic delays** between requests
- **Batch processing** to maximize efficiency
- **Respectful usage** within API guidelines
- **Automatic retry** logic for rate limit hits

### Natural Language Schema

Instead of rigid database schemas, we use:
- **Free-form text fields** for maximum flexibility
- **Human-readable content** that AI can process
- **Searchable natural language** for powerful queries
- **Extensible format** that grows with requirements

## 🧪 Example AI Decision

```
Repository: microsoft/vscode-claude-extension
Description: VS Code extension for Claude integration
Stars: 42
Language: TypeScript

AI Evaluation:
DECISION: mirror
REASON: High-quality VS Code extension with clear Claude integration, active development, and good documentation
NOTES: Well-structured TypeScript codebase with proper VS Code extension patterns, includes comprehensive README with installation and usage instructions
FUTURE_ACTIONS: Mirror immediately and consider featuring in DXT showcase
```

## 📊 Performance Characteristics

### Discovery Speed
- **~100 repositories/hour** with GitHub token
- **~10 repositories/hour** without token
- **Parallel processing** where possible
- **Efficient caching** of results

### AI Evaluation
- **~2-3 seconds per repository** (OpenAI GPT-3.5)
- **~1-2 seconds per repository** (Anthropic Claude)
- **Batch processing** for efficiency
- **Error handling** and retry logic

### Storage Efficiency
- **SQLite database** for fast queries
- **Natural language compression** (human-readable but compact)
- **Automatic indexing** for common queries
- **Export capabilities** for analysis

## 🔮 Advanced Usage

### Custom AI Analysis

```python
from dxt_curator import SimpleInventory

# Export inventory for AI analysis
inventory = SimpleInventory()
data = inventory.export_for_ai()

# Use with your own AI models
# Analyze patterns, generate reports, etc.
```

### Workflow Customization

```python
from dxt_curator.core import StrategicGitHubSearch, AIEvaluator

# Custom discovery
searcher = StrategicGitHubSearch(github_token)
results = searcher.discover_dxt_repositories()

# Filter results
filtered = [r for r in results if r.stars > 10]

# Custom evaluation
evaluator = AIEvaluator(api_provider="anthropic")
for repo in filtered:
    decision = evaluator.evaluate_repo(repo)
    print(f"{repo.full_name}: {decision['decision']}")
```

### Integration with Other Tools

```python
# Export for mirror setup
mirror_ready = inventory.get_repos_by_status('mirror')
for repo in mirror_ready:
    print(f"Mirror: {repo.clone_url}")
    print(f"Reason: {repo.evaluation_notes}")
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup

```bash
git clone https://github.com/DXT-Mirror/dxt-curator.git
cd dxt-curator
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black dxt_curator/
```

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Anthropic** for Claude and the inspiration for DXT
- **OpenAI** for GPT models that power the evaluation
- **GitHub** for the comprehensive API that makes discovery possible
- **DXT Community** for the use cases and requirements that shaped this tool

## 🏢 Sponsorship

This project is sponsored by the [Cloud Security Alliance (CSA)](https://cloudsecurityalliance.org/) and maintained by the Model Context Protocol Security Working Group.

## 🆘 Support

- **Documentation**: [README.md](README.md)
- **Issues**: [GitHub Issues](https://github.com/DXT-Mirror/dxt-curator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/DXT-Mirror/dxt-curator/discussions)

## 🗺️ Roadmap

- [ ] **Web Interface**: Browser-based UI for non-technical users
- [ ] **Advanced Analytics**: Pattern recognition and trend analysis
- [ ] **Integration APIs**: Webhooks and REST API for external tools
- [ ] **Multi-language Support**: Evaluation in languages other than English
- [ ] **Collaborative Features**: Team-based curation and decision making

---

**DXT Curator** represents the future of repository curation - where AI and human intelligence work together to create something better than either could achieve alone.

## 🎨 Philosophy in Action

This project embodies several key principles:

### 1. **AI-First Design**
Instead of trying to encode human knowledge into rigid rules, we let AI process information the way humans do - by reading, understanding, and making contextual decisions.

### 2. **Natural Language as Data**
All decisions, reasoning, and metadata are stored in human-readable format. This makes the system transparent, debuggable, and extensible without code changes.

### 3. **Flexible Decision Framework**
Rather than binary accept/reject decisions, we support nuanced outcomes like "check later" that reflect the real-world complexity of repository evaluation.

### 4. **Complete Audit Trail**
Every decision is recorded with full reasoning, creating a comprehensive history that can be analyzed, learned from, and improved upon.

### 5. **Strategic Automation**
We automate the tedious parts (discovery, cloning, data extraction) while letting AI handle the creative parts (evaluation, reasoning, decision-making).

This approach creates a system that's both powerful and maintainable, capable of handling edge cases and evolving requirements without constant developer intervention.

**The future of software curation is here - and it speaks natural language.**