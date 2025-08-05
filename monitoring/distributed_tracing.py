"""
Distributed tracing configuration for enhanced observability.
OpenTelemetry integration for comprehensive application monitoring.
"""

import functools
import logging
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional

try:
    # OpenTelemetry imports
    from opentelemetry import metrics, trace
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    from opentelemetry.exporter.prometheus import PrometheusMetricReader
    from opentelemetry.instrumentation.logging import LoggingInstrumentor
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.semconv.resource import ResourceAttributes

    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    # Fallback when OpenTelemetry is not available
    OPENTELEMETRY_AVAILABLE = False
    trace = None
    metrics = None


class TracingConfig:
    """Configuration for distributed tracing."""

    def __init__(self):
        self.service_name = os.getenv('SERVICE_NAME', 'multimodal-contract-extractor')
        self.service_version = os.getenv('SERVICE_VERSION', '0.1.0')
        self.environment = os.getenv('ENVIRONMENT', 'development')

        # Jaeger configuration
        self.jaeger_endpoint = os.getenv('JAEGER_ENDPOINT', 'http://localhost:14268/api/traces')
        self.jaeger_enabled = os.getenv('JAEGER_ENABLED', 'false').lower() == 'true'

        # Prometheus configuration
        self.prometheus_port = int(os.getenv('PROMETHEUS_PORT', '8888'))
        self.prometheus_enabled = os.getenv('PROMETHEUS_ENABLED', 'true').lower() == 'true'

        # Sampling configuration
        self.trace_sample_rate = float(os.getenv('TRACE_SAMPLE_RATE', '1.0'))

        # Feature flags
        self.enable_db_instrumentation = os.getenv('ENABLE_DB_INSTRUMENTATION', 'true').lower() == 'true'
        self.enable_http_instrumentation = os.getenv('ENABLE_HTTP_INSTRUMENTATION', 'true').lower() == 'true'
        self.enable_logging_instrumentation = os.getenv('ENABLE_LOGGING_INSTRUMENTATION', 'true').lower() == 'true'


class DistributedTracing:
    """Distributed tracing manager for enhanced observability."""

    def __init__(self, config: Optional[TracingConfig] = None):
        self.config = config or TracingConfig()
        self.tracer = None
        self.meter = None
        self.initialized = False

        # Metrics
        self.request_counter = None
        self.request_duration = None
        self.error_counter = None
        self.active_requests = None

        # Fallback logging when OpenTelemetry is not available
        self.logger = logging.getLogger(__name__)

    def initialize(self) -> bool:
        """Initialize distributed tracing."""
        if not OPENTELEMETRY_AVAILABLE:
            self.logger.warning("OpenTelemetry not available. Tracing disabled.")
            return False

        try:
            # Configure resource
            resource = Resource.create({
                ResourceAttributes.SERVICE_NAME: self.config.service_name,
                ResourceAttributes.SERVICE_VERSION: self.config.service_version,
                ResourceAttributes.DEPLOYMENT_ENVIRONMENT: self.config.environment,
            })

            # Configure tracing
            self._setup_tracing(resource)

            # Configure metrics
            self._setup_metrics(resource)

            # Setup instrumentation
            self._setup_instrumentation()

            self.initialized = True
            self.logger.info(f"Distributed tracing initialized for {self.config.service_name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize distributed tracing: {e}")
            return False

    def _setup_tracing(self, resource: 'Resource') -> None:
        """Setup tracing configuration."""
        # Create tracer provider
        tracer_provider = TracerProvider(resource=resource)

        # Add Jaeger exporter if enabled
        if self.config.jaeger_enabled:
            jaeger_exporter = JaegerExporter(
                collector_endpoint=self.config.jaeger_endpoint,
            )
            span_processor = BatchSpanProcessor(jaeger_exporter)
            tracer_provider.add_span_processor(span_processor)

        # Set global tracer provider
        trace.set_tracer_provider(tracer_provider)

        # Get tracer
        self.tracer = trace.get_tracer(__name__)

    def _setup_metrics(self, resource: 'Resource') -> None:
        """Setup metrics configuration."""
        readers = []

        # Add Prometheus reader if enabled
        if self.config.prometheus_enabled:
            prometheus_reader = PrometheusMetricReader()
            readers.append(prometheus_reader)

        # Create meter provider
        meter_provider = MeterProvider(resource=resource, metric_readers=readers)
        metrics.set_meter_provider(meter_provider)

        # Get meter
        self.meter = metrics.get_meter(__name__)

        # Create metrics instruments
        self.request_counter = self.meter.create_counter(
            name="requests_total",
            description="Total number of requests",
            unit="1"
        )

        self.request_duration = self.meter.create_histogram(
            name="request_duration_seconds",
            description="Request duration in seconds",
            unit="s"
        )

        self.error_counter = self.meter.create_counter(
            name="errors_total",
            description="Total number of errors",
            unit="1"
        )

        self.active_requests = self.meter.create_up_down_counter(
            name="active_requests",
            description="Number of active requests",
            unit="1"
        )

    def _setup_instrumentation(self) -> None:
        """Setup automatic instrumentation."""
        if self.config.enable_http_instrumentation:
            RequestsInstrumentor().instrument()

        if self.config.enable_logging_instrumentation:
            LoggingInstrumentor().instrument()

    def trace_operation(self, operation_name: str, attributes: Optional[Dict[str, Any]] = None):
        """Context manager for tracing operations."""
        if not self.initialized or not self.tracer:
            return self._fallback_context_manager(operation_name, attributes)

        return self.tracer.start_as_current_span(
            operation_name,
            attributes=attributes or {}
        )

    @contextmanager
    def _fallback_context_manager(self, operation_name: str, attributes: Optional[Dict[str, Any]] = None):
        """Fallback context manager when tracing is not available."""
        start_time = datetime.now(timezone.utc)
        self.logger.info(f"Starting operation: {operation_name}")

        try:
            yield None
        except Exception as e:
            self.logger.error(f"Operation {operation_name} failed: {e}")
            raise
        finally:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            self.logger.info(f"Completed operation: {operation_name} (took {duration:.3f}s)")

    def trace_function(self, operation_name: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None):
        """Decorator for tracing functions."""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                span_name = operation_name or f"{func.__module__}.{func.__name__}"
                span_attributes = attributes or {}

                # Add function metadata
                span_attributes.update({
                    'function.name': func.__name__,
                    'function.module': func.__module__,
                })

                with self.trace_operation(span_name, span_attributes):
                    # Record metrics
                    if self.request_counter:
                        self.request_counter.add(1, {'operation': span_name})

                    if self.active_requests:
                        self.active_requests.add(1, {'operation': span_name})

                    start_time = datetime.now(timezone.utc)

                    try:
                        result = func(*args, **kwargs)
                        return result
                    except Exception as e:
                        if self.error_counter:
                            self.error_counter.add(1, {
                                'operation': span_name,
                                'error_type': type(e).__name__
                            })
                        raise
                    finally:
                        duration = (datetime.now(timezone.utc) - start_time).total_seconds()

                        if self.request_duration:
                            self.request_duration.record(duration, {'operation': span_name})

                        if self.active_requests:
                            self.active_requests.add(-1, {'operation': span_name})

            return wrapper
        return decorator

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """Add an event to the current span."""
        if not self.initialized:
            self.logger.info(f"Event: {name} - {attributes}")
            return

        current_span = trace.get_current_span()
        if current_span:
            current_span.add_event(name, attributes or {})

    def set_attribute(self, key: str, value: Any) -> None:
        """Set an attribute on the current span."""
        if not self.initialized:
            self.logger.info(f"Attribute: {key} = {value}")
            return

        current_span = trace.get_current_span()
        if current_span:
            current_span.set_attribute(key, value)

    def record_exception(self, exception: Exception) -> None:
        """Record an exception in the current span."""
        if not self.initialized:
            self.logger.error(f"Exception: {exception}")
            return

        current_span = trace.get_current_span()
        if current_span:
            current_span.record_exception(exception)
            current_span.set_status(trace.Status(trace.StatusCode.ERROR, str(exception)))

    def get_trace_id(self) -> Optional[str]:
        """Get the current trace ID."""
        if not self.initialized:
            return None

        current_span = trace.get_current_span()
        if current_span:
            return format(current_span.get_span_context().trace_id, '032x')
        return None

    def shutdown(self) -> None:
        """Shutdown tracing providers."""
        if not self.initialized:
            return

        try:
            # Shutdown tracer provider
            tracer_provider = trace.get_tracer_provider()
            if hasattr(tracer_provider, 'shutdown'):
                tracer_provider.shutdown()

            # Shutdown meter provider
            meter_provider = metrics.get_meter_provider()
            if hasattr(meter_provider, 'shutdown'):
                meter_provider.shutdown()

            self.logger.info("Distributed tracing shutdown completed")
        except Exception as e:
            self.logger.error(f"Error during tracing shutdown: {e}")


