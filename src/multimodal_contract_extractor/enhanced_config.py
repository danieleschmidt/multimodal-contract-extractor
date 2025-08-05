"""
Enhanced configuration management for Generation 2 features.

This module extends the base configuration with support for all Generation 2 features
including resilience, security, monitoring, validation, and infrastructure components.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml

from .config import Config as BaseConfig
from .config import DocumentConfig, ExtractionConfig, OCRConfig

logger = logging.getLogger(__name__)


class EnhancedConfigValidationError(Exception):
    """Raised when enhanced configuration validation fails."""


@dataclass
class ResilienceConfig:
    """Resilience and fault tolerance configuration."""

    # Circuit breaker settings
    circuit_breaker_enabled: bool = True
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout: float = 60.0
    circuit_breaker_expected_failure_rate: float = 0.5
    circuit_breaker_minimum_requests: int = 10

    # Retry settings
    retry_enabled: bool = True
    retry_max_attempts: int = 3
    retry_initial_delay: float = 1.0
    retry_max_delay: float = 60.0
    retry_backoff_multiplier: float = 2.0
    retry_jitter_enabled: bool = True

    # Graceful degradation
    graceful_degradation_enabled: bool = True
    degradation_timeout_seconds: int = 30


@dataclass
class EnhancedSecurityConfig:
    """Enhanced security configuration."""

    # Basic security (inherited from base)
    max_file_size_mb: int = 100
    request_id_length_limit: int = 64

    # Virus scanning
    virus_scanning_enabled: bool = True
    virus_scan_timeout_seconds: int = 30

    # Rate limiting
    rate_limiting_enabled: bool = True
    rate_limit_requests_per_window: int = 100
    rate_limit_window_seconds: int = 60
    rate_limit_block_duration_seconds: int = 300

    # Authentication & Authorization
    jwt_enabled: bool = True
    jwt_secret_key: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # Audit logging
    audit_logging_enabled: bool = True
    audit_log_file: Optional[str] = None
    audit_max_events: int = 10000

    # Encryption
    encryption_enabled: bool = True

    # Network security
    allowed_origins: List[str] = field(default_factory=lambda: ["*"])
    blocked_ips: Set[str] = field(default_factory=set)
    trusted_proxies: Set[str] = field(default_factory=set)
    require_https: bool = True

    # Session management
    session_timeout_minutes: int = 30
    min_password_length: int = 8


@dataclass
class ValidationConfig:
    """Data validation and integrity configuration."""

    # Schema validation
    schema_validation_enabled: bool = True
    strict_schema_validation: bool = False

    # File integrity
    file_integrity_checks_enabled: bool = True
    checksum_algorithms: List[str] = field(default_factory=lambda: ["sha256", "md5"])

    # Data structure validation
    structure_validation_enabled: bool = True
    max_nesting_depth: int = 10
    max_string_length: int = 10000
    max_list_length: int = 10000

    # Corruption detection
    corruption_detection_enabled: bool = True
    null_byte_check_enabled: bool = True
    compression_ratio_check_enabled: bool = True

    # Validation reporting
    detailed_validation_reports: bool = True
    validation_cache_enabled: bool = True
    validation_cache_ttl_seconds: int = 3600


@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration."""

    # Structured logging
    structured_logging_enabled: bool = True
    log_level: str = "INFO"
    log_format: str = "json"
    log_file: Optional[str] = None
    log_rotation_enabled: bool = True
    log_max_size_mb: int = 100
    log_backup_count: int = 5

    # Metrics collection
    metrics_enabled: bool = True
    metrics_port: int = 8000
    metrics_path: str = "/metrics"
    custom_metrics_enabled: bool = True

    # Distributed tracing
    tracing_enabled: bool = True
    tracing_sample_rate: float = 1.0
    jaeger_enabled: bool = False
    jaeger_endpoint: Optional[str] = None

    # Performance profiling
    profiling_enabled: bool = True
    profile_slow_operations: bool = True
    slow_operation_threshold_seconds: float = 1.0

    # Alerting
    alerting_enabled: bool = True
    alert_webhook_url: Optional[str] = None
    alert_slack_webhook: Optional[str] = None
    alert_email_recipients: List[str] = field(default_factory=list)

    # System monitoring
    system_monitoring_enabled: bool = True
    system_monitoring_interval_seconds: int = 30
    resource_threshold_cpu_percent: float = 80.0
    resource_threshold_memory_percent: float = 85.0
    resource_threshold_disk_percent: float = 90.0


