"""
Enterprise Reliability Integration Module

Central integration point for all enterprise reliability components:
- Error Handling and Recovery
- Monitoring and Observability
- Security and Compliance
- Health Checks and Self-Healing
- Logging and Analytics

This module provides a unified interface for initializing, configuring,
and coordinating all reliability systems.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from .enhanced_enterprise_security import (
    SecurityContext,
    get_enhanced_security_manager,
)
from .enterprise_error_handling import (
    ComponentType,
    get_error_recovery_manager,
)
from .enterprise_health_recovery import (
    get_health_recovery_system,
)
from .enterprise_logging_analytics import (
    EventCategory,
    LogLevel,
    get_logging_analytics_system,
)
from .enterprise_monitoring import get_monitoring_system

logger = logging.getLogger(__name__)


class ReliabilityLevel(Enum):
    """Reliability configuration levels."""

    BASIC = "basic"
    STANDARD = "standard"
    HIGH = "high"
    CRITICAL = "critical"


class DeploymentEnvironment(Enum):
    """Deployment environment types."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class ReliabilityConfiguration:
    """Configuration for enterprise reliability systems."""

    # General settings
    reliability_level: ReliabilityLevel = ReliabilityLevel.STANDARD
    environment: DeploymentEnvironment = DeploymentEnvironment.DEVELOPMENT

    # Error handling configuration
    circuit_breaker_enabled: bool = True
    max_retry_attempts: int = 3
    retry_backoff_multiplier: float = 2.0
    auto_recovery_enabled: bool = True

    # Monitoring configuration
    monitoring_enabled: bool = True
    metrics_collection_interval: float = 30.0
    performance_anomaly_detection: bool = True
    alert_thresholds: Dict[str, float] = field(default_factory=lambda: {
        'cpu_usage_warning': 80.0,
        'cpu_usage_critical': 90.0,
        'memory_usage_warning': 85.0,
        'memory_usage_critical': 95.0,
        'error_rate_warning': 0.05,
        'error_rate_critical': 0.10
    })

    # Security configuration
    security_enabled: bool = True
    encryption_enabled: bool = True
    audit_logging_enabled: bool = True
    key_rotation_interval: float = 86400.0  # 24 hours

    # Health check configuration
    health_checks_enabled: bool = True
    health_check_interval: float = 60.0
    self_healing_enabled: bool = True
    chaos_engineering_enabled: bool = False

    # Logging configuration
    structured_logging_enabled: bool = True
    log_level: LogLevel = LogLevel.INFO
    log_file_rotation_size_mb: int = 100
    log_retention_days: int = 30
    analytics_enabled: bool = True

    # Research-specific configuration
    experiment_tracking_enabled: bool = True
    algorithm_performance_monitoring: bool = True
    research_data_encryption: bool = True


