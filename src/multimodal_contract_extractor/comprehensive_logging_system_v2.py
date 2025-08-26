#!/usr/bin/env python3
"""
Comprehensive Logging System v2.0 - Generation 2: MAKE IT ROBUST
Advanced enterprise-grade logging with structured logging, log aggregation,
real-time monitoring, and intelligent log analysis for the autonomous SDLC system.
"""

import asyncio
import json
import logging
import logging.handlers
import time
import traceback
import threading
from typing import Dict, List, Any, Optional, Union, Callable, TextIO
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from datetime import datetime, timedelta
from pathlib import Path
import queue
import sys
import os
from contextlib import contextmanager
import hashlib
import gzip
import shutil


class LogLevel(Enum):
    """Extended log levels"""
    TRACE = 5
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50
    SECURITY = 60
    BUSINESS = 70


class LogCategory(Enum):
    """Log categories for classification"""
    APPLICATION = auto()
    SECURITY = auto()
    PERFORMANCE = auto()
    BUSINESS = auto()
    SYSTEM = auto()
    AUDIT = auto()
    DEBUG = auto()
    INTEGRATION = auto()


class LogDestination(Enum):
    """Log output destinations"""
    FILE = auto()
    CONSOLE = auto()
    SYSLOG = auto()
    DATABASE = auto()
    ELASTICSEARCH = auto()
    KAFKA = auto()
    WEBHOOK = auto()