@dataclass
class InfrastructureConfig:
    """Infrastructure and deployment configuration."""

    # Caching
    caching_enabled: bool = True
    cache_type: str = "memory"  # memory, redis
    cache_max_size: int = 1000
    cache_ttl_seconds: int = 3600
    cache_compression_enabled: bool = True
    cache_persistence_enabled: bool = False
    cache_persistence_path: Optional[str] = None

    # Redis (if cache_type = "redis")
    redis_url: str = "redis://localhost:6379"
    redis_db: int = 0
    redis_timeout_seconds: int = 5

    # Database connection pooling
    database_pooling_enabled: bool = True
    database_pool_size: int = 10
    database_pool_max_overflow: int = 20
    database_pool_timeout_seconds: int = 30
    database_pool_recycle_seconds: int = 3600

    # Backup and recovery
    backup_enabled: bool = True
    backup_strategy: str = "incremental"  # full, incremental, differential
    backup_directory: str = "backups"
    backup_retention_days: int = 30
    backup_compression_enabled: bool = True
    backup_schedule_hours: List[int] = field(default_factory=lambda: [2, 14])

    # Health monitoring
    health_monitoring_enabled: bool = True
    health_check_interval_seconds: int = 60
    health_check_timeout_seconds: int = 30

    # Failover and high availability
    failover_enabled: bool = False
    failover_nodes: List[str] = field(default_factory=list)
    load_balancing_enabled: bool = False
    load_balancing_strategy: str = "round_robin"


@dataclass
class TestingConfig:
    """Testing and QA configuration."""

    # Test execution
    test_timeout_seconds: int = 300
    parallel_test_execution: bool = True
    test_workers: int = 4

    # Security testing
    security_tests_enabled: bool = True
    penetration_testing_enabled: bool = False
    vulnerability_scanning_enabled: bool = True

    # Performance testing
    performance_tests_enabled: bool = True
    load_testing_enabled: bool = False
    stress_testing_enabled: bool = False
    benchmark_baseline_enabled: bool = True

    # Chaos engineering
    chaos_testing_enabled: bool = False
    chaos_failure_rate: float = 0.1
    chaos_recovery_time_seconds: int = 60

    # Test data management
    test_data_cleanup_enabled: bool = True
    test_isolation_enabled: bool = True
    test_fixtures_auto_generation: bool = True


