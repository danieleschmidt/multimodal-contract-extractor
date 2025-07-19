# Technical Debt Log

## Current Technical Debt Items

### 🔴 Critical (Blocking core functionality)

#### TD-001: Placeholder Extraction Implementation
- **Location**: `extract.py:83`
- **Issue**: Core extraction logic is a placeholder comment
- **Impact**: Prevents actual document processing
- **Effort**: Large (requires ML model integration)
- **Created**: 2025-07-19
- **Priority**: P1 - Blocking
- **Owner**: Backend Team

#### TD-002: Missing OCR/VLM Integration
- **Location**: `clause_detection.py`
- **Issue**: Clause detection lacks actual ML model calls
- **Impact**: No real clause identification capability
- **Effort**: Large (model integration, API calls)
- **Created**: 2025-07-19
- **Priority**: P1 - Blocking
- **Owner**: ML Team

### 🟡 Medium (Affects maintainability/quality)

#### TD-003: Scattered Configuration
- **Location**: Multiple modules
- **Issue**: Configuration spread across files, no central config
- **Impact**: Hard to manage settings, deployment complexity
- **Effort**: Medium (refactor config system)
- **Created**: 2025-07-19
- **Priority**: P2 - Important
- **Owner**: DevOps Team

#### TD-004: Error Handling Inconsistency
- **Location**: CLI modules
- **Issue**: Inconsistent error handling patterns across modules
- **Impact**: Poor user experience, debugging difficulty
- **Effort**: Medium (standardize error patterns)
- **Created**: 2025-07-19
- **Priority**: P2 - Important
- **Owner**: Backend Team

#### TD-005: Missing Input Validation
- **Location**: `extract.py`, `batch_extract.py`
- **Issue**: Limited file validation and sanitization
- **Impact**: Security vulnerability, potential crashes
- **Effort**: Medium (add validation layers)
- **Created**: 2025-07-19
- **Priority**: P1 - Security
- **Owner**: Security Team

### 🟢 Low (Nice to have improvements)

#### TD-006: Hardcoded File Paths
- **Location**: Various test files
- **Issue**: Some tests use hardcoded paths
- **Impact**: Test portability issues
- **Effort**: Small (parameterize paths)
- **Created**: 2025-07-19
- **Priority**: P3 - Minor
- **Owner**: QA Team

#### TD-007: Missing Type Hints
- **Location**: Some utility functions
- **Issue**: Incomplete type annotations
- **Impact**: Reduced IDE support, maintainability
- **Effort**: Small (add type hints)
- **Created**: 2025-07-19
- **Priority**: P3 - Minor
- **Owner**: Backend Team

## Resolution Guidelines

### Critical Debt
- Must be addressed before next major release
- Requires architectural decisions and planning
- Should be included in sprint planning

### Medium Debt
- Address during regular sprint work when related features are modified
- Can be bundled with related feature development
- Should not block releases but plan for resolution

### Low Debt
- Address during maintenance windows
- Good for junior developer tasks
- Can be deferred if higher priority work exists

## Tracking Process

1. **Identification**: Add new debt items when discovered during development
2. **Prioritization**: Assign priority based on impact and blocking nature
3. **Assignment**: Assign to appropriate team/owner
4. **Resolution**: Update status when addressed
5. **Review**: Monthly review of all debt items

## Metrics

- Total debt items: 7
- Critical: 2
- Medium: 3
- Low: 2
- Average age: New (established 2025-07-19)

## Next Actions

1. Address TD-001 and TD-002 as part of core extraction implementation
2. Plan TD-003 and TD-005 for next sprint
3. Bundle TD-004 with error handling improvements
4. Schedule TD-006 and TD-007 for maintenance tasks