class EnterpriseReliabilityManager:
    """Central manager for all enterprise reliability components."""

    def __init__(self, config: Optional[ReliabilityConfiguration] = None):
        self.config = config or ReliabilityConfiguration()
        self._initialized = False
        self._running = False

        # Get component instances
        self.error_manager = get_error_recovery_manager()
        self.monitoring_system = get_monitoring_system()
        self.security_manager = get_enhanced_security_manager()
        self.health_system = get_health_recovery_system()
        self.logging_system = get_logging_analytics_system()

        # Integration state
        self._startup_tasks: List[Callable] = []
        self._shutdown_tasks: List[Callable] = []
        self._health_callbacks: List[Callable] = []
        self._lock = threading.Lock()

    async def initialize(self):
        """Initialize all reliability systems."""
        if self._initialized:
            logger.warning("Reliability manager already initialized")
            return

        logger.info(f"Initializing enterprise reliability systems (level: {self.config.reliability_level.value})")

        try:
            # Configure systems based on configuration
            await self._configure_error_handling()
            await self._configure_monitoring()
            await self._configure_security()
            await self._configure_health_system()
            await self._configure_logging()

            # Set up integration points
            await self._setup_integrations()

            self._initialized = True
            logger.info("Enterprise reliability systems initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize reliability systems: {e}")
            raise

    async def start(self):
        """Start all reliability systems."""
        if not self._initialized:
            await self.initialize()

        if self._running:
            logger.warning("Reliability systems already running")
            return

        logger.info("Starting enterprise reliability systems")

        try:
            # Start systems in order
            if self.config.monitoring_enabled:
                await self.monitoring_system.start_monitoring(
                    collection_interval=self.config.metrics_collection_interval
                )

            if self.config.health_checks_enabled:
                await self.health_system.start_monitoring()

            if self.config.analytics_enabled:
                await self.logging_system.start_analytics()

            # Run startup tasks
            for task in self._startup_tasks:
                await task()

            self._running = True

            # Log startup completion
            self.logging_system.structured_logger.info(
                "Enterprise reliability systems started",
                category=EventCategory.SYSTEM,
                context_data={
                    'reliability_level': self.config.reliability_level.value,
                    'environment': self.config.environment.value,
                    'monitoring_enabled': self.config.monitoring_enabled,
                    'security_enabled': self.config.security_enabled,
                    'health_checks_enabled': self.config.health_checks_enabled
                }
            )

            logger.info("Enterprise reliability systems started successfully")

        except Exception as e:
            logger.error(f"Failed to start reliability systems: {e}")
            raise

    async def stop(self):
        """Stop all reliability systems gracefully."""
        if not self._running:
            logger.warning("Reliability systems not running")
            return

        logger.info("Stopping enterprise reliability systems")

        try:
            # Run shutdown tasks
            for task in self._shutdown_tasks:
                try:
                    await task()
                except Exception as e:
                    logger.error(f"Error in shutdown task: {e}")

            # Stop systems in reverse order
            if self.config.analytics_enabled:
                await self.logging_system.stop_analytics()

            if self.config.health_checks_enabled:
                await self.health_system.stop_monitoring()

            if self.config.monitoring_enabled:
                await self.monitoring_system.stop_monitoring()

            self._running = False
            logger.info("Enterprise reliability systems stopped")

        except Exception as e:
            logger.error(f"Error stopping reliability systems: {e}")
            raise

    async def _configure_error_handling(self):
        """Configure error handling system."""
        logger.debug("Configuring error handling system")

        # Configure circuit breakers based on reliability level
        if self.config.reliability_level in [ReliabilityLevel.HIGH, ReliabilityLevel.CRITICAL]:
            # More aggressive circuit breaker settings for high reliability
            for circuit_name, circuit_breaker in self.error_manager.circuit_breakers.items():
                circuit_breaker.failure_threshold = 2  # Lower threshold
                circuit_breaker.recovery_timeout = 30.0  # Faster recovery

        # Configure auto-recovery
        self.error_manager.self_healing.auto_recovery_enabled = self.config.auto_recovery_enabled

        logger.debug("Error handling system configured")

    async def _configure_monitoring(self):
        """Configure monitoring system."""
        logger.debug("Configuring monitoring system")

        # Configure alert thresholds based on environment
        if self.config.environment == DeploymentEnvironment.PRODUCTION:
            # Stricter thresholds for production
            alert_manager = self.monitoring_system.alert_manager

            for rule_name, rule in alert_manager.alert_rules.items():
                if 'cpu_usage' in rule_name:
                    rule.threshold = self.config.alert_thresholds.get('cpu_usage_critical', 90.0)
                elif 'memory_usage' in rule_name:
                    rule.threshold = self.config.alert_thresholds.get('memory_usage_critical', 95.0)
                elif 'error_rate' in rule_name:
                    rule.threshold = self.config.alert_thresholds.get('error_rate_critical', 0.10)

        logger.debug("Monitoring system configured")

    async def _configure_security(self):
        """Configure security system."""
        logger.debug("Configuring security system")

        if not self.config.security_enabled:
            logger.warning("Security is disabled - not recommended for production")
            return

        # Configure key rotation based on environment
        if self.config.environment == DeploymentEnvironment.PRODUCTION:
            # More frequent key rotation in production
            for component, config in self.security_manager.encryption_manager.algorithm_encryption_configs.items():
                config['rotation_interval'] = self.config.key_rotation_interval

        logger.debug("Security system configured")

    async def _configure_health_system(self):
        """Configure health monitoring system."""
        logger.debug("Configuring health system")

        # Configure chaos engineering based on environment
        if self.config.environment in [DeploymentEnvironment.DEVELOPMENT, DeploymentEnvironment.TESTING]:
            self.health_system.chaos_engineering.safety_enabled = True
        else:
            # Disable chaos engineering in production unless explicitly enabled
            self.health_system.chaos_engineering.safety_enabled = self.config.chaos_engineering_enabled

        # Configure self-healing
        self.health_system.self_healing.auto_recovery_enabled = self.config.self_healing_enabled

        logger.debug("Health system configured")

    async def _configure_logging(self):
        """Configure logging and analytics system."""
        logger.debug("Configuring logging system")

        # Configure log rotation
        self.logging_system.structured_logger.rotation_size_mb = self.config.log_file_rotation_size_mb

        # Configure analytics based on environment
        if self.config.environment == DeploymentEnvironment.PRODUCTION:
            # More comprehensive analytics in production
            self.logging_system.analytics_enabled = self.config.analytics_enabled

        logger.debug("Logging system configured")

    async def _setup_integrations(self):
        """Set up integrations between different systems."""
        logger.debug("Setting up system integrations")

        # Error handling -> Monitoring integration
        self._setup_error_monitoring_integration()

        # Health -> Recovery integration
        self._setup_health_recovery_integration()

        # Security -> Audit logging integration
        self._setup_security_logging_integration()

        # Monitoring -> Alerting integration
        self._setup_monitoring_alerting_integration()

        logger.debug("System integrations configured")

    def _setup_error_monitoring_integration(self):
        """Integrate error handling with monitoring."""
        # Errors are automatically recorded in monitoring via the error analytics system
        pass

    def _setup_health_recovery_integration(self):
        """Integrate health monitoring with automatic recovery."""
        # Health checks automatically trigger recovery when unhealthy states are detected
        pass

    def _setup_security_logging_integration(self):
        """Integrate security events with audit logging."""
        # Security events are automatically logged via the audit logger
        pass

    def _setup_monitoring_alerting_integration(self):
        """Integrate monitoring with alerting systems."""
        # Monitoring automatically evaluates alert rules and triggers notifications
        pass

    def register_startup_task(self, task: Callable):
        """Register a task to run during startup."""
        self._startup_tasks.append(task)

    def register_shutdown_task(self, task: Callable):
        """Register a task to run during shutdown."""
        self._shutdown_tasks.append(task)

    def register_health_callback(self, callback: Callable):
        """Register a callback for health status changes."""
        self._health_callbacks.append(callback)

    async def execute_algorithm_with_full_reliability(
        self,
        algorithm_func: Callable,
        algorithm_name: str,
        component: ComponentType,
        security_context: SecurityContext,
        input_data: Dict[str, Any],
        required_permission: str = "execute_research"
    ) -> Dict[str, Any]:
        """Execute an algorithm with full reliability features enabled."""

        # Start experiment tracking
        experiment_id = None
        if self.config.experiment_tracking_enabled:
            experiment_id = self.logging_system.research_tracker.start_experiment(
                algorithm_name=algorithm_name,
                parameters=input_data.copy(),
                tags={'reliability_managed': 'true'}
            )

        try:
            # Execute with security, monitoring, and error recovery
            async with self.security_manager.secure_operation(
                security_context,
                component,
                f"execute_{algorithm_name}",
                algorithm_name,
                required_permission
            ):
                # Execute with error recovery
                result = await self.error_manager.execute_with_recovery(
                    algorithm_func,
                    component,
                    f"execute_{algorithm_name}",
                    input_data,
                    max_attempts=self.config.max_retry_attempts
                )

                # Record performance metrics
                if self.config.algorithm_performance_monitoring and isinstance(result, dict):
                    self.monitoring_system.record_algorithm_metrics(
                        algorithm_name=algorithm_name,
                        execution_time=result.get('execution_time', 0.0),
                        throughput=result.get('throughput', 0.0),
                        accuracy=result.get('accuracy', 0.0),
                        confidence=result.get('confidence', 0.0),
                        resource_usage=result.get('resource_usage', {}),
                        error_count=0,
                        success_count=1
                    )

                # Update experiment
                if experiment_id and isinstance(result, dict):
                    self.logging_system.research_tracker.update_experiment_metrics(
                        experiment_id,
                        metrics=result.get('metrics', {}),
                        results=result.get('results', {})
                    )

                # Log successful execution
                self.logging_system.structured_logger.research(
                    f"Algorithm {algorithm_name} executed successfully with full reliability",
                    algorithm_name=algorithm_name,
                    experiment_id=experiment_id,
                    component=component,
                    accuracy=result.get('accuracy') if isinstance(result, dict) else None,
                    confidence=result.get('confidence') if isinstance(result, dict) else None
                )

                return result

        except Exception as e:
            # Record error metrics
            if self.config.monitoring_enabled:
                self.monitoring_system.record_algorithm_metrics(
                    algorithm_name=algorithm_name,
                    execution_time=0.0,
                    throughput=0.0,
                    accuracy=0.0,
                    confidence=0.0,
                    resource_usage={},
                    error_count=1,
                    success_count=0
                )

            # Log error
            self.logging_system.structured_logger.error(
                f"Algorithm {algorithm_name} failed",
                error=e,
                algorithm_name=algorithm_name,
                experiment_id=experiment_id,
                component=component
            )

            # Mark experiment as failed
            if experiment_id:
                self.logging_system.research_tracker.finish_experiment(
                    experiment_id,
                    status="failed",
                    notes=f"Failed with error: {str(e)}"
                )

            raise

        finally:
            # Finish experiment if it's still running
            if experiment_id:
                try:
                    # Try to finish the experiment if not already finished
                    self.logging_system.research_tracker.finish_experiment(
                        experiment_id,
                        status="completed"
                    )
                except:
                    # Experiment might already be finished
                    pass

    async def get_comprehensive_system_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all reliability systems."""
        status = {
            'timestamp': time.time(),
            'reliability_level': self.config.reliability_level.value,
            'environment': self.config.environment.value,
            'initialized': self._initialized,
            'running': self._running
        }

        if not self._running:
            return status

        try:
            # Error handling status
            if self.config.circuit_breaker_enabled:
                status['error_handling'] = self.error_manager.get_error_statistics()

            # Monitoring status
            if self.config.monitoring_enabled:
                status['monitoring'] = self.monitoring_system.get_dashboard_data()

            # Security status
            if self.config.security_enabled:
                status['security'] = await self.security_manager.security_health_check()

            # Health system status
            if self.config.health_checks_enabled:
                status['health'] = self.health_system.get_system_health_summary()

            # Logging and analytics status
            if self.config.analytics_enabled:
                status['analytics'] = self.logging_system.get_comprehensive_analytics_dashboard()

        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            status['error'] = str(e)

        return status

    async def perform_comprehensive_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check across all systems."""
        health_check_result = {
            'timestamp': time.time(),
            'overall_status': 'healthy',
            'systems': {}
        }

        try:
            # Check error handling system
            error_stats = self.error_manager.get_error_statistics()
            error_health = 'healthy'
            if error_stats.get('recent_errors_24h', 0) > 100:
                error_health = 'degraded'
            if any(cb_state == 'open' for cb_state in error_stats.get('circuit_breaker_states', {}).values()):
                error_health = 'unhealthy'

            health_check_result['systems']['error_handling'] = {
                'status': error_health,
                'details': error_stats
            }

            # Check monitoring system
            monitoring_health = await self.monitoring_system.health_check()
            health_check_result['systems']['monitoring'] = monitoring_health

            # Check security system
            security_health = await self.security_manager.security_health_check()
            health_check_result['systems']['security'] = security_health

            # Check health system
            health_summary = self.health_system.get_system_health_summary()
            health_check_result['systems']['health'] = {
                'status': health_summary['overall_status'],
                'details': health_summary
            }

            # Determine overall status
            system_statuses = [
                health_check_result['systems']['error_handling']['status'],
                monitoring_health.get('status', 'unknown'),
                security_health.get('security_status', 'unknown'),
                health_summary['overall_status']
            ]

            if 'critical' in system_statuses:
                health_check_result['overall_status'] = 'critical'
            elif 'unhealthy' in system_statuses:
                health_check_result['overall_status'] = 'unhealthy'
            elif 'degraded' in system_statuses:
                health_check_result['overall_status'] = 'degraded'
            else:
                health_check_result['overall_status'] = 'healthy'

        except Exception as e:
            logger.error(f"Error in comprehensive health check: {e}")
            health_check_result['overall_status'] = 'error'
            health_check_result['error'] = str(e)

        return health_check_result

    def get_configuration(self) -> ReliabilityConfiguration:
        """Get current configuration."""
        return self.config

    async def update_configuration(self, new_config: ReliabilityConfiguration):
        """Update configuration (requires restart for some changes)."""
        logger.info("Updating reliability configuration")

        # Store old config for comparison
        old_config = self.config
        self.config = new_config

        # Apply changes that can be made without restart
        if old_config.auto_recovery_enabled != new_config.auto_recovery_enabled:
            self.error_manager.self_healing.auto_recovery_enabled = new_config.auto_recovery_enabled

        if old_config.self_healing_enabled != new_config.self_healing_enabled:
            self.health_system.self_healing.auto_recovery_enabled = new_config.self_healing_enabled

        # Log configuration change
        self.logging_system.structured_logger.info(
            "Reliability configuration updated",
            category=EventCategory.SYSTEM,
            context_data={
                'old_reliability_level': old_config.reliability_level.value,
                'new_reliability_level': new_config.reliability_level.value,
                'requires_restart': old_config.environment != new_config.environment
            }
        )

        logger.info("Reliability configuration updated")