@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: datetime
    level: LogLevel
    category: LogCategory
    logger_name: str
    message: str
    module: str
    function: str
    line_number: int
    thread_id: str
    process_id: int
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    exception: Optional[str] = None
    stack_trace: Optional[str] = None
    duration_ms: Optional[float] = None
    
    def to_json(self) -> str:
        """Convert log entry to JSON string"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['level'] = self.level.name
        data['category'] = self.category.name
        return json.dumps(data, default=str)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert log entry to dictionary"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['level'] = self.level.name
        data['category'] = self.category.name
        return data


@dataclass
class LoggingConfig:
    """Logging system configuration"""
    log_level: LogLevel = LogLevel.INFO
    enable_console: bool = True
    enable_file: bool = True
    log_directory: str = "logs"
    log_file_name: str = "application.log"
    max_file_size_mb: int = 100
    backup_count: int = 10
    enable_compression: bool = True
    enable_structured_logging: bool = True
    enable_async_logging: bool = True
    buffer_size: int = 1000
    flush_interval: float = 5.0
    enable_log_sampling: bool = False
    sampling_rate: float = 1.0
    destinations: List[LogDestination] = field(default_factory=lambda: [LogDestination.FILE, LogDestination.CONSOLE])


class LogBuffer:
    """Thread-safe log buffer for async logging"""
    
    def __init__(self, max_size: int = 1000):
        self.buffer = queue.Queue(maxsize=max_size)
        self.max_size = max_size
        self._lock = threading.Lock()
        self._dropped_count = 0
    
    def add(self, entry: LogEntry) -> bool:
        """Add log entry to buffer"""
        try:
            self.buffer.put_nowait(entry)
            return True
        except queue.Full:
            with self._lock:
                self._dropped_count += 1
            return False
    
    def get_batch(self, batch_size: int = 100, timeout: float = 1.0) -> List[LogEntry]:
        """Get batch of log entries"""
        entries = []
        start_time = time.time()
        
        while len(entries) < batch_size and (time.time() - start_time) < timeout:
            try:
                entry = self.buffer.get_nowait()
                entries.append(entry)
            except queue.Empty:
                if entries:  # Return partial batch if we have some entries
                    break
                time.sleep(0.01)  # Short sleep to avoid busy waiting
        
        return entries
    
    def size(self) -> int:
        """Get current buffer size"""
        return self.buffer.qsize()
    
    def dropped_count(self) -> int:
        """Get count of dropped log entries"""
        with self._lock:
            return self._dropped_count


class LogFormatter:
    """Advanced log formatter with multiple output formats"""
    
    def __init__(self, format_type: str = "json"):
        self.format_type = format_type
        self.sensitive_fields = {'password', 'token', 'key', 'secret', 'auth'}
    
    def format(self, entry: LogEntry) -> str:
        """Format log entry based on configured format"""
        if self.format_type == "json":
            return self._format_json(entry)
        elif self.format_type == "structured":
            return self._format_structured(entry)
        else:
            return self._format_plain(entry)
    
    def _format_json(self, entry: LogEntry) -> str:
        """Format as JSON"""
        return entry.to_json()
    
    def _format_structured(self, entry: LogEntry) -> str:
        """Format as key-value pairs"""
        parts = [
            f"timestamp={entry.timestamp.isoformat()}",
            f"level={entry.level.name}",
            f"category={entry.category.name}",
            f"logger={entry.logger_name}",
            f"message='{entry.message}'",
            f"module={entry.module}",
            f"function={entry.function}:{entry.line_number}"
        ]
        
        if entry.user_id:
            parts.append(f"user_id={entry.user_id}")
        if entry.request_id:
            parts.append(f"request_id={entry.request_id}")
        if entry.duration_ms:
            parts.append(f"duration_ms={entry.duration_ms}")
        
        return " ".join(parts)
    
    def _format_plain(self, entry: LogEntry) -> str:
        """Format as plain text"""
        return f"[{entry.timestamp.isoformat()}] {entry.level.name} - {entry.logger_name} - {entry.message}"
    
    def _sanitize_sensitive_data(self, data: Any) -> Any:
        """Remove sensitive data from logs"""
        if isinstance(data, dict):
            return {k: "[REDACTED]" if any(field in k.lower() for field in self.sensitive_fields) else v 
                    for k, v in data.items()}
        return data


class LogWriter:
    """Base class for log writers"""
    
    def __init__(self, formatter: LogFormatter):
        self.formatter = formatter
        self.active = True
    
    async def write(self, entry: LogEntry):
        """Write log entry"""
        raise NotImplementedError
    
    async def write_batch(self, entries: List[LogEntry]):
        """Write batch of log entries"""
        for entry in entries:
            await self.write(entry)
    
    def close(self):
        """Close writer"""
        self.active = False


class FileLogWriter(LogWriter):
    """File-based log writer with rotation"""
    
    def __init__(self, formatter: LogFormatter, config: LoggingConfig):
        super().__init__(formatter)
        self.config = config
        self.log_path = Path(config.log_directory)
        self.log_path.mkdir(exist_ok=True)
        
        self.current_file = self.log_path / config.log_file_name
        self.current_size = 0
        self.file_handle: Optional[TextIO] = None
        self._lock = threading.Lock()
        
        self._open_log_file()
    
    def _open_log_file(self):
        """Open log file for writing"""
        if self.file_handle:
            self.file_handle.close()
        
        self.file_handle = open(self.current_file, 'a', encoding='utf-8')
        if self.current_file.exists():
            self.current_size = self.current_file.stat().st_size
        else:
            self.current_size = 0
    
    async def write(self, entry: LogEntry):
        """Write single log entry to file"""
        if not self.active or not self.file_handle:
            return
        
        formatted_entry = self.formatter.format(entry) + "\n"
        entry_size = len(formatted_entry.encode('utf-8'))
        
        with self._lock:
            # Check if rotation is needed
            if self.current_size + entry_size > self.config.max_file_size_mb * 1024 * 1024:
                self._rotate_log_file()
            
            self.file_handle.write(formatted_entry)
            self.file_handle.flush()
            self.current_size += entry_size
    
    def _rotate_log_file(self):
        """Rotate log files"""
        if not self.current_file.exists():
            return
        
        # Close current file
        if self.file_handle:
            self.file_handle.close()
        
        # Rotate existing files
        for i in range(self.config.backup_count - 1, 0, -1):
            old_file = self.log_path / f"{self.config.log_file_name}.{i}"
            new_file = self.log_path / f"{self.config.log_file_name}.{i + 1}"
            
            if old_file.exists():
                if self.config.enable_compression and i == self.config.backup_count - 1:
                    # Compress oldest file
                    with open(old_file, 'rb') as f_in:
                        with gzip.open(f"{new_file}.gz", 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    old_file.unlink()
                else:
                    old_file.rename(new_file)
        
        # Move current file to .1
        backup_file = self.log_path / f"{self.config.log_file_name}.1"
        self.current_file.rename(backup_file)
        
        # Open new current file
        self._open_log_file()
    
    def close(self):
        """Close file writer"""
        super().close()
        if self.file_handle:
            self.file_handle.close()


class ConsoleLogWriter(LogWriter):
    """Console log writer"""
    
    def __init__(self, formatter: LogFormatter):
        super().__init__(formatter)
    
    async def write(self, entry: LogEntry):
        """Write to console"""
        if not self.active:
            return
        
        formatted_entry = self.formatter.format(entry)
        
        # Color coding for console output
        if entry.level == LogLevel.ERROR or entry.level == LogLevel.CRITICAL:
            print(f"\033[91m{formatted_entry}\033[0m", file=sys.stderr)  # Red
        elif entry.level == LogLevel.WARNING:
            print(f"\033[93m{formatted_entry}\033[0m")  # Yellow
        elif entry.level == LogLevel.INFO:
            print(f"\033[92m{formatted_entry}\033[0m")  # Green
        else:
            print(formatted_entry)


class LogAggregator:
    """Log aggregation and analysis"""
    
    def __init__(self):
        self.log_stats = {}
        self.error_patterns = {}
        self.performance_metrics = {}
        self._lock = threading.Lock()
    
    def process_entry(self, entry: LogEntry):
        """Process log entry for aggregation"""
        with self._lock:
            # Update statistics
            key = f"{entry.level.name}_{entry.category.name}"
            self.log_stats[key] = self.log_stats.get(key, 0) + 1
            
            # Track error patterns
            if entry.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
                error_hash = hashlib.md5(entry.message.encode()).hexdigest()[:8]
                if error_hash not in self.error_patterns:
                    self.error_patterns[error_hash] = {
                        'message': entry.message,
                        'count': 0,
                        'first_seen': entry.timestamp,
                        'last_seen': entry.timestamp
                    }
                
                self.error_patterns[error_hash]['count'] += 1
                self.error_patterns[error_hash]['last_seen'] = entry.timestamp
            
            # Track performance metrics
            if entry.duration_ms:
                metric_key = f"{entry.module}_{entry.function}"
                if metric_key not in self.performance_metrics:
                    self.performance_metrics[metric_key] = {
                        'count': 0,
                        'total_duration': 0,
                        'min_duration': float('inf'),
                        'max_duration': 0
                    }
                
                metrics = self.performance_metrics[metric_key]
                metrics['count'] += 1
                metrics['total_duration'] += entry.duration_ms
                metrics['min_duration'] = min(metrics['min_duration'], entry.duration_ms)
                metrics['max_duration'] = max(metrics['max_duration'], entry.duration_ms)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get aggregated statistics"""
        with self._lock:
            # Calculate performance averages
            performance_summary = {}
            for key, metrics in self.performance_metrics.items():
                if metrics['count'] > 0:
                    performance_summary[key] = {
                        'avg_duration_ms': metrics['total_duration'] / metrics['count'],
                        'min_duration_ms': metrics['min_duration'],
                        'max_duration_ms': metrics['max_duration'],
                        'call_count': metrics['count']
                    }
            
            return {
                'log_counts': dict(self.log_stats),
                'error_patterns': dict(self.error_patterns),
                'performance_metrics': performance_summary,
                'total_logs': sum(self.log_stats.values()),
                'error_count': sum(v for k, v in self.log_stats.items() if 'ERROR' in k or 'CRITICAL' in k)
            }


