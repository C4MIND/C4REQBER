"""
Pattern Configuration System
Manage which patterns are enabled/loaded
"""

import os
import yaml
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class PatternConfig:
    """Configuration for pattern loading"""
    
    auto_load_tiers: List[str] = field(default_factory=lambda: ["CORE", "ESSENTIAL"])
    enabled_patterns: List[str] = field(default_factory=list)
    disabled_patterns: List[str] = field(default_factory=list)
    validation_prep_load: bool = True
    validation_max_patterns: int = 10
    max_memory_mb: int = 4096
    max_loaded_patterns: int = 50
    lazy_load_extended: bool = True
    lazy_load_on_demand: bool = True
    auto_install_dependencies: bool = False
    cache_loaded_patterns: bool = True
    cache_dir: str = ".pattern_cache"
    
    @classmethod
    def from_file(cls, path: str) -> "PatternConfig":
        """Load configuration from YAML or JSON file"""
        path = Path(path)
        
        if not path.exists():
            logger.warning(f"Config file not found: {path}, using defaults")
            return cls()
            
        with open(path) as f:
            if path.suffix == '.json':
                data = json.load(f)
            else:
                data = yaml.safe_load(f)
                
        return cls(**data)
    
    @classmethod
    def from_env(cls) -> "PatternConfig":
        """Load configuration from environment variables"""
        config = cls()
        
        if tiers := os.getenv("TURBO_CDI_AUTO_LOAD_TIERS"):
            config.auto_load_tiers = tiers.split(",")
            
        if enabled := os.getenv("TURBO_CDI_ENABLED_PATTERNS"):
            config.enabled_patterns = enabled.split(",")
            
        if disabled := os.getenv("TURBO_CDI_DISABLED_PATTERNS"):
            config.disabled_patterns = disabled.split(",")
            
        if mem := os.getenv("TURBO_CDI_MAX_MEMORY_MB"):
            config.max_memory_mb = int(mem)
            
        if os.getenv("TURBO_CDI_AUTO_INSTALL"):
            config.auto_install_dependencies = True
            
        return config
    
    def should_load(self, pattern_id: str, tier: str) -> bool:
        """Check if pattern should be loaded based on configuration"""
        if pattern_id in self.disabled_patterns:
            return False
            
        if pattern_id in self.enabled_patterns:
            return True
            
        return tier in self.auto_load_tiers


default_config_yaml = """
# TURBO-CDI Pattern Loading Configuration

auto_load_tiers:
  - CORE
  - ESSENTIAL

enabled_patterns: []
disabled_patterns: []

validation_prep_load: true
validation_max_patterns: 10

max_memory_mb: 4096
max_loaded_patterns: 50

lazy_load_extended: true
lazy_load_on_demand: true

auto_install_dependencies: false

cache_loaded_patterns: true
cache_dir: ".pattern_cache"
"""


def create_default_config(path: str = "config/patterns.yaml"):
    """Create default configuration file"""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        f.write(default_config_yaml)
    logger.info(f"Created default pattern config: {path}")