@dataclass
class EnhancedConfig:
    """Enhanced configuration with Generation 2 features."""

    # Base configurations (Generation 1)
    ocr: OCRConfig = field(default_factory=OCRConfig)
    extraction: ExtractionConfig = field(default_factory=ExtractionConfig)
    document: DocumentConfig = field(default_factory=DocumentConfig)

    # Generation 2 configurations
    resilience: ResilienceConfig = field(default_factory=ResilienceConfig)
    security: EnhancedSecurityConfig = field(default_factory=EnhancedSecurityConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    infrastructure: InfrastructureConfig = field(default_factory=InfrastructureConfig)
    testing: TestingConfig = field(default_factory=TestingConfig)

    # Global settings
    environment: str = "development"
    debug_enabled: bool = False
    feature_flags: Dict[str, bool] = field(default_factory=dict)


# Global enhanced configuration singleton
_enhanced_config_instance: Optional[EnhancedConfig] = None


def _load_enhanced_from_environment() -> Dict[str, Any]:
    """Load enhanced configuration overrides from environment variables."""
    env_config = {}

    # Resilience Configuration
    if val := os.getenv("MCE_RESILIENCE_CIRCUIT_BREAKER_ENABLED"):
        env_config.setdefault("resilience", {})["circuit_breaker_enabled"] = val.lower() in ("true", "1", "yes")
    if val := os.getenv("MCE_RESILIENCE_CIRCUIT_BREAKER_FAILURE_THRESHOLD"):
        env_config.setdefault("resilience", {})["circuit_breaker_failure_threshold"] = int(val)
    if val := os.getenv("MCE_RESILIENCE_RETRY_ENABLED"):
        env_config.setdefault("resilience", {})["retry_enabled"] = val.lower() in ("true", "1", "yes")
    if val := os.getenv("MCE_RESILIENCE_RETRY_MAX_ATTEMPTS"):
        env_config.setdefault("resilience", {})["retry_max_attempts"] = int(val)

    # Enhanced Security Configuration
    if val := os.getenv("MCE_SECURITY_VIRUS_SCANNING_ENABLED"):
        env_config.setdefault("security", {})["virus_scanning_enabled"] = val.lower() in ("true", "1", "yes")
    if val := os.getenv("MCE_SECURITY_RATE_LIMITING_ENABLED"):
        env_config.setdefault("security", {})["rate_limiting_enabled"] = val.lower() in ("true", "1", "yes")
    if val := os.getenv("MCE_SECURITY_JWT_ENABLED"):
        env_config.setdefault("security", {})["jwt_enabled"] = val.lower() in ("true", "1", "yes")
    if val := os.getenv("MCE_SECURITY_JWT_SECRET_KEY"):
        env_config.setdefault("security", {})["jwt_secret_key"] = val
    if val := os.getenv("MCE_SECURITY_AUDIT_LOGGING_ENABLED"):
        env_config.setdefault("security", {})["audit_logging_enabled"] = val.lower() in ("true", "1", "yes")

    # Validation Configuration
    if val := os.getenv("MCE_VALIDATION_SCHEMA_VALIDATION_ENABLED"):
        env_config.setdefault("validation", {})["schema_validation_enabled"] = val.lower() in ("true", "1", "yes")
    if val := os.getenv("MCE_VALIDATION_FILE_INTEGRITY_CHECKS_ENABLED"):
        env_config.setdefault("validation", {})["file_integrity_checks_enabled"] = val.lower() in ("true", "1", "yes")
    if val := os.getenv("MCE_VALIDATION_CORRUPTION_DETECTION_ENABLED"):
        env_config.setdefault("validation", {})["corruption_detection_enabled"] = val.lower() in ("true", "1", "yes")

    # Monitoring Configuration
    if val := os.getenv("MCE_MONITORING_STRUCTURED_LOGGING_ENABLED"):
        env_config.setdefault("monitoring", {})["structured_logging_enabled"] = val.lower() in ("true", "1", "yes")
    if val := os.getenv("MCE_MONITORING_LOG_LEVEL"):
        env_config.setdefault("monitoring", {})["log_level"] = val.upper()
    if val := os.getenv("MCE_MONITORING_METRICS_ENABLED"):
        env_config.setdefault("monitoring", {})["metrics_enabled"] = val.lower() in ("true", "1", "yes")
    if val := os.getenv("MCE_MONITORING_TRACING_ENABLED"):
        env_config.setdefault("monitoring", {})["tracing_enabled"] = val.lower() in ("true", "1", "yes")
    if val := os.getenv("MCE_MONITORING_ALERTING_ENABLED"):
        env_config.setdefault("monitoring", {})["alerting_enabled"] = val.lower() in ("true", "1", "yes")

    # Infrastructure Configuration
    if val := os.getenv("MCE_INFRASTRUCTURE_CACHING_ENABLED"):
        env_config.setdefault("infrastructure", {})["caching_enabled"] = val.lower() in ("true", "1", "yes")
    if val := os.getenv("MCE_INFRASTRUCTURE_CACHE_TYPE"):
        env_config.setdefault("infrastructure", {})["cache_type"] = val
    if val := os.getenv("MCE_INFRASTRUCTURE_REDIS_URL"):
        env_config.setdefault("infrastructure", {})["redis_url"] = val
    if val := os.getenv("MCE_INFRASTRUCTURE_BACKUP_ENABLED"):
        env_config.setdefault("infrastructure", {})["backup_enabled"] = val.lower() in ("true", "1", "yes")
    if val := os.getenv("MCE_INFRASTRUCTURE_DATABASE_POOLING_ENABLED"):
        env_config.setdefault("infrastructure", {})["database_pooling_enabled"] = val.lower() in ("true", "1", "yes")

    # Testing Configuration
    if val := os.getenv("MCE_TESTING_SECURITY_TESTS_ENABLED"):
        env_config.setdefault("testing", {})["security_tests_enabled"] = val.lower() in ("true", "1", "yes")
    if val := os.getenv("MCE_TESTING_PERFORMANCE_TESTS_ENABLED"):
        env_config.setdefault("testing", {})["performance_tests_enabled"] = val.lower() in ("true", "1", "yes")
    if val := os.getenv("MCE_TESTING_CHAOS_TESTING_ENABLED"):
        env_config.setdefault("testing", {})["chaos_testing_enabled"] = val.lower() in ("true", "1", "yes")

    # Global Settings
    if val := os.getenv("MCE_ENVIRONMENT"):
        env_config["environment"] = val
    if val := os.getenv("MCE_DEBUG_ENABLED"):
        env_config["debug_enabled"] = val.lower() in ("true", "1", "yes")

    return env_config


def _load_enhanced_from_file(config_path: str) -> Dict[str, Any]:
    """Load enhanced configuration from YAML file."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Enhanced configuration file not found: {config_path}")

    with open(path, encoding="utf-8") as f:
        try:
            return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Invalid YAML in enhanced config file {config_path}: {e}") from e


def _merge_enhanced_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple enhanced configuration dictionaries."""
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


def _create_enhanced_config_from_dict(config_dict: Dict[str, Any]) -> EnhancedConfig:
    """Create an EnhancedConfig instance from a dictionary."""
    config = EnhancedConfig()

    # Update all sections
    sections = [
        "ocr", "extraction", "document", "resilience", "security",
        "validation", "monitoring", "infrastructure", "testing"
    ]

    for section in sections:
        if section in config_dict:
            section_config = getattr(config, section)
            for key, value in config_dict[section].items():
                if hasattr(section_config, key):
                    setattr(section_config, key, value)

    # Update global settings
    if "environment" in config_dict:
        config.environment = config_dict["environment"]
    if "debug_enabled" in config_dict:
        config.debug_enabled = config_dict["debug_enabled"]
    if "feature_flags" in config_dict:
        config.feature_flags.update(config_dict["feature_flags"])

    return config


def validate_enhanced_config(config: EnhancedConfig) -> None:
    """Validate enhanced configuration values."""
    errors = []

    # Validate resilience configuration
    if config.resilience.circuit_breaker_failure_threshold <= 0:
        errors.append("resilience.circuit_breaker_failure_threshold must be positive")
    if not 0.0 <= config.resilience.circuit_breaker_expected_failure_rate <= 1.0:
        errors.append("resilience.circuit_breaker_expected_failure_rate must be between 0.0 and 1.0")
    if config.resilience.retry_max_attempts <= 0:
        errors.append("resilience.retry_max_attempts must be positive")

    # Validate security configuration
    if config.security.max_file_size_mb <= 0:
        errors.append("security.max_file_size_mb must be positive")
    if config.security.rate_limit_requests_per_window <= 0:
        errors.append("security.rate_limit_requests_per_window must be positive")
    if config.security.jwt_expiration_hours <= 0:
        errors.append("security.jwt_expiration_hours must be positive")
    if config.security.min_password_length < 1:
        errors.append("security.min_password_length must be at least 1")

    # Validate validation configuration
    if config.validation.max_nesting_depth <= 0:
        errors.append("validation.max_nesting_depth must be positive")
    if config.validation.max_string_length <= 0:
        errors.append("validation.max_string_length must be positive")

    # Validate monitoring configuration
    valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if config.monitoring.log_level not in valid_log_levels:
        errors.append(f"monitoring.log_level must be one of {valid_log_levels}")
    if not 0 <= config.monitoring.metrics_port <= 65535:
        errors.append("monitoring.metrics_port must be between 0 and 65535")
    if not 0.0 <= config.monitoring.tracing_sample_rate <= 1.0:
        errors.append("monitoring.tracing_sample_rate must be between 0.0 and 1.0")

    # Validate infrastructure configuration
    if config.infrastructure.cache_max_size <= 0:
        errors.append("infrastructure.cache_max_size must be positive")
    if config.infrastructure.cache_ttl_seconds <= 0:
        errors.append("infrastructure.cache_ttl_seconds must be positive")
    if config.infrastructure.database_pool_size <= 0:
        errors.append("infrastructure.database_pool_size must be positive")

    # Validate testing configuration
    if config.testing.test_timeout_seconds <= 0:
        errors.append("testing.test_timeout_seconds must be positive")
    if config.testing.test_workers <= 0:
        errors.append("testing.test_workers must be positive")
    if not 0.0 <= config.testing.chaos_failure_rate <= 1.0:
        errors.append("testing.chaos_failure_rate must be between 0.0 and 1.0")

    if errors:
        raise EnhancedConfigValidationError(
            "Enhanced configuration validation failed:\n" +
            "\n".join(f"- {error}" for error in errors)
        )


def load_enhanced_config(config_path: Optional[str] = None, reload: bool = False) -> EnhancedConfig:
    """Load enhanced configuration from file and environment variables."""
    global _enhanced_config_instance

    # Return cached instance unless reload requested
    if _enhanced_config_instance is not None and not reload:
        return _enhanced_config_instance

    # Start with empty config dict
    configs_to_merge = []

    # Load from file if provided
    if config_path:
        try:
            file_config = _load_enhanced_from_file(config_path)
            configs_to_merge.append(file_config)
            logger.info(f"Loaded enhanced configuration from file: {config_path}")
        except FileNotFoundError:
            logger.warning(f"Enhanced configuration file not found: {config_path}, using defaults")
        except yaml.YAMLError as e:
            logger.exception(f"Failed to parse enhanced configuration file {config_path}: {e}")
            raise

    # Load from environment (always checked, takes precedence)
    env_config = _load_enhanced_from_environment()
    if env_config:
        configs_to_merge.append(env_config)
        logger.info("Applied enhanced configuration overrides from environment variables")

    # Merge all configuration sources
    if configs_to_merge:
        merged_config = _merge_enhanced_configs(*configs_to_merge)
        config = _create_enhanced_config_from_dict(merged_config)
    else:
        # Use all defaults
        config = EnhancedConfig()
        logger.info("Using default enhanced configuration values")

    # Validate the final configuration
    validate_enhanced_config(config)

    # Cache and return
    _enhanced_config_instance = config
    return config


def get_enhanced_config() -> EnhancedConfig:
    """Get the current enhanced configuration instance."""
    if _enhanced_config_instance is None:
        return load_enhanced_config()
    return _enhanced_config_instance


def reload_enhanced_config(config_path: Optional[str] = None) -> EnhancedConfig:
    """Reload enhanced configuration, clearing any cached instance."""
    return load_enhanced_config(config_path=config_path, reload=True)


def get_feature_flag(flag_name: str, default: bool = False) -> bool:
    """Get a feature flag value."""
    config = get_enhanced_config()
    return config.feature_flags.get(flag_name, default)


def set_feature_flag(flag_name: str, enabled: bool) -> None:
    """Set a feature flag value."""
    config = get_enhanced_config()
    config.feature_flags[flag_name] = enabled


# Backwards compatibility with base config
def get_config() -> BaseConfig:
    """Get base configuration for backwards compatibility."""
    enhanced = get_enhanced_config()

    # Create base config from enhanced config
    base = BaseConfig()
    base.ocr = enhanced.ocr
    base.extraction = enhanced.extraction
    base.document = enhanced.document

    # Map enhanced security to base security
    base.security.max_file_size_mb = enhanced.security.max_file_size_mb
    base.security.request_id_length_limit = enhanced.security.request_id_length_limit

    # Map enhanced health to base health (create simple health config)
    from dataclasses import dataclass

    @dataclass
    class SimpleHealthConfig:
        check_timeout_seconds: int = 5

    base.health = SimpleHealthConfig()

    return base


# Example enhanced configuration YAML
EXAMPLE_ENHANCED_CONFIG = """
# Enhanced Configuration for Multimodal Contract Extractor - Generation 2

# Generation 1 configurations
ocr:
  cache_size_limit: 100
  context_window_size: 100
  auto_detect_language: true
  default_language: "en"
  supported_languages: ["en", "es", "fr", "de", "ja", "zh", "zh-tw"]

extraction:
  base_confidence_score: 0.75
  length_bonus_divisor: 1000
  max_confidence_cap: 0.95
  file_size_threshold_mb: 10
  streaming_chunk_size: 5

document:
  default_streaming_chunk_size: 10

# Generation 2 configurations

resilience:
  circuit_breaker_enabled: true
  circuit_breaker_failure_threshold: 5
  circuit_breaker_recovery_timeout: 60.0
  retry_enabled: true
  retry_max_attempts: 3
  graceful_degradation_enabled: true

security:
  max_file_size_mb: 100
  virus_scanning_enabled: true
  rate_limiting_enabled: true
  jwt_enabled: true
  audit_logging_enabled: true
  encryption_enabled: true
  require_https: true

validation:
  schema_validation_enabled: true
  file_integrity_checks_enabled: true
  structure_validation_enabled: true
  corruption_detection_enabled: true

monitoring:
  structured_logging_enabled: true
  log_level: "INFO"
  metrics_enabled: true
  tracing_enabled: true
  alerting_enabled: true
  system_monitoring_enabled: true

infrastructure:
  caching_enabled: true
  cache_type: "memory"
  backup_enabled: true
  database_pooling_enabled: true
  health_monitoring_enabled: true

testing:
  security_tests_enabled: true
  performance_tests_enabled: true
  chaos_testing_enabled: false

# Global settings
environment: "production"
debug_enabled: false
feature_flags:
  advanced_ocr: true
  multi_language_support: true
  real_time_collaboration: true
"""


if __name__ == "__main__":
    # Example usage
    try:
        config = load_enhanced_config()
        print(f"Loaded enhanced configuration for environment: {config.environment}")
        print(f"Security features enabled: virus_scanning={config.security.virus_scanning_enabled}")
        print(f"Monitoring enabled: metrics={config.monitoring.metrics_enabled}")
        print(f"Infrastructure: caching={config.infrastructure.caching_enabled}")

        # Test feature flags
        set_feature_flag("test_feature", True)
        print(f"Test feature flag: {get_feature_flag('test_feature')}")

        # Backwards compatibility
        base_config = get_config()
        print(f"Base config OCR cache size: {base_config.ocr.cache_size_limit}")

    except Exception as e:
        print(f"Configuration error: {e}")
