"""
Configuration loader with validation and defaults.
"""

import yaml
from pathlib import Path
from typing import Dict, Any


DEFAULT_CONFIG = {
    "coercion_thresholds": {
        "numeric": 0.8,
        "date": 0.7,
        "categorical_unique_ratio": 0.3
    },
    "imputation": {
        "numeric": "median",
        "categorical": "mode",
        "date": "keep_nat"
    },
    "duplicates": {
        "default_action": "remove_keep_first"
    },
    "outlier": {
        "zscore_threshold": 3.0,
        "iqr_multiplier": 1.5,
        "isolationforest_min_rows": 50,
        "contamination": 0.05
    },
    "health_weights": {
        "completeness": 0.35,
        "uniqueness": 0.2,
        "consistency": 0.2,
        "validity": 0.15,
        "outlier_penalty": 0.1
    },
    "manual_review": {
        "health_threshold": 0.6,
        "coercion_loss_threshold": 0.2
    },
    "upload": {
        "max_bytes": 20000000,
        "allowed_extensions": [".csv", ".xlsx"]
    },
    "logging": {
        "level": "INFO",
        "format": "json",
        "mask_pii": True
    },
    "persistence": {
        "enable_action_log": True
    },
    "analysis": {
        "top_values_count": 10,
        "skewness_threshold": 0.5,
        "top_k_contribution_pct": 10
    }
}


def _deep_merge(base: Dict, override: Dict) -> Dict:
    """Deep merge two dictionaries."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file with fallback to defaults.
    
    Args:
        config_path: Path to config.yaml file. If None, looks in current directory.
        
    Returns:
        Configuration dictionary with validated values.
    """
    config = DEFAULT_CONFIG.copy()
    
    if config_path is None:
        # Try to find config.yaml in the same directory as this file
        current_dir = Path(__file__).parent.parent
        config_path = current_dir / "config.yaml"
    else:
        config_path = Path(config_path)
    
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                if user_config:
                    config = _deep_merge(config, user_config)
        except Exception as e:
            # Log warning but continue with defaults
            print(f"Warning: Could not load config from {config_path}: {e}")
            print("Using default configuration.")
    
    # Validate critical values
    _validate_config(config)
    
    return config


def _validate_config(config: Dict[str, Any]) -> None:
    """
    Validate configuration values.
    
    Raises:
        ValueError: If configuration is invalid.
    """
    # Validate thresholds are in valid ranges
    thresholds = config["coercion_thresholds"]
    for key, value in thresholds.items():
        if not 0 <= value <= 1:
            raise ValueError(f"coercion_thresholds.{key} must be between 0 and 1, got {value}")
    
    # Validate health weights sum to approximately 1.0
    weights = config["health_weights"]
    weight_sum = sum(weights.values())
    if not 0.95 <= weight_sum <= 1.05:
        raise ValueError(f"health_weights must sum to ~1.0, got {weight_sum}")
    
    # Validate outlier parameters
    outlier = config["outlier"]
    if outlier["zscore_threshold"] <= 0:
        raise ValueError("outlier.zscore_threshold must be positive")
    if outlier["iqr_multiplier"] <= 0:
        raise ValueError("outlier.iqr_multiplier must be positive")
    if not 0 < outlier["contamination"] < 0.5:
        raise ValueError("outlier.contamination must be between 0 and 0.5")
    
    # Validate upload limits
    if config["upload"]["max_bytes"] <= 0:
        raise ValueError("upload.max_bytes must be positive")


def get_config_value(config: Dict[str, Any], path: str, default: Any = None) -> Any:
    """
    Get a nested configuration value using dot notation.
    
    Args:
        config: Configuration dictionary
        path: Dot-separated path (e.g., "outlier.zscore_threshold")
        default: Default value if path not found
        
    Returns:
        Configuration value or default
    """
    keys = path.split('.')
    value = config
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    
    return value
