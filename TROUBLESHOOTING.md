# DXT Curator Troubleshooting Guide

This guide helps you resolve common issues with DXT Curator.

## 🚨 Common Issues

### Installation Problems

#### "Package not found" error
```bash
# Problem: pip install dxt-curator fails
# Solution: Install in development mode
pip install -e .

# Or install with all dependencies
pip install -e ".[dev]"
```

#### "Python version not supported"
```bash
# Problem: Python version too old
# Solution: Use Python 3.8 or newer
python --version  # Check your version
pyenv install 3.9.0  # Install newer Python if needed
```

#### "No module named 'dxt_curator'"
```bash
# Problem: Package not installed correctly
# Solution: Clean and reinstall
pip uninstall dxt-curator
pip install -e .
```

### Configuration Issues

#### "No API key found"
```bash
# Problem: Missing API keys
# Solution: Set environment variables
export GITHUB_TOKEN="your_token_here"
export OPENAI_API_KEY="your_key_here"
# OR
export ANTHROPIC_API_KEY="your_key_here"

# Or create .env file
cp .env.example .env
# Edit .env with your keys
```

#### "Invalid configuration"
```bash
# Problem: Bad config file
# Solution: Validate configuration
python -c "from dxt_curator.utils.config import Config; Config()"

# Or regenerate config
rm dxt_curator_config.json
python setup_dev.py
```

### Discovery Problems

#### "Rate limit exceeded"
```bash
# Problem: GitHub API rate limit hit
# Solution: Wait or use authenticated requests
export GITHUB_TOKEN="your_token_here"  # Increases rate limit

# Or reduce discovery rate
dxt-curator discover 5  # Instead of 50
```

#### "No repositories found"
```bash
# Problem: Search returns no results
# Solution: Check search terms or broaden criteria
dxt-curator discover 10 --min-stars 1  # Lower star threshold
```

#### "Clone timeout"
```bash
# Problem: Repository cloning times out
# Solution: Increase timeout in config
{
  "workflow": {
    "clone_timeout": 120
  }
}
```

### Evaluation Problems

#### "AI evaluation failed"
```bash
# Problem: AI API issues
# Solution: Check API key and provider
python -c "import os; print(os.getenv('OPENAI_API_KEY', 'Not set'))"

# Test with different provider
dxt-curator discover 5 --ai-provider anthropic
```

#### "JSON parsing error"
```bash
# Problem: AI response not in expected format
# Solution: Check logs for details
tail -f dxt_curator.log

# Or run with debug logging
export LOG_LEVEL=DEBUG
dxt-curator discover 5
```

#### "Prompt injection detected"
```bash
# Problem: Security system flagging content
# Solution: Check security logs
cat security.log

# This is normal - the system is working correctly
```

### Database Issues

#### "Database locked"
```bash
# Problem: SQLite database locked
# Solution: Check for running processes
ps aux | grep dxt-curator

# Or remove lock file
rm dxt_inventory.db-wal
rm dxt_inventory.db-shm
```

#### "Corrupted database"
```bash
# Problem: Database corruption
# Solution: Backup and recreate
cp dxt_inventory.db dxt_inventory.db.backup
rm dxt_inventory.db
dxt-curator discover 5  # Recreates database
```

### Network Issues

#### "Connection timeout"
```bash
# Problem: Network connectivity issues
# Solution: Check network and proxy settings
curl -I https://api.github.com

# Configure proxy if needed
export HTTP_PROXY=http://proxy:8080
export HTTPS_PROXY=http://proxy:8080
```

#### "SSL certificate error"
```bash
# Problem: SSL/TLS certificate issues
# Solution: Update certificates or disable verification (not recommended)
pip install --upgrade certifi

# Only as last resort:
export PYTHONHTTPSVERIFY=0
```

## 🔧 Debugging Tools

### Health Check
```bash
# Quick health check
make health

# Or manual check
python scripts/test_setup.py
```

### Verbose Logging
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
dxt-curator discover 5

# Or check logs
tail -f dxt_curator.log
```

### Configuration Validation
```bash
# Validate configuration
python -c "from dxt_curator.utils.config import Config; c = Config(); print('OK')"

# Show current config
python -c "from dxt_curator.utils.config import Config; c = Config(); print(c.to_dict())"
```

### Database Inspection
```bash
# Check database status
python -c "from dxt_curator import SimpleInventory; i = SimpleInventory(); print(i.get_summary())"

# Export database for inspection
dxt-curator export --output debug_export.json
```

## 🛠️ Advanced Debugging

### Custom Logging
```python
import logging
import sys

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Now run your code
from dxt_curator import SimpleDXTWorkflow
workflow = SimpleDXTWorkflow()
```

### Manual Testing
```python
# Test individual components
from dxt_curator.core import StrategicGitHubSearch, AIEvaluator
from dxt_curator.utils.security import get_sanitizer

# Test discovery
searcher = StrategicGitHubSearch()
results = searcher.discover_dxt_repositories(max_total=1)

# Test evaluation
evaluator = AIEvaluator()
decision = evaluator.evaluate_repo(results[0].__dict__)

# Test security
sanitizer = get_sanitizer()
safe_content = sanitizer.sanitize_content("test content")
```

### Performance Profiling
```python
import cProfile
import pstats

# Profile discovery
pr = cProfile.Profile()
pr.enable()

from dxt_curator import SimpleDXTWorkflow
workflow = SimpleDXTWorkflow()
workflow.discover_and_evaluate(5)

pr.disable()
stats = pstats.Stats(pr)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

## 📊 Performance Issues

### Slow Discovery
```bash
# Problem: Discovery takes too long
# Solution: Reduce batch size or increase delays
{
  "github": {
    "rate_limit_delay": 0.5,
    "max_search_results": 50
  }
}
```

### Memory Usage
```bash
# Problem: High memory usage
# Solution: Process in smaller batches
dxt-curator discover 10  # Instead of 100

# Or increase swap space
sudo swapon --show
```

### Disk Space
```bash
# Problem: Running out of disk space
# Solution: Clean up temporary files
make clean

# Or clean manually
rm -rf temp_clones/
rm -rf __pycache__/
```

## 🔒 Security Issues

### Suspicious Content Warnings
```bash
# Problem: Many security warnings
# Solution: This is normal - check security.log
cat security.log

# Security system is working correctly
```

### False Positives
```bash
# Problem: Good repositories being flagged
# Solution: Adjust security patterns (advanced)
# Edit dxt_curator/utils/security.py
# Or report the issue for pattern improvement
```

## 🆘 Getting Help

### Self-Help Checklist
- [ ] Check this troubleshooting guide
- [ ] Run `make health` or `python scripts/test_setup.py`
- [ ] Check logs: `tail -f dxt_curator.log`
- [ ] Verify API keys are set correctly
- [ ] Try with a smaller test case

### Reporting Issues
When reporting issues, include:
1. **Error message**: Complete error text
2. **Environment**: OS, Python version, package version
3. **Configuration**: Anonymized config file
4. **Steps to reproduce**: Exact commands run
5. **Logs**: Relevant log entries

```bash
# Gather debugging info
echo "Python version: $(python --version)"
echo "Package version: $(pip show dxt-curator | grep Version)"
echo "OS: $(uname -a)"
echo "Config exists: $([ -f dxt_curator_config.json ] && echo 'Yes' || echo 'No')"
echo "Env file exists: $([ -f .env ] && echo 'Yes' || echo 'No')"
```

### Community Resources
- **GitHub Issues**: [Report bugs and feature requests](https://github.com/DXT-Mirror/dxt-curator/issues)
- **Discussions**: [Ask questions and share ideas](https://github.com/DXT-Mirror/dxt-curator/discussions)
- **Documentation**: README.md and EXAMPLES.md

## 🔄 Recovery Procedures

### Complete Reset
```bash
# Nuclear option - complete reset
make clean
rm -f dxt_inventory.db*
rm -f dxt_curator_config.json
rm -f .env
pip uninstall dxt-curator
pip install -e .
python setup_dev.py
```

### Backup and Restore
```bash
# Backup important data
cp dxt_inventory.db dxt_inventory.db.backup
cp dxt_curator_config.json dxt_curator_config.json.backup

# Restore if needed
cp dxt_inventory.db.backup dxt_inventory.db
cp dxt_curator_config.json.backup dxt_curator_config.json
```

---

**Remember**: Most issues are configuration-related. Check your API keys, environment variables, and configuration files first!