# Global reliability manager instance
_reliability_manager: Optional[EnterpriseReliabilityManager] = None
_manager_lock = threading.Lock()


def get_reliability_manager() -> EnterpriseReliabilityManager:
    """Get the global reliability manager instance."""
    global _reliability_manager

    with _manager_lock:
        if _reliability_manager is None:
            _reliability_manager = EnterpriseReliabilityManager()

    return _reliability_manager


def initialize_reliability_manager(config: Optional[ReliabilityConfiguration] = None) -> EnterpriseReliabilityManager:
    """Initialize the global reliability manager with configuration."""
    global _reliability_manager

    with _manager_lock:
        if _reliability_manager is not None:
            logger.warning("Reliability manager already exists, replacing with new configuration")

        _reliability_manager = EnterpriseReliabilityManager(config)

    return _reliability_manager


# Convenience functions for easy integration
async def start_enterprise_reliability(config: Optional[ReliabilityConfiguration] = None):
    """Start enterprise reliability systems with optional configuration."""
    manager = initialize_reliability_manager(config)
    await manager.start()
    return manager


async def stop_enterprise_reliability():
    """Stop enterprise reliability systems."""
    manager = get_reliability_manager()
    await manager.stop()


async def execute_with_full_reliability(
    algorithm_func: Callable,
    algorithm_name: str,
    component: ComponentType,
    security_context: SecurityContext,
    input_data: Dict[str, Any],
    required_permission: str = "execute_research"
) -> Dict[str, Any]:
    """Execute algorithm with full enterprise reliability features."""
    manager = get_reliability_manager()
    return await manager.execute_algorithm_with_full_reliability(
        algorithm_func,
        algorithm_name,
        component,
        security_context,
        input_data,
        required_permission
    )


