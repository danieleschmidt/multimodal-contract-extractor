# Release v0.7.0

## 🚀 Major Feature: Centralized Configuration Management
- **NEW: Flexible Configuration System**: Implemented comprehensive configuration management following Twelve-Factor App principles
  - **YAML Configuration**: Support for `config.yml` files with complete schema validation
  - **Environment Variables**: Full environment variable override support with `MCE_` prefix
  - **Singleton Pattern**: Efficient configuration caching with reload capabilities
  - **12+ Configurable Parameters**: All hardcoded values now configurable
- **Configuration Categories**:
  - **OCR Settings**: Cache size limits, context window sizes
  - **Extraction Settings**: Confidence thresholds, file size limits, streaming parameters
  - **Security Settings**: File size limits, request ID constraints
  - **Health Check Settings**: Timeout configurations
  - **Document Processing**: Streaming chunk sizes and memory management
- **Developer Experience**: 
  - Added `config.example.yml` with detailed documentation and production recommendations
  - Updated README with comprehensive configuration examples
  - Full API documentation for `load_config()`, `get_config()`, and `reload_config()`

## 🧪 Enhanced Testing & Quality
- **12 New Configuration Tests**: Comprehensive test suite for configuration loading, validation, and environment overrides
- **Validation System**: Robust input validation with descriptive error messages
- **Test Isolation**: Proper singleton management in test suites

## 🔧 Code Quality Improvements
- **Eliminated Hardcoded Values**: Replaced 12+ magic numbers and constants throughout the codebase
- **Improved Maintainability**: Centralized configuration makes deployment and customization significantly easier
- **Better Error Handling**: Configuration validation provides clear feedback for invalid settings

## 📚 Documentation Updates
- **Configuration Guide**: Comprehensive documentation in README with examples
- **Production Recommendations**: Guidelines for production deployment configurations
- **Environment Variable Reference**: Complete list of supported environment variables

# Release v0.6.0

## 🚨 Critical Bug Fix
- **FIXED: Broken Batch Processing**: Resolved critical issue where `batch_extract.py` was creating dummy results instead of performing actual document extraction
  - **Root Cause**: batch_extract.py:96-103 was creating placeholder DocumentInfo with 0 pages and 0.00s processing time
  - **Solution**: Replaced dummy creation with real `extract_from_document()` calls 
  - **Impact**: Batch processing now performs actual OCR, clause detection, and produces meaningful results
  - **Testing**: Added comprehensive test `test_batch_extract_performs_real_extraction` to prevent regression
  - **Performance**: Restored full document processing capability (1.6s avg processing time, real clause detection)

## 🔧 Code Quality Improvements  
- Fixed import order issues in CLI modules (ruff E402 compliance)
- Improved test coverage for batch processing workflows
- Enhanced error handling and logging consistency

# Release v0.3.0

## ✨ Features
- **🚀 MAJOR: Real Document Extraction**: Replaced placeholder with actual OCR-based clause detection
  - Integrated Tesseract OCR for text extraction from PDF and image documents
  - Keyword-based clause classification (confidentiality, termination, payment terms, etc.)
  - Confidence scoring and key term extraction for each detected clause  
  - Document type inference (NDA, employment agreement, service agreement)
  - Processing time metrics and structured JSON output matching documented format
- **📊 Enhanced Output**: Rich extraction results with detailed metadata
  - Document information including page count, processing time, overall confidence
  - Clause-level details: ID, type, text, page number, confidence, key terms
  - Extraction metadata: timestamp, model version, processing method
- **🧪 Integration Tests**: Comprehensive end-to-end testing
  - Tests for PDF processing pipeline from load to JSON output
  - Validation of output structure against documented format
  - Edge case handling for documents with no detectable clauses

## 🔧 Technical Improvements
- Created `extraction.py` module bridging OCR detection with CLI
- Enhanced test helpers to create valid PDFs with text content for OCR testing
- Updated CLI to use real extraction instead of placeholder functionality
- Fixed deprecation warnings in datetime usage

# Release v0.2.0

## ✨ Features
- **Security Hardening**: Comprehensive input validation and sanitization
  - File type validation with magic byte detection
  - Path sanitization to prevent directory traversal attacks
  - File size limits (default 100MB) to prevent DoS
  - Request ID sanitization for secure logging
  - Output path validation with security checks
- **Enhanced CLI**: Both `extract.py` and `batch_extract.py` now use secure validation
- **Test Coverage**: 21 new security-focused tests ensuring robust validation

## 🔒 Security
- Added comprehensive file input validation
- Prevented directory traversal vulnerabilities
- Implemented secure path handling throughout CLI
- Added protection against malicious file uploads
- Sanitized all user inputs for logging safety

## 🐛 Fixes
- Improved error handling with security-focused messages
- Enhanced batch processing with file validation

## Other Changes
- Created development infrastructure (BACKLOG.md, TECH_DEBT.md)
- Updated test suite to use secure file formats
- Added test helper utilities for consistent test data

# Release v0.1.0

## ✨ Features
- CLI now accepts ``--log-level`` to control verbosity
- Streaming document loader reduces memory usage
- CI workflow runs lint, security and tests

## 🐛 Fixes
- None

## Other Changes
- Dependency versions updated

# Release v0.0.2

## ✨ Features
- Added `batch_extract.py` for directory-based extraction
- Exposed `__version__` and added `--version` to both CLI utilities
- README includes development setup and version checks
- Added simple Streamlit web interface (`web_app.py`)

## 🐛 Fixes
- No bug fixes.

## Other Changes
- Merge work branch
- Applying previous commit.
- Merge pull request #1 from danieleschmidt/codex/generate-strategic-development-plan
- chore(release): prepare for release v0.0.1
- docs(review): add code review report
- Update README.md
- Initial commit