class ComprehensiveLogger:
    """Main comprehensive logging system"""
    
    def __init__(self, name: str, config: Optional[LoggingConfig] = None):
        self.name = name
        self.config = config or LoggingConfig()
        
        # Initialize components
        self.formatter = LogFormatter("json" if self.config.enable_structured_logging else "plain")
        self.buffer = LogBuffer(self.config.buffer_size) if self.config.enable_async_logging else None
        self.aggregator = LogAggregator()
        
        # Initialize writers
        self.writers: List[LogWriter] = []
        self._initialize_writers()
        
        # Background processing
        self._shutdown = threading.Event()
        self._background_thread = None
        if self.config.enable_async_logging:
            self._start_background_processing()
    
    def _initialize_writers(self):
        """Initialize log writers based on configuration"""
        if LogDestination.FILE in self.config.destinations:
            self.writers.append(FileLogWriter(self.formatter, self.config))
        
        if LogDestination.CONSOLE in self.config.destinations:
            self.writers.append(ConsoleLogWriter(self.formatter))
    
    def _start_background_processing(self):
        """Start background log processing thread"""
        self._background_thread = threading.Thread(target=self._background_worker, daemon=True)
        self._background_thread.start()
    
    def _background_worker(self):
        """Background worker for processing log entries"""
        while not self._shutdown.is_set():
            try:
                if self.buffer:
                    entries = self.buffer.get_batch(batch_size=50, timeout=self.config.flush_interval)
                    if entries:
                        asyncio.run(self._process_batch(entries))
                else:
                    time.sleep(0.1)
            except Exception as e:
                # Fallback logging to stderr to avoid infinite loops
                print(f"Logging system error: {e}", file=sys.stderr)
    
    async def _process_batch(self, entries: List[LogEntry]):
        """Process batch of log entries"""
        for entry in entries:
            self.aggregator.process_entry(entry)
            
            for writer in self.writers:
                try:
                    await writer.write(entry)
                except Exception as e:
                    print(f"Writer error: {e}", file=sys.stderr)
    
    def _create_log_entry(self, level: LogLevel, message: str, category: LogCategory = LogCategory.APPLICATION,
                         **kwargs) -> LogEntry:
        """Create log entry with context information"""
        import inspect
        
        # Get caller information
        frame = inspect.currentframe()
        try:
            caller_frame = frame.f_back.f_back if frame and frame.f_back else None
            if caller_frame:
                module = caller_frame.f_globals.get('__name__', 'unknown')
                function = caller_frame.f_code.co_name
                line_number = caller_frame.f_lineno
            else:
                module = 'unknown'
                function = 'unknown'
                line_number = 0
        finally:
            del frame
        
        return LogEntry(
            timestamp=datetime.utcnow(),
            level=level,
            category=category,
            logger_name=self.name,
            message=message,
            module=module,
            function=function,
            line_number=line_number,
            thread_id=threading.current_thread().name,
            process_id=os.getpid(),
            **kwargs
        )
    
    def _log(self, level: LogLevel, message: str, category: LogCategory = LogCategory.APPLICATION, **kwargs):
        """Internal logging method"""
        if level.value < self.config.log_level.value:
            return
        
        entry = self._create_log_entry(level, message, category, **kwargs)
        
        if self.config.enable_async_logging and self.buffer:
            success = self.buffer.add(entry)
            if not success:
                # Buffer full, write directly as fallback
                asyncio.run(self._process_batch([entry]))
        else:
            # Synchronous logging
            self.aggregator.process_entry(entry)
            asyncio.run(self._process_batch([entry]))
    
    # Public logging methods
    def trace(self, message: str, **kwargs):
        """Log trace message"""
        self._log(LogLevel.TRACE, message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self._log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self._log(LogLevel.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self._log(LogLevel.WARNING, message, **kwargs)
    
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log error message"""
        if exception:
            kwargs['exception'] = str(exception)
            kwargs['stack_trace'] = traceback.format_exc()
        self._log(LogLevel.ERROR, message, **kwargs)
    
    def critical(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log critical message"""
        if exception:
            kwargs['exception'] = str(exception)
            kwargs['stack_trace'] = traceback.format_exc()
        self._log(LogLevel.CRITICAL, message, **kwargs)
    
    def security(self, message: str, **kwargs):
        """Log security event"""
        self._log(LogLevel.SECURITY, message, LogCategory.SECURITY, **kwargs)
    
    def business(self, message: str, **kwargs):
        """Log business event"""
        self._log(LogLevel.BUSINESS, message, LogCategory.BUSINESS, **kwargs)
    
    def performance(self, message: str, duration_ms: float, **kwargs):
        """Log performance metric"""
        self._log(LogLevel.INFO, message, LogCategory.PERFORMANCE, duration_ms=duration_ms, **kwargs)
    
    @contextmanager
    def timer(self, operation_name: str, **kwargs):
        """Context manager for timing operations"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = (time.time() - start_time) * 1000
            self.performance(f"Operation '{operation_name}' completed", duration, **kwargs)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get logging statistics"""
        stats = self.aggregator.get_statistics()
        if self.buffer:
            stats['buffer_size'] = self.buffer.size()
            stats['dropped_entries'] = self.buffer.dropped_count()
        return stats
    
    def shutdown(self):
        """Shutdown logging system"""
        self._shutdown.set()
        
        if self._background_thread:
            self._background_thread.join(timeout=5.0)
        
        # Flush remaining entries
        if self.buffer:
            remaining_entries = self.buffer.get_batch(batch_size=1000, timeout=1.0)
            if remaining_entries:
                asyncio.run(self._process_batch(remaining_entries))
        
        # Close writers
        for writer in self.writers:
            writer.close()


# Global logger instance
_global_logger: Optional[ComprehensiveLogger] = None

def get_logger(name: str = "terragon", config: Optional[LoggingConfig] = None) -> ComprehensiveLogger:
    """Get or create logger instance"""
    global _global_logger
    if _global_logger is None:
        _global_logger = ComprehensiveLogger(name, config)
    return _global_logger

def configure_logging(config: LoggingConfig):
    """Configure global logging"""
    global _global_logger
    _global_logger = ComprehensiveLogger("terragon", config)

# Example usage and testing
if __name__ == "__main__":
    async def test_logging_system():
        """Test the comprehensive logging system"""
        print("📝 Testing Comprehensive Logging System v2.0")
        
        # Configure logging
        config = LoggingConfig(
            log_level=LogLevel.DEBUG,
            enable_async_logging=True,
            enable_structured_logging=True,
            log_directory="test_logs",
            max_file_size_mb=1
        )
        
        logger = ComprehensiveLogger("test_logger", config)
        
        # Test different log levels
        logger.trace("This is a trace message")
        logger.debug("Debug information", user_id="test_user")
        logger.info("Application started successfully", request_id="req_123")
        logger.warning("This is a warning", tags={"component": "test"})
        
        # Test error logging with exception
        try:
            raise ValueError("Test exception")
        except Exception as e:
            logger.error("An error occurred", exception=e, metadata={"test_data": "value"})
        
        # Test security logging
        logger.security("Security event detected", 
                        user_id="admin", 
                        source_ip="192.168.1.1",
                        metadata={"attack_type": "brute_force"})
        
        # Test performance logging
        with logger.timer("test_operation", user_id="test_user"):
            await asyncio.sleep(0.1)  # Simulate work
        
        logger.performance("Manual performance log", 150.5, operation="data_processing")
        
        # Test business logging
        logger.business("Contract processed successfully", 
                       contract_id="contract_123",
                       user_id="user_456",
                       metadata={"contract_type": "legal", "pages": 10})
        
        # Give time for async processing
        await asyncio.sleep(2)
        
        # Get statistics
        stats = logger.get_statistics()
        print(f"Logging statistics: {json.dumps(stats, indent=2, default=str)}")
        
        # Shutdown
        logger.shutdown()
    
    # Run test
    asyncio.run(test_logging_system())