# Configuration Guide

This guide provides comprehensive documentation for configuring the Multimodal Contract Extractor.

## Configuration Overview

The application uses a hierarchical configuration system:

1. **Default values** (hardcoded in the application)
2. **Configuration file** (`config.yml`)
3. **Environment variables** (highest priority)

Configuration follows the [Twelve-Factor App](https://12factor.net/config) methodology.

## Configuration File Format

Configuration files use YAML format. Create a `config.yml` file in your project directory:

```yaml
# config.yml
ocr:
  cache_size_limit: 100
  context_window_size: 100

extraction:
  base_confidence_score: 0.75
  max_confidence_cap: 0.95
  
security:
  max_file_size_mb: 100
```

## Configuration Sections

### OCR Configuration (`ocr`)

Controls Optical Character Recognition behavior and caching.

#### `cache_size_limit`
- **Type**: Integer
- **Default**: `100`
- **Description**: Maximum number of OCR results to cache in memory
- **Impact**: Higher values improve performance but increase memory usage
- **Recommended values**:
  - Development: `50-100`
  - Production: `200-500`
  - High-memory systems: `1000+`

```yaml
ocr:
  cache_size_limit: 200
```

#### `context_window_size`
- **Type**: Integer  
- **Default**: `100`
- **Description**: Number of characters before/after keywords to extract for context
- **Impact**: Affects clause boundary detection accuracy
- **Recommended values**:
  - Precise extraction: `50-100`
  - Comprehensive context: `150-200`
  - Full paragraph context: `300+`

```yaml
ocr:
  context_window_size: 150
```

#### Advanced OCR Options

```yaml
ocr:
  # Cache configuration
  cache_size_limit: 500
  cache_ttl_seconds: 3600  # Cache expiration time
  
  # OCR engine settings
  tesseract_config: "--oem 3 --psm 6"  # Tesseract configuration
  dpi: 300  # DPI for PDF to image conversion
  
  # Language settings
  languages: ["eng", "fra", "deu"]  # OCR languages
  fallback_language: "eng"  # Default language
  
  # Context extraction
  context_window_size: 100
  min_context_length: 20  # Minimum context to extract
  max_context_length: 500  # Maximum context per clause
```

### Extraction Configuration (`extraction`)

Controls document processing and clause detection algorithms.

#### `base_confidence_score`
- **Type**: Float (0.0-1.0)
- **Default**: `0.75`
- **Description**: Base confidence score for keyword-based clause detection
- **Impact**: Lower values detect more clauses (higher recall), higher values are more selective (higher precision)
- **Recommended values**:
  - Comprehensive extraction: `0.6-0.7`
  - Balanced approach: `0.75-0.8`
  - Conservative extraction: `0.85-0.9`

```yaml
extraction:
  base_confidence_score: 0.8
```

#### `length_bonus_divisor`
- **Type**: Integer
- **Default**: `1000`
- **Description**: Divisor for calculating length-based confidence bonus
- **Impact**: Lower values give larger bonuses for longer clauses
- **Formula**: `bonus = clause_length / length_bonus_divisor`

#### `max_confidence_cap`
- **Type**: Float (0.0-1.0)
- **Default**: `0.95`
- **Description**: Maximum confidence score for keyword-based detection
- **Impact**: Prevents overconfidence in automated detection

#### `file_size_threshold_mb`
- **Type**: Integer
- **Default**: `10`
- **Description**: File size threshold in MB for switching to streaming mode
- **Impact**: Files larger than this threshold use memory-efficient streaming
- **Recommended values**:
  - Low-memory systems: `5-10`
  - Standard systems: `15-25`
  - High-memory systems: `50+`

#### `streaming_chunk_size`
- **Type**: Integer
- **Default**: `5`
- **Description**: Number of pages to process at once during streaming
- **Impact**: Balance between memory usage and processing efficiency
- **Recommended values**:
  - Memory-constrained: `3-5`
  - Balanced: `5-10`
  - High-performance: `10-20`

#### Advanced Extraction Options

```yaml
extraction:
  # Confidence scoring
  base_confidence_score: 0.75
  length_bonus_divisor: 1000
  max_confidence_cap: 0.95
  min_confidence_threshold: 0.5  # Minimum score to include clause
  
  # Streaming configuration
  file_size_threshold_mb: 15
  streaming_chunk_size: 8
  memory_limit_mb: 512  # Memory limit per processing batch
  
  # Clause detection
  keyword_matching_algorithm: "fuzzy"  # "exact", "fuzzy", "semantic"
  fuzzy_match_threshold: 0.8  # For fuzzy matching
  max_clauses_per_document: 1000  # Prevent memory issues
  
  # Processing timeouts
  per_page_timeout_seconds: 30
  total_processing_timeout_seconds: 300
  
  # Quality filters
  min_clause_length: 10  # Minimum characters per clause
  max_clause_length: 5000  # Maximum characters per clause
  filter_duplicates: true  # Remove duplicate clauses
  duplicate_similarity_threshold: 0.9
```

### Security Configuration (`security`)

Controls file validation, size limits, and security measures.

#### `max_file_size_mb`
- **Type**: Integer
- **Default**: `100`
- **Description**: Maximum allowed file size in MB
- **Impact**: Files larger than this are rejected
- **Recommended values**:
  - Web applications: `50-100`
  - Enterprise systems: `200-500`
  - Batch processing: `1000+`

#### `request_id_length_limit`
- **Type**: Integer
- **Default**: `64`
- **Description**: Maximum length for request IDs used in logging
- **Impact**: Prevents DoS attacks via very long request IDs

#### Advanced Security Options

```yaml
security:
  # File size limits
  max_file_size_mb: 150
  min_file_size_bytes: 1024  # Minimum file size (1KB)
  
  # File validation
  allowed_mime_types:
    - "application/pdf"
    - "image/png"
    - "image/jpeg"
    - "image/tiff"
  
  # Rate limiting
  max_requests_per_minute: 60
  max_concurrent_requests: 10
  
  # Request validation
  request_id_length_limit: 64
  max_filename_length: 255
  sanitize_filenames: true
  
  # Temporary file security
  temp_file_permissions: "0600"  # Owner read/write only
  temp_file_cleanup_timeout: 3600  # Cleanup after 1 hour
  
  # Content scanning
  scan_for_malware: false  # Enable virus scanning
  block_password_protected: true  # Block encrypted PDFs
  
  # Logging security
  log_request_bodies: false  # Don't log sensitive data
  mask_personal_info: true  # Mask PII in logs
```

### Health Check Configuration (`health`)

Controls system health monitoring and dependency checking.

#### `check_timeout_seconds`
- **Type**: Integer
- **Default**: `5`
- **Description**: Timeout in seconds for dependency health checks
- **Impact**: Prevents hanging on unresponsive services

#### Advanced Health Check Options

```yaml
health:
  # Check timeouts
  check_timeout_seconds: 10
  startup_timeout_seconds: 30
  
  # Dependency checks
  check_tesseract: true
  check_poppler: true
  check_python_packages: true
  check_disk_space: true
  check_memory: true
  
  # Thresholds
  min_free_disk_mb: 1000  # Minimum free disk space
  max_memory_usage_percent: 90  # Maximum memory usage
  
  # Health check endpoints
  endpoint_path: "/health"
  detailed_endpoint_path: "/health/detailed"
  
  # Check intervals
  periodic_check_interval_seconds: 60
  dependency_recheck_interval_seconds: 300
```

### Document Processing Configuration (`document`)

Controls document loading and processing behavior.

#### `default_streaming_chunk_size`
- **Type**: Integer
- **Default**: `10`
- **Description**: Default number of pages to load at once for streaming
- **Impact**: Balances memory usage with processing efficiency

#### Advanced Document Options

```yaml
document:
  # Streaming configuration
  default_streaming_chunk_size: 12
  max_pages_per_document: 500  # Limit document size
  
  # PDF processing
  pdf_dpi: 300  # DPI for PDF to image conversion
  pdf_format: "RGB"  # Color format: RGB, L (grayscale)
  pdf_use_poppler: true  # Use Poppler for PDF processing
  
  # Image processing
  image_preprocessing: true  # Enable image enhancement
  image_denoise: false  # Apply denoising filters
  image_contrast_enhancement: 1.2  # Contrast multiplier
  image_sharpening: 1.1  # Sharpening factor
  
  # Page detection
  auto_rotate_pages: true  # Auto-rotate based on text
  detect_page_orientation: true
  skip_blank_pages: true  # Skip pages with no content
  blank_page_threshold: 50  # Minimum characters for non-blank
  
  # Memory management
  unload_pages_after_processing: true  # Save memory
  cache_processed_pages: false  # Trade memory for speed
```

## Environment Variable Configuration

Override any configuration setting using environment variables with the format: `MCE_<SECTION>_<SETTING>`

### Common Environment Variables

```bash
# OCR Configuration
export MCE_OCR_CACHE_SIZE_LIMIT=200
export MCE_OCR_CONTEXT_WINDOW_SIZE=150

# Extraction Configuration
export MCE_EXTRACTION_BASE_CONFIDENCE_SCORE=0.8
export MCE_EXTRACTION_FILE_SIZE_THRESHOLD_MB=20
export MCE_EXTRACTION_STREAMING_CHUNK_SIZE=8

# Security Configuration
export MCE_SECURITY_MAX_FILE_SIZE_MB=150
export MCE_SECURITY_REQUEST_ID_LENGTH_LIMIT=64

# Health Check Configuration
export MCE_HEALTH_CHECK_TIMEOUT_SECONDS=10

# Document Configuration
export MCE_DOCUMENT_DEFAULT_STREAMING_CHUNK_SIZE=12
export MCE_DOCUMENT_PDF_DPI=300
```

### Environment-Specific Configuration

#### Development
```bash
export MCE_EXTRACTION_BASE_CONFIDENCE_SCORE=0.7
export MCE_OCR_CACHE_SIZE_LIMIT=50
export MCE_SECURITY_MAX_FILE_SIZE_MB=50
export MCE_LOG_LEVEL=DEBUG
```

#### Staging
```bash
export MCE_EXTRACTION_BASE_CONFIDENCE_SCORE=0.8
export MCE_OCR_CACHE_SIZE_LIMIT=200
export MCE_SECURITY_MAX_FILE_SIZE_MB=100
export MCE_LOG_LEVEL=INFO
```

#### Production
```bash
export MCE_EXTRACTION_BASE_CONFIDENCE_SCORE=0.85
export MCE_OCR_CACHE_SIZE_LIMIT=500
export MCE_SECURITY_MAX_FILE_SIZE_MB=200
export MCE_LOG_LEVEL=WARNING
```

## Configuration Loading

### Programmatic Configuration

```python
from multimodal_contract_extractor.config import load_config, get_config, Config

# Load from specific file
config = load_config(config_path='config.prod.yml')

# Load from default locations (config.yml, then environment variables)
config = get_config()

# Access configuration values
print(f"OCR cache limit: {config.ocr.cache_size_limit}")
print(f"Max file size: {config.security.max_file_size_mb}MB")
print(f"Base confidence: {config.extraction.base_confidence_score}")

# Check if streaming will be used for a file
file_size_mb = 25
will_stream = file_size_mb > config.extraction.file_size_threshold_mb
print(f"Will use streaming: {will_stream}")
```

### Configuration Validation

```python
from multimodal_contract_extractor.config import validate_config

try:
    config = load_config('config.yml')
    validate_config(config)
    print("Configuration is valid")
except ValueError as e:
    print(f"Configuration error: {e}")
```

### Dynamic Configuration Updates

```python
# Update configuration at runtime (not persistent)
config = get_config()
config.ocr.cache_size_limit = 300
config.extraction.base_confidence_score = 0.8

# Reload configuration from file
config = load_config(config_path='config.yml', reload=True)
```

## Performance Tuning

### High-Performance Configuration

For systems with ample resources:

```yaml
ocr:
  cache_size_limit: 1000
  context_window_size: 200

extraction:
  base_confidence_score: 0.8
  file_size_threshold_mb: 50
  streaming_chunk_size: 15

document:
  default_streaming_chunk_size: 20
  pdf_dpi: 400
  cache_processed_pages: true
```

### Memory-Constrained Configuration

For systems with limited memory:

```yaml
ocr:
  cache_size_limit: 25
  context_window_size: 75

extraction:
  file_size_threshold_mb: 5
  streaming_chunk_size: 3
  memory_limit_mb: 256

document:
  default_streaming_chunk_size: 3
  unload_pages_after_processing: true
  cache_processed_pages: false
```

### High-Throughput Configuration

For batch processing scenarios:

```yaml
ocr:
  cache_size_limit: 500
  
extraction:
  base_confidence_score: 0.75
  streaming_chunk_size: 10
  per_page_timeout_seconds: 15

security:
  max_concurrent_requests: 20
  max_requests_per_minute: 300

health:
  check_timeout_seconds: 3
  periodic_check_interval_seconds: 30
```

## Configuration Best Practices

### 1. Environment-Specific Files

Use separate configuration files for different environments:

```
config/
├── base.yml          # Common settings
├── development.yml   # Development overrides
├── staging.yml       # Staging overrides
└── production.yml    # Production overrides
```

### 2. Sensitive Data Management

Never store sensitive data in configuration files:

```yaml
# Bad - hardcoded secrets
database:
  password: "secret123"

# Good - use environment variables
database:
  password: ${DATABASE_PASSWORD}
```

### 3. Configuration Versioning

Include configuration schema version:

```yaml
config_version: "1.2"
ocr:
  cache_size_limit: 100
```

### 4. Monitoring Configuration

Log configuration values on startup:

```python
import logging
from multimodal_contract_extractor.config import get_config

config = get_config()
logging.info(f"Configuration loaded: OCR cache={config.ocr.cache_size_limit}, "
            f"Max file size={config.security.max_file_size_mb}MB")
```

### 5. Gradual Rollouts

Use feature flags for new configuration options:

```yaml
features:
  enable_advanced_ocr: false
  enable_semantic_matching: false
  enable_performance_monitoring: true
```

## Troubleshooting Configuration

### Validate Configuration Syntax

```bash
# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('config.yml'))"

# Validate configuration
python -c "from multimodal_contract_extractor.config import load_config; load_config('config.yml')"
```

### Debug Configuration Loading

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from multimodal_contract_extractor.config import load_config
config = load_config('config.yml')
# Debug messages will show configuration loading process
```

### Check Effective Configuration

```python
from multimodal_contract_extractor.config import get_config
import json

config = get_config()
print(json.dumps(config.__dict__, indent=2, default=str))
```

### Override Precedence Testing

```python
import os
from multimodal_contract_extractor.config import get_config

# Set environment variable
os.environ['MCE_OCR_CACHE_SIZE_LIMIT'] = '999'

config = get_config()
print(f"Cache limit: {config.ocr.cache_size_limit}")  # Should be 999
```