# Global tracing instance
_tracing_instance: Optional[DistributedTracing] = None


def get_tracer() -> DistributedTracing:
    """Get the global tracing instance."""
    global _tracing_instance

    if _tracing_instance is None:
        _tracing_instance = DistributedTracing()
        _tracing_instance.initialize()

    return _tracing_instance


def trace_operation(operation_name: str, attributes: Optional[Dict[str, Any]] = None):
    """Context manager for tracing operations."""
    return get_tracer().trace_operation(operation_name, attributes)


def trace_function(operation_name: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None):
    """Decorator for tracing functions."""
    return get_tracer().trace_function(operation_name, attributes)


# Example usage and integration functions
@trace_function("document.processing")
def example_document_processing(document_path: str) -> Dict[str, Any]:
    """Example function with tracing."""
    tracer = get_tracer()

    # Add custom attributes
    tracer.set_attribute("document.path", document_path)
    tracer.set_attribute("document.size", os.path.getsize(document_path) if os.path.exists(document_path) else 0)

    # Add an event
    tracer.add_event("processing.started")

    try:
        # Simulate processing
        import time
        time.sleep(0.1)

        result = {
            "status": "success",
            "clauses_found": 5,
            "processing_time": 0.1
        }

        # Add result attributes
        tracer.set_attribute("result.clauses_found", result["clauses_found"])
        tracer.add_event("processing.completed", {"clauses_found": result["clauses_found"]})

        return result

    except Exception as e:
        tracer.record_exception(e)
        raise


# Application integration
def setup_application_tracing() -> DistributedTracing:
    """Setup tracing for the entire application."""
    config = TracingConfig()
    tracer = DistributedTracing(config)

    if tracer.initialize():
        # Register cleanup
        import atexit
        atexit.register(tracer.shutdown)

        return tracer

    return tracer  # Return even if initialization failed for fallback behavior


if __name__ == "__main__":
    # Example usage
    tracer = setup_application_tracing()

    # Test tracing
    with trace_operation("test.operation"):
        print("Testing distributed tracing...")

        # Test function decorator
        result = example_document_processing("/tmp/test.pdf")
        print(f"Result: {result}")

        # Test trace ID
        trace_id = tracer.get_trace_id()
        print(f"Trace ID: {trace_id}")

    print("Tracing test completed")
