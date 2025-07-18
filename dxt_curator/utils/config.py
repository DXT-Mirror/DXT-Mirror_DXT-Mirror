"""
Configuration management for DXT Curator.

This module provides centralized configuration management that supports
both environment variables and configuration files. It follows the
principle of "sensible defaults with easy customization."
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """
    Configuration manager for DXT Curator.
    
    This class provides a centralized way to manage configuration
    across all components of the system.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Optional path to configuration file
        """
        self.config_file = config_file or "dxt_curator_config.json"
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file and environment variables."""
        # Default configuration
        config = {
            'github': {
                'token': os.getenv('GITHUB_MIRROR_TOKEN') or os.getenv('GITHUB_TOKEN'),
                'rate_limit_delay': 1.0,
                'max_search_results': 100
            },
            'ai': {
                'provider': 'openai',
                'openai_api_key': os.getenv('OPENAI_API_KEY'),
                'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY'),
                'max_tokens': 1000,
                'temperature': 0.1
            },
            'inventory': {
                'database_path': 'dxt_inventory.db',
                'backup_interval': 3600  # 1 hour
            },
            'workflow': {
                'temp_dir': './temp_clones',
                'clone_timeout': 60,
                'default_discovery_limit': 50
            }
        }
        
        # Load from file if it exists
        if Path(self.config_file).exists():
            try:
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                    config.update(file_config)
            except Exception as e:
                print(f"Warning: Could not load config file {self.config_file}: {e}")
        
        return config
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., 'github.token')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def save(self) -> None:
        """Save current configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config file: {e}")


# Global configuration instance
_config = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config