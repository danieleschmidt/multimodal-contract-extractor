"""
Enhanced configuration management for Generation 3 scaling features.

This module extends the enhanced configuration with support for all Generation 3 features
including high-performance computing, distributed processing, advanced caching,
resource management, performance analytics, and enterprise integration.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# Import Generation 2 config if available
try:
    from .enhanced_config import EnhancedConfig as BaseEnhancedConfig
    GENERATION_2_CONFIG_AVAILABLE = True
except ImportError:
    from .config import Config as BaseEnhancedConfig
    GENERATION_2_CONFIG_AVAILABLE = False

logger = logging.getLogger(__name__)


class Generation3ConfigValidationError(Exception):
    """Raised when Generation 3 configuration validation fails."""


@dataclass
class HighPerformanceComputingConfig:
    """High-performance computing configuration."""

    # GPU acceleration
    enable_gpu: bool = False
    gpu_device_ids: List[int] = field(default_factory=list)
    gpu_memory_limit_mb: Optional[int] = None
    gpu_batch_size: int = 32

    # Parallel processing
    thread_pool_size: int = 8
    process_pool_size: int = 4
    worker_timeout_seconds: float = 300.0
    max_queue_size: int = 1000
    adaptive_pool_sizing: bool = True

    # Memory optimization
    memory_limit_mb: Optional[int] = None
    memory_warning_threshold: float = 0.8
    memory_critical_threshold: float = 0.9
    gc_optimization_enabled: bool = True

    # Streaming processing
    streaming_enabled: bool = True
    streaming_chunk_size: int = 1024 * 1024  # 1MB
    streaming_overlap_bytes: int = 1024  # 1KB
    streaming_memory_limit_mb: int = 512


@dataclass
class DistributedProcessingConfig:
    """Distributed processing configuration."""

    # Message queue settings
    enable_distributed: bool = False
    message_queue_type: str = "redis"  # redis, rabbitmq, inmemory
    message_queue_url: str = "redis://localhost:6379"
    queue_max_size: int = 10000

    # Task processing
    task_timeout_seconds: float = 300.0
    max_retries: int = 3
    retry_delay_seconds: float = 5.0

    # Load balancing
    load_balancing_strategy: str = "weighted"  # round_robin, least_loaded, weighted
    worker_health_check_interval: float = 30.0
    worker_heartbeat_timeout: float = 60.0

    # Scaling
    min_workers: int = 2
    max_workers: int = 20
    auto_scaling_enabled: bool = True
    scale_up_threshold: float = 0.8
    scale_down_threshold: float = 0.3


@dataclass
class AdvancedCachingConfig:
    """Advanced multi-level caching configuration."""

    # L1 Memory Cache
    l1_enabled: bool = True
    l1_max_size_mb: int = 128
    l1_max_entries: int = 10000
    l1_eviction_policy: str = "lru"  # lru, lfu, ttl, random, adaptive
    l1_default_ttl: Optional[float] = None

    # L2 Redis Cache
    l2_enabled: bool = False
    l2_redis_url: str = "redis://localhost:6379"
    l2_key_prefix: str = "mce_l2"
    l2_default_ttl: float = 3600.0  # 1 hour

    # L3 Persistent Cache
    l3_enabled: bool = True
    l3_cache_dir: str = "./cache/l3"
    l3_max_size_mb: int = 1024
    l3_cleanup_interval: float = 300.0  # 5 minutes

    # Cache warming
    cache_warming_enabled: bool = True
    cache_warming_strategies: List[str] = field(default_factory=lambda: ["pattern_based", "frequency_based"])

    # Analytics
    cache_analytics_enabled: bool = True
    cache_metrics_interval: float = 60.0


@dataclass
class ResourceManagementConfig:
    """Resource management and auto-scaling configuration."""

    # Resource monitoring
    monitoring_enabled: bool = True
    monitoring_interval: float = 5.0
    metrics_history_size: int = 100

    # Thresholds
    cpu_warning_threshold: float = 70.0
    cpu_critical_threshold: float = 90.0
    memory_warning_threshold: float = 75.0
    memory_critical_threshold: float = 90.0
    disk_warning_threshold: float = 80.0
    disk_critical_threshold: float = 95.0

    # Auto-scaling
    auto_scaling_enabled: bool = True
    auto_scaling_cooldown: float = 300.0  # 5 minutes
    auto_scaling_evaluation_window: int = 5  # minutes

    # Worker pool management
    initial_worker_pool_size: int = 4
    min_worker_pool_size: int = 2
    max_worker_pool_size: int = 20
    worker_pool_scale_increment: int = 2


@dataclass
class PerformanceAnalyticsConfig:
    """Performance analytics and optimization configuration."""

    # Metrics collection
    metrics_collection_enabled: bool = True
    metrics_collection_interval: float = 1.0
    metrics_retention_hours: int = 24

    # Performance profiling
    profiling_enabled: bool = True
    profiling_sample_rate: float = 0.1  # 10% of operations
    profiling_detailed_memory: bool = False

    # Bottleneck detection
    bottleneck_detection_enabled: bool = True
    bottleneck_detection_sensitivity: float = 0.7
    bottleneck_analysis_window: int = 10  # minutes

    # Automated optimization
    auto_optimization_enabled: bool = True
    optimization_interval: float = 300.0  # 5 minutes
    optimization_confidence_threshold: float = 0.8

    # Alerting
    performance_alerting_enabled: bool = True
    alert_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "high_latency": 5.0,  # seconds
        "low_throughput": 0.1,  # requests/second
        "high_error_rate": 0.1  # 10%
    })


@dataclass
class EnterpriseIntegrationConfig:
    """Enterprise integration configuration."""

    # SSO Configuration
    sso_enabled: bool = False
    sso_default_provider: str = "oauth2"
    sso_session_timeout: float = 3600.0  # 1 hour
    sso_providers: List[Dict[str, Any]] = field(default_factory=list)

    # API Gateway
    api_gateway_enabled: bool = False
    api_gateway_features: List[str] = field(default_factory=lambda: [
        "authentication", "rate_limiting", "logging"
    ])
    api_gateway_rate_limits: List[Dict[str, Any]] = field(default_factory=list)

    # Microservices
    microservices_enabled: bool = False
    service_registry_enabled: bool = False
    service_discovery_enabled: bool = False
    service_mesh_enabled: bool = False

    # Security
    enterprise_security_enabled: bool = False
    token_validation_strict: bool = True
    audit_logging_enabled: bool = True

    # Integration patterns
    circuit_breaker_enabled: bool = True
    bulkhead_pattern_enabled: bool = False
    timeout_pattern_enabled: bool = True


@dataclass
class TestingConfig:
    """Testing and quality assurance configuration."""

    # Performance testing
    performance_testing_enabled: bool = True
    load_testing_enabled: bool = False
    stress_testing_enabled: bool = False

    # Regression testing
    regression_testing_enabled: bool = True
    regression_baseline_path: Optional[str] = None
    regression_threshold: float = 0.1  # 10% performance degradation

    # Quality gates
    quality_gates_enabled: bool = True
    min_success_rate: float = 0.95  # 95%
    max_response_time: float = 5.0  # 5 seconds
    max_error_rate: float = 0.05  # 5%


@dataclass
class Generation3Config:
    """Complete Generation 3 configuration including all previous generations."""

    # Include all previous generation configs
    base_config: BaseEnhancedConfig = field(default_factory=BaseEnhancedConfig)

    # Generation 3 specific configs
    high_performance_computing: HighPerformanceComputingConfig = field(default_factory=HighPerformanceComputingConfig)
    distributed_processing: DistributedProcessingConfig = field(default_factory=DistributedProcessingConfig)
    advanced_caching: AdvancedCachingConfig = field(default_factory=AdvancedCachingConfig)
    resource_management: ResourceManagementConfig = field(default_factory=ResourceManagementConfig)
    performance_analytics: PerformanceAnalyticsConfig = field(default_factory=PerformanceAnalyticsConfig)
    enterprise_integration: EnterpriseIntegrationConfig = field(default_factory=EnterpriseIntegrationConfig)
    testing: TestingConfig = field(default_factory=TestingConfig)

    # Global Generation 3 settings
    generation_3_enabled: bool = True
    feature_flags: Dict[str, bool] = field(default_factory=lambda: {
        "gpu_acceleration": False,
        "distributed_processing": False,
        "advanced_caching": True,
        "auto_scaling": True,
        "performance_analytics": True,
        "enterprise_integration": False
    })

    # Environment settings
    environment: str = "development"  # development, staging, production
    debug_mode: bool = False
    log_level: str = "INFO"


# Global configuration instance
_generation3_config_instance: Optional[Generation3Config] = None


def _load_generation3_from_environment() -> Dict[str, Any]:
    """Load Generation 3 configuration overrides from environment variables."""
    env_config = {}

    # High-Performance Computing
    if val := os.getenv("MCE_G3_ENABLE_GPU"):
        env_config.setdefault("high_performance_computing", {})["enable_gpu"] = val.lower() in ("true", "1", "yes")
    if val := os.getenv("MCE_G3_THREAD_POOL_SIZE"):
        env_config.setdefault("high_performance_computing", {})["thread_pool_size"] = int(val)
    if val := os.getenv("MCE_G3_MEMORY_LIMIT_MB"):
        env_config.setdefault("high_performance_computing", {})["memory_limit_mb"] = int(val)

    # Distributed Processing
    if val := os.getenv("MCE_G3_ENABLE_DISTRIBUTED"):
        env_config.setdefault("distributed_processing", {})["enable_distributed"] = val.lower() in ("true", "1", "yes")
    if val := os.getenv("MCE_G3_MESSAGE_QUEUE_URL"):
        env_config.setdefault("distributed_processing", {})["message_queue_url"] = val
    if val := os.getenv("MCE_G3_MAX_WORKERS"):
        env_config.setdefault("distributed_processing", {})["max_workers"] = int(val)

    # Advanced Caching
    if val := os.getenv("MCE_G3_L1_CACHE_SIZE_MB"):
        env_config.setdefault("advanced_caching", {})["l1_max_size_mb"] = int(val)
    if val := os.getenv("MCE_G3_L2_REDIS_URL"):
        env_config.setdefault("advanced_caching", {})["l2_redis_url"] = val
        env_config.setdefault("advanced_caching", {})["l2_enabled"] = True
    if val := os.getenv("MCE_G3_L3_CACHE_SIZE_MB"):
        env_config.setdefault("advanced_caching", {})["l3_max_size_mb"] = int(val)

    # Resource Management
    if val := os.getenv("MCE_G3_ENABLE_AUTO_SCALING"):
        env_config.setdefault("resource_management", {})["auto_scaling_enabled"] = val.lower() in ("true", "1", "yes")
    if val := os.getenv("MCE_G3_MONITORING_INTERVAL"):
        env_config.setdefault("resource_management", {})["monitoring_interval"] = float(val)

    # Performance Analytics
    if val := os.getenv("MCE_G3_ENABLE_ANALYTICS"):
        env_config.setdefault("performance_analytics", {})["metrics_collection_enabled"] = val.lower() in ("true", "1", "yes")
    if val := os.getenv("MCE_G3_METRICS_INTERVAL"):
        env_config.setdefault("performance_analytics", {})["metrics_collection_interval"] = float(val)

    # Enterprise Integration
    if val := os.getenv("MCE_G3_ENABLE_SSO"):
        env_config.setdefault("enterprise_integration", {})["sso_enabled"] = val.lower() in ("true", "1", "yes")
    if val := os.getenv("MCE_G3_ENABLE_API_GATEWAY"):
        env_config.setdefault("enterprise_integration", {})["api_gateway_enabled"] = val.lower() in ("true", "1", "yes")

    # Global settings
    if val := os.getenv("MCE_G3_ENVIRONMENT"):
        env_config["environment"] = val
    if val := os.getenv("MCE_G3_DEBUG_MODE"):
        env_config["debug_mode"] = val.lower() in ("true", "1", "yes")
    if val := os.getenv("MCE_G3_LOG_LEVEL"):
        env_config["log_level"] = val.upper()

    return env_config


def _load_generation3_from_file(config_path: str) -> Dict[str, Any]:
    """Load Generation 3 configuration from YAML file."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Generation 3 configuration file not found: {config_path}")

    with open(path, encoding="utf-8") as f:
        try:
            return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Invalid YAML in Generation 3 config file {config_path}: {e}") from e


