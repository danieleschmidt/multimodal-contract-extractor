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
