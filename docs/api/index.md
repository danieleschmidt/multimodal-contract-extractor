# API Reference

This section provides comprehensive documentation for the Multimodal Contract Extractor API.

## Overview

The Multimodal Contract Extractor provides both a Python API and REST API for programmatic access to contract extraction capabilities.

## Quick Start

```python
from multimodal_contract_extractor import DocumentProcessor
from multimodal_contract_extractor.config import Config

# Initialize configuration
config = Config()

# Create processor
processor = DocumentProcessor(config)

# Process document
result = processor.extract_clauses("path/to/contract.pdf")
```

## API Components

### Core Modules

- **[Document Processing](document.md)** - Core document processing functionality
- **[Extraction Engine](extraction.md)** - Contract clause extraction logic
- **[Configuration](config.md)** - Configuration management
- **[Security](security.md)** - Security utilities and validation
- **[Metrics](metrics.md)** - Performance monitoring and metrics

### REST API

- **[REST API](rest.md)** - HTTP API endpoints
- **[OpenAPI Specification](openapi.md)** - Interactive API documentation

## Error Handling

All API functions use structured exception handling:

```python
from multimodal_contract_extractor.exceptions import (
    ExtractionError,
    ConfigurationError,
    SecurityError
)

try:
    result = processor.extract_clauses("document.pdf")
except ExtractionError as e:
    print(f"Extraction failed: {e}")
except SecurityError as e:
    print(f"Security validation failed: {e}")
```

## Performance Considerations

- Use batch processing for multiple documents
- Configure appropriate memory limits
- Monitor extraction metrics
- Implement caching for repeated operations

## Version Compatibility

The API follows semantic versioning. Check the version compatibility matrix:

| API Version | Python Version | Status |
|-------------|----------------|--------|
| 0.1.x       | ≥3.8          | Active |

## Next Steps

- Explore the [Core Modules](document.md) documentation
- Check out the [REST API](rest.md) endpoints
- View the [OpenAPI Specification](openapi.md) for interactive testing