def _merge_generation3_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple Generation 3 configuration dictionaries."""
    merged = {}

    for config in configs:
        for section, values in config.items():
            if section not in merged:
                merged[section] = {}

            if isinstance(values, dict):
                if isinstance(merged[section], dict):
                    merged[section].update(values)
                else:
                    merged[section] = values
            else:
                merged[section] = values

    return merged


def _create_generation3_config_from_dict(config_dict: Dict[str, Any]) -> Generation3Config:
    """Create Generation3Config instance from dictionary."""

    # Create base config
    if GENERATION_2_CONFIG_AVAILABLE:
        # Use Generation 2 config as base
        base_config_data = config_dict.get("base_config", {})
        base_config = BaseEnhancedConfig()
        # Update base config from data (simplified)
    else:
        # Fallback to Generation 1 config
        base_config = BaseEnhancedConfig()

    # Create Generation 3 config
    config = Generation3Config(base_config=base_config)

    # Update High-Performance Computing config
    if "high_performance_computing" in config_dict:
        hpc_data = config_dict["high_performance_computing"]
        for key, value in hpc_data.items():
            if hasattr(config.high_performance_computing, key):
                setattr(config.high_performance_computing, key, value)

    # Update Distributed Processing config
    if "distributed_processing" in config_dict:
        dp_data = config_dict["distributed_processing"]
        for key, value in dp_data.items():
            if hasattr(config.distributed_processing, key):
                setattr(config.distributed_processing, key, value)

    # Update Advanced Caching config
    if "advanced_caching" in config_dict:
        ac_data = config_dict["advanced_caching"]
        for key, value in ac_data.items():
            if hasattr(config.advanced_caching, key):
                setattr(config.advanced_caching, key, value)

    # Update Resource Management config
    if "resource_management" in config_dict:
        rm_data = config_dict["resource_management"]
        for key, value in rm_data.items():
            if hasattr(config.resource_management, key):
                setattr(config.resource_management, key, value)

    # Update Performance Analytics config
    if "performance_analytics" in config_dict:
        pa_data = config_dict["performance_analytics"]
        for key, value in pa_data.items():
            if hasattr(config.performance_analytics, key):
                setattr(config.performance_analytics, key, value)

    # Update Enterprise Integration config
    if "enterprise_integration" in config_dict:
        ei_data = config_dict["enterprise_integration"]
        for key, value in ei_data.items():
            if hasattr(config.enterprise_integration, key):
                setattr(config.enterprise_integration, key, value)

    # Update Testing config
    if "testing" in config_dict:
        test_data = config_dict["testing"]
        for key, value in test_data.items():
            if hasattr(config.testing, key):
                setattr(config.testing, key, value)

    # Update global settings
    global_settings = ["generation_3_enabled", "environment", "debug_mode", "log_level"]
    for setting in global_settings:
        if setting in config_dict:
            setattr(config, setting, config_dict[setting])

    # Update feature flags
    if "feature_flags" in config_dict:
        config.feature_flags.update(config_dict["feature_flags"])

    return config


def validate_generation3_config(config: Generation3Config) -> None:
    """Validate Generation 3 configuration values."""
    errors = []

    # Validate High-Performance Computing
    hpc = config.high_performance_computing
    if hpc.thread_pool_size <= 0:
        errors.append("high_performance_computing.thread_pool_size must be positive")
    if hpc.process_pool_size <= 0:
        errors.append("high_performance_computing.process_pool_size must be positive")
    if hpc.memory_limit_mb is not None and hpc.memory_limit_mb <= 0:
        errors.append("high_performance_computing.memory_limit_mb must be positive if specified")

    # Validate Distributed Processing
    dp = config.distributed_processing
    if dp.enable_distributed:
        if not dp.message_queue_url:
            errors.append("distributed_processing.message_queue_url required when distributed processing is enabled")
        if dp.max_workers < dp.min_workers:
            errors.append("distributed_processing.max_workers must be >= min_workers")

    # Validate Advanced Caching
    ac = config.advanced_caching
    if ac.l1_max_size_mb <= 0:
        errors.append("advanced_caching.l1_max_size_mb must be positive")
    if ac.l3_max_size_mb <= 0:
        errors.append("advanced_caching.l3_max_size_mb must be positive")

    # Validate Resource Management
    rm = config.resource_management
    if rm.monitoring_interval <= 0:
        errors.append("resource_management.monitoring_interval must be positive")
    if rm.max_worker_pool_size < rm.min_worker_pool_size:
        errors.append("resource_management.max_worker_pool_size must be >= min_worker_pool_size")

    # Validate Performance Analytics
    pa = config.performance_analytics
    if pa.metrics_collection_interval <= 0:
        errors.append("performance_analytics.metrics_collection_interval must be positive")

    # Validate environment
    valid_environments = ["development", "staging", "production"]
    if config.environment not in valid_environments:
        errors.append(f"environment must be one of: {', '.join(valid_environments)}")

    if errors:
        raise Generation3ConfigValidationError(
            "Generation 3 configuration validation failed:\n" +
            "\n".join(f"- {error}" for error in errors)
        )


def load_generation3_config(config_path: Optional[str] = None, reload: bool = False) -> Generation3Config:
    """
    Load Generation 3 configuration from file and environment variables.
    
    Configuration is loaded in the following order (later sources override earlier ones):
    1. Default values (hardcoded in dataclasses)
    2. Configuration file (if provided)
    3. Environment variables (always checked)
    
    Args:
        config_path: Optional path to YAML configuration file
        reload: If True, reload configuration even if already loaded
        
    Returns:
        Configured Generation3Config instance
        
    Raises:
        Generation3ConfigValidationError: If configuration validation fails
        FileNotFoundError: If config_path is provided but file doesn't exist
        yaml.YAMLError: If the YAML file is malformed
    """
    global _generation3_config_instance

    # Return cached instance unless reload requested
    if _generation3_config_instance is not None and not reload:
        return _generation3_config_instance

    # Start with empty config dict (defaults come from dataclasses)
    configs_to_merge = []

    # Load from file if provided
    if config_path:
        try:
            file_config = _load_generation3_from_file(config_path)
            configs_to_merge.append(file_config)
            logger.info(f"Loaded Generation 3 configuration from file: {config_path}")
        except FileNotFoundError:
            logger.warning(f"Generation 3 config file not found: {config_path}, using defaults")
        except yaml.YAMLError as e:
            logger.exception(f"Failed to parse Generation 3 config file {config_path}: {e}")
            raise

    # Load from environment (always checked, takes precedence)
    env_config = _load_generation3_from_environment()
    if env_config:
        configs_to_merge.append(env_config)
        logger.info("Applied Generation 3 configuration overrides from environment variables")

    # Merge all configuration sources
    if configs_to_merge:
        merged_config = _merge_generation3_configs(*configs_to_merge)
        config = _create_generation3_config_from_dict(merged_config)
    else:
        # Use all defaults
        config = Generation3Config()
        logger.info("Using default Generation 3 configuration values")

    # Validate the final configuration
    validate_generation3_config(config)

    # Cache and return
    _generation3_config_instance = config
    return config


def get_generation3_config() -> Generation3Config:
    """
    Get the current Generation 3 configuration instance.
    
    If no configuration has been loaded yet, loads with default values.
    
    Returns:
        Current Generation3Config instance
    """
    if _generation3_config_instance is None:
        return load_generation3_config()
    return _generation3_config_instance


def reload_generation3_config(config_path: Optional[str] = None) -> Generation3Config:
    """
    Reload Generation 3 configuration, clearing any cached instance.
    
    Args:
        config_path: Optional path to YAML configuration file
        
    Returns:
        Newly loaded Generation3Config instance
    """
    return load_generation3_config(config_path=config_path, reload=True)


def get_generation3_feature_flag(flag_name: str) -> bool:
    """
    Get the value of a Generation 3 feature flag.
    
    Args:
        flag_name: Name of the feature flag
        
    Returns:
        Boolean value of the feature flag
    """
    config = get_generation3_config()
    return config.feature_flags.get(flag_name, False)


def set_generation3_feature_flag(flag_name: str, enabled: bool) -> None:
    """
    Set the value of a Generation 3 feature flag.
    
    Args:
        flag_name: Name of the feature flag
        enabled: Whether to enable the feature
    """
    config = get_generation3_config()
    config.feature_flags[flag_name] = enabled
    logger.info(f"Generation 3 feature flag '{flag_name}' set to {enabled}")


def create_example_generation3_config() -> str:
    """
    Create an example Generation 3 configuration file content.
    
    Returns:
        YAML configuration file content as string
    """

    example_config = {
        "generation_3_enabled": True,
        "environment": "development",
        "debug_mode": False,
        "log_level": "INFO",

        "feature_flags": {
            "gpu_acceleration": False,
            "distributed_processing": False,
            "advanced_caching": True,
            "auto_scaling": True,
            "performance_analytics": True,
            "enterprise_integration": False
        },

        "high_performance_computing": {
            "enable_gpu": False,
            "thread_pool_size": 8,
            "process_pool_size": 4,
            "memory_limit_mb": 2048,
            "streaming_enabled": True,
            "streaming_chunk_size": 1048576  # 1MB
        },

        "distributed_processing": {
            "enable_distributed": False,
            "message_queue_type": "redis",
            "message_queue_url": "redis://localhost:6379",
            "max_workers": 10,
            "auto_scaling_enabled": True
        },

        "advanced_caching": {
            "l1_enabled": True,
            "l1_max_size_mb": 128,
            "l1_eviction_policy": "lru",
            "l2_enabled": False,
            "l2_redis_url": "redis://localhost:6379",
            "l3_enabled": True,
            "l3_max_size_mb": 1024,
            "cache_warming_enabled": True
        },

        "resource_management": {
            "monitoring_enabled": True,
            "monitoring_interval": 5.0,
            "auto_scaling_enabled": True,
            "cpu_warning_threshold": 70.0,
            "memory_warning_threshold": 75.0,
            "initial_worker_pool_size": 4
        },

        "performance_analytics": {
            "metrics_collection_enabled": True,
            "metrics_collection_interval": 1.0,
            "bottleneck_detection_enabled": True,
            "auto_optimization_enabled": True,
            "performance_alerting_enabled": True
        },

        "enterprise_integration": {
            "sso_enabled": False,
            "api_gateway_enabled": False,
            "microservices_enabled": False,
            "enterprise_security_enabled": False
        },

        "testing": {
            "performance_testing_enabled": True,
            "regression_testing_enabled": True,
            "quality_gates_enabled": True,
            "min_success_rate": 0.95,
            "max_response_time": 5.0
        }
    }

    return yaml.dump(example_config, default_flow_style=False, indent=2)
