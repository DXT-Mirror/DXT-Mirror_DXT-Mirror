"""
DXT Curator: AI-Powered Repository Discovery and Curation

A natural language approach to finding, evaluating, and curating DXT (Claude Desktop Extension) 
repositories using AI APIs. This package provides both programmatic APIs and CLI tools.

Philosophy:
- Use AI's natural language processing strengths instead of rigid structures
- Store decisions and reasoning in human-readable format
- Leverage AI to read repositories like humans do
- Maintain complete audit trails with natural language explanations

Key Components:
- Discovery: Strategic GitHub search with quality filtering
- Evaluation: AI-powered analysis using OpenAI/Anthropic APIs
- Inventory: Natural language repository tracking
- Workflow: Simple orchestration of the entire process
"""

__version__ = "0.1.0"
__author__ = "DXT Mirror Team"
__email__ = "team@dxt-mirror.org"

# Core imports for library usage
from .core.inventory import SimpleInventory
from .core.file_inventory import FileInventory
from .core.evaluator import AIEvaluator
from .core.discovery import StrategicGitHubSearch
from .core.workflow import SimpleDXTWorkflow

# Convenience imports
from .utils.config import Config
from .utils.logging import setup_logging

__all__ = [
    'SimpleInventory',
    'FileInventory',
    'AIEvaluator', 
    'StrategicGitHubSearch',
    'SimpleDXTWorkflow',
    'Config',
    'setup_logging'
]