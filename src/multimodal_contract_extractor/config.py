"""Centralized configuration management for Multimodal Contract Extractor.

This module provides a centralized configuration system that follows the
Twelve-Factor App methodology, supporting configuration via environment
variables and YAML files, with environment variables taking precedence.

Environment Variable Naming Convention:
- Prefix: MCE_ (Multimodal Contract Extractor)
- Format: MCE_<SECTION>_<SETTING>
- Example: MCE_OCR_CACHE_SIZE_LIMIT=200

Example configuration file (config.yml):
```yaml
ocr:
  cache_size_limit: 100
  context_window_size: 100

extraction:
  base_confidence_score: 0.75
  length_bonus_divisor: 1000
  max_confidence_cap: 0.95
  file_size_threshold_mb: 10
  streaming_chunk_size: 5

security:
  max_file_size_mb: 100
  request_id_length_limit: 64

health:
  check_timeout_seconds: 5

document:
  default_streaming_chunk_size: 10
```
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""


@dataclass
class OCRConfig:
    """OCR-related configuration."""
    cache_size_limit: int = 100
    context_window_size: int = 100


@dataclass
class ExtractionConfig:
    """Document extraction configuration."""
    base_confidence_score: float = 0.75
    length_bonus_divisor: int = 1000
    max_confidence_cap: float = 0.95
    file_size_threshold_mb: int = 10
    streaming_chunk_size: int = 5


@dataclass
class SecurityConfig:
    """Security-related configuration."""
    max_file_size_mb: int = 100
    request_id_length_limit: int = 64


@dataclass
class HealthConfig:
    """Health check configuration."""
    check_timeout_seconds: int = 5


@dataclass
class DocumentConfig:
    """Document processing configuration."""
    default_streaming_chunk_size: int = 10


@dataclass
class Config:
    """Main configuration class containing all configuration sections."""
    ocr: OCRConfig = field(default_factory=OCRConfig)
    extraction: ExtractionConfig = field(default_factory=ExtractionConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    health: HealthConfig = field(default_factory=HealthConfig)
    document: DocumentConfig = field(default_factory=DocumentConfig)


# Global configuration singleton
_config_instance: Config | None = None


def _load_from_environment() -> dict[str, Any]:
    """Load configuration overrides from environment variables.

    Returns:
        Dictionary of configuration values parsed from environment variables.
    """
    env_config = {}

    # OCR Configuration
    if val := os.getenv("MCE_OCR_CACHE_SIZE_LIMIT"):
        env_config.setdefault("ocr", {})["cache_size_limit"] = int(val)
    if val := os.getenv("MCE_OCR_CONTEXT_WINDOW_SIZE"):
        env_config.setdefault("ocr", {})["context_window_size"] = int(val)

    # Extraction Configuration
    if val := os.getenv("MCE_EXTRACTION_BASE_CONFIDENCE_SCORE"):
        env_config.setdefault("extraction", {})["base_confidence_score"] = float(val)
    if val := os.getenv("MCE_EXTRACTION_LENGTH_BONUS_DIVISOR"):
        env_config.setdefault("extraction", {})["length_bonus_divisor"] = int(val)
    if val := os.getenv("MCE_EXTRACTION_MAX_CONFIDENCE_CAP"):
        env_config.setdefault("extraction", {})["max_confidence_cap"] = float(val)
    if val := os.getenv("MCE_EXTRACTION_FILE_SIZE_THRESHOLD_MB"):
        env_config.setdefault("extraction", {})["file_size_threshold_mb"] = int(val)
    if val := os.getenv("MCE_EXTRACTION_STREAMING_CHUNK_SIZE"):
        env_config.setdefault("extraction", {})["streaming_chunk_size"] = int(val)

    # Security Configuration
    if val := os.getenv("MCE_SECURITY_MAX_FILE_SIZE_MB"):
        env_config.setdefault("security", {})["max_file_size_mb"] = int(val)
    if val := os.getenv("MCE_SECURITY_REQUEST_ID_LENGTH_LIMIT"):
        env_config.setdefault("security", {})["request_id_length_limit"] = int(val)

    # Health Configuration
    if val := os.getenv("MCE_HEALTH_CHECK_TIMEOUT_SECONDS"):
        env_config.setdefault("health", {})["check_timeout_seconds"] = int(val)

    # Document Configuration
    if val := os.getenv("MCE_DOCUMENT_DEFAULT_STREAMING_CHUNK_SIZE"):
        env_config.setdefault("document", {})["default_streaming_chunk_size"] = int(val)

    return env_config


def _load_from_file(config_path: str) -> dict[str, Any]:
    """Load configuration from YAML file.

    Args:
        config_path: Path to the YAML configuration file.

    Returns:
        Dictionary of configuration values from the file.

    Raises:
        FileNotFoundError: If the config file doesn't exist.
        yaml.YAMLError: If the YAML file is malformed.
    """
    path = Path(config_path)
    if not path.exists():
        msg = f"Configuration file not found: {config_path}"
        raise FileNotFoundError(msg)

    with open(path, encoding="utf-8") as f:
        try:
            return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            msg = f"Invalid YAML in config file {config_path}: {e}"
            raise yaml.YAMLError(msg) from e


def _merge_configs(*configs: dict[str, Any]) -> dict[str, Any]:
    """Merge multiple configuration dictionaries, with later ones taking precedence.

    Args:
        *configs: Configuration dictionaries to merge.

    Returns:
        Merged configuration dictionary.
    """
    merged = {}

    for config in configs:
        for section, values in config.items():
            if section not in merged:
                merged[section] = {}
            if isinstance(values, dict):
                merged[section].update(values)
            else:
                merged[section] = values

    return merged


def _create_config_from_dict(config_dict: dict[str, Any]) -> Config:
    """Create a Config instance from a dictionary.

    Args:
        config_dict: Dictionary containing configuration values.

    Returns:
        Config instance populated with the provided values.
    """
    config = Config()

    # Update OCR config
    if "ocr" in config_dict:
        for key, value in config_dict["ocr"].items():
            if hasattr(config.ocr, key):
                setattr(config.ocr, key, value)

    # Update Extraction config
    if "extraction" in config_dict:
        for key, value in config_dict["extraction"].items():
            if hasattr(config.extraction, key):
                setattr(config.extraction, key, value)

    # Update Security config
    if "security" in config_dict:
        for key, value in config_dict["security"].items():
            if hasattr(config.security, key):
                setattr(config.security, key, value)

    # Update Health config
    if "health" in config_dict:
        for key, value in config_dict["health"].items():
            if hasattr(config.health, key):
                setattr(config.health, key, value)

    # Update Document config
    if "document" in config_dict:
        for key, value in config_dict["document"].items():
            if hasattr(config.document, key):
                setattr(config.document, key, value)

    return config


def validate_config(config: Config) -> None:
    """Validate configuration values.

    Args:
        config: Configuration instance to validate.

    Raises:
        ConfigValidationError: If any configuration values are invalid.
    """
    errors = []

    # Validate OCR configuration
    if config.ocr.cache_size_limit <= 0:
        errors.append("ocr.cache_size_limit must be positive")
    if config.ocr.context_window_size <= 0:
        errors.append("ocr.context_window_size must be positive")

    # Validate Extraction configuration
    if not 0.0 <= config.extraction.base_confidence_score <= 1.0:
        errors.append("extraction.base_confidence_score must be between 0.0 and 1.0")
    if config.extraction.length_bonus_divisor <= 0:
        errors.append("extraction.length_bonus_divisor must be positive")
    if not 0.0 <= config.extraction.max_confidence_cap <= 1.0:
        errors.append("extraction.max_confidence_cap must be between 0.0 and 1.0")
    if config.extraction.file_size_threshold_mb <= 0:
        errors.append("extraction.file_size_threshold_mb must be positive")
    if config.extraction.streaming_chunk_size <= 0:
        errors.append("extraction.streaming_chunk_size must be positive")

    # Validate Security configuration
    if config.security.max_file_size_mb <= 0:
        errors.append("security.max_file_size_mb must be positive")
    if config.security.request_id_length_limit <= 0:
        errors.append("security.request_id_length_limit must be positive")

    # Validate Health configuration
    if config.health.check_timeout_seconds <= 0:
        errors.append("health.check_timeout_seconds must be positive")

    # Validate Document configuration
    if config.document.default_streaming_chunk_size <= 0:
        errors.append("document.default_streaming_chunk_size must be positive")

    if errors:
        raise ConfigValidationError("Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors))


def load_config(config_path: str | None = None, reload: bool = False) -> Config:
    """Load configuration from file and environment variables.

    Configuration is loaded in the following order (later sources override earlier ones):
    1. Default values (hardcoded in dataclasses)
    2. Configuration file (if provided)
    3. Environment variables (always checked)

    Args:
        config_path: Optional path to YAML configuration file.
        reload: If True, reload the configuration even if already loaded.

    Returns:
        Configured Config instance.

    Raises:
        ConfigValidationError: If configuration validation fails.
        FileNotFoundError: If config_path is provided but file doesn't exist.
        yaml.YAMLError: If the YAML file is malformed.
    """
    global _config_instance

    # Return cached instance unless reload requested
    if _config_instance is not None and not reload:
        return _config_instance

    # Start with empty config dict (defaults come from dataclasses)
    configs_to_merge = []

    # Load from file if provided
    if config_path:
        try:
            file_config = _load_from_file(config_path)
            configs_to_merge.append(file_config)
            logger.info(f"Loaded configuration from file: {config_path}")
        except FileNotFoundError:
            logger.warning(f"Configuration file not found: {config_path}, using defaults")
        except yaml.YAMLError as e:
            logger.exception(f"Failed to parse configuration file {config_path}: {e}")
            raise

    # Load from environment (always checked, takes precedence)
    env_config = _load_from_environment()
    if env_config:
        configs_to_merge.append(env_config)
        logger.info("Applied configuration overrides from environment variables")

    # Merge all configuration sources
    if configs_to_merge:
        merged_config = _merge_configs(*configs_to_merge)
        config = _create_config_from_dict(merged_config)
    else:
        # Use all defaults
        config = Config()
        logger.info("Using default configuration values")

    # Validate the final configuration
    validate_config(config)

    # Cache and return
    _config_instance = config
    return config


def get_config() -> Config:
    """Get the current configuration instance.

    If no configuration has been loaded yet, loads with default values.

    Returns:
        Current Config instance.
    """
    if _config_instance is None:
        return load_config()
    return _config_instance


def reload_config(config_path: str | None = None) -> Config:
    """Reload configuration, clearing any cached instance.

    Args:
        config_path: Optional path to YAML configuration file.

    Returns:
        Newly loaded Config instance.
    """
    return load_config(config_path=config_path, reload=True)