async def get_system_status() -> Dict[str, Any]:
    """Get comprehensive system status."""
    manager = get_reliability_manager()
    return await manager.get_comprehensive_system_status()


async def perform_health_check() -> Dict[str, Any]:
    """Perform comprehensive health check."""
    manager = get_reliability_manager()
    return await manager.perform_comprehensive_health_check()


# Configuration presets
DEVELOPMENT_CONFIG = ReliabilityConfiguration(
    reliability_level=ReliabilityLevel.BASIC,
    environment=DeploymentEnvironment.DEVELOPMENT,
    circuit_breaker_enabled=False,
    chaos_engineering_enabled=True,
    security_enabled=True,
    encryption_enabled=False,  # Simplified for development
    log_level=LogLevel.DEBUG
)

TESTING_CONFIG = ReliabilityConfiguration(
    reliability_level=ReliabilityLevel.STANDARD,
    environment=DeploymentEnvironment.TESTING,
    circuit_breaker_enabled=True,
    chaos_engineering_enabled=True,
    security_enabled=True,
    encryption_enabled=True,
    log_level=LogLevel.INFO
)

PRODUCTION_CONFIG = ReliabilityConfiguration(
    reliability_level=ReliabilityLevel.HIGH,
    environment=DeploymentEnvironment.PRODUCTION,
    circuit_breaker_enabled=True,
    max_retry_attempts=5,
    auto_recovery_enabled=True,
    monitoring_enabled=True,
    metrics_collection_interval=15.0,  # More frequent in production
    security_enabled=True,
    encryption_enabled=True,
    audit_logging_enabled=True,
    health_checks_enabled=True,
    health_check_interval=30.0,  # More frequent health checks
    self_healing_enabled=True,
    chaos_engineering_enabled=False,  # Disabled in production
    analytics_enabled=True,
    log_level=LogLevel.WARNING  # Less verbose in production
)
