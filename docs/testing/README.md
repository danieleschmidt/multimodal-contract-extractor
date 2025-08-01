# Testing Guide

This guide covers the comprehensive testing strategy for the Multimodal Contract Extractor, including unit tests, integration tests, performance tests, and end-to-end testing.

## Test Structure

```
tests/
├── conftest.py                 # Global fixtures and configuration
├── fixtures/                   # Test data and fixtures
├── unit/                      # Unit tests (fast, isolated)
├── integration/               # Integration tests (slower, dependencies)
├── e2e/                       # End-to-end workflow tests
├── performance/               # Performance and load tests
├── contracts/                 # Contract testing for APIs
└── security/                  # Security-focused tests
```

## Test Categories

### Unit Tests
- **Location**: `tests/test_*.py` (root level)
- **Purpose**: Test individual functions and classes in isolation
- **Speed**: Fast (< 1 second per test)
- **Dependencies**: None (mocked)
- **Markers**: `@pytest.mark.unit`

### Integration Tests
- **Location**: `tests/integration/`
- **Purpose**: Test component interactions
- **Speed**: Medium (1-10 seconds per test)
- **Dependencies**: Real dependencies, but controlled
- **Markers**: `@pytest.mark.integration`

### End-to-End Tests
- **Location**: `tests/e2e/`
- **Purpose**: Test complete user workflows
- **Speed**: Slow (10+ seconds per test)
- **Dependencies**: Full system
- **Markers**: `@pytest.mark.integration`

### Performance Tests
- **Location**: `tests/performance/`
- **Purpose**: Validate performance requirements
- **Speed**: Variable
- **Dependencies**: Performance monitoring tools
- **Markers**: `@pytest.mark.performance`

### Contract Tests
- **Location**: `tests/contracts/`
- **Purpose**: Validate API contracts and interfaces
- **Speed**: Fast to medium
- **Dependencies**: Mock services
- **Markers**: `@pytest.mark.contract`

## Running Tests

### All Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html --cov-report=term
```

### Specific Test Categories
```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Performance tests only
pytest -m performance

# Exclude slow tests
pytest -m "not slow"
```

### Specific Test Files
```bash
# Run specific test file
pytest tests/test_config.py

# Run specific test function
pytest tests/test_config.py::test_load_config

# Run tests matching pattern
pytest -k "config"
```

### Development Testing
```bash
# Fast development cycle (fail fast)
pytest -x --ff

# Verbose output
pytest -v

# Show local variables on failure
pytest -l

# Run tests in parallel (with pytest-xdist)
pytest -n auto
```

## Test Configuration

### pytest.ini Configuration
- Coverage thresholds: 85% minimum
- Strict markers and configuration
- Custom markers for test categorization
- Logging configuration
- Warning filters

### Fixtures and Test Data
- Global fixtures in `conftest.py`
- Test data factories for generating test cases
- Temporary directories and file management
- Mock external services and dependencies
- Performance timing utilities

## Test Data Management

### Synthetic Test Data
All test data must be synthetic and non-sensitive:
- Use generic company names (e.g., "Test Company Inc.")
- Use placeholder addresses and contact information
- Create realistic but clearly fake contract content
- Never use real contract documents

### Test Data Location
- Sample contracts: `tests/fixtures/contracts/`
- Mock images: `tests/fixtures/images/`
- JSON fixtures: `tests/fixtures/data/`
- Configuration files: `tests/fixtures/configs/`

## Performance Testing

### Performance Thresholds
- Document processing: < 30 seconds
- Clause extraction: < 10 seconds
- OCR processing: < 15 seconds
- Batch processing: < 60 seconds per document

### Load Testing Scenarios
- Single user processing multiple documents
- Multiple concurrent users
- High-volume batch processing
- Memory usage under load
- Error recovery under stress

### Performance Monitoring
- Memory usage tracking
- Processing time measurement
- Throughput metrics
- Resource utilization
- Regression detection

## Security Testing

### Security Test Categories
- Input validation
- File upload security
- Authentication and authorization
- Data sanitization
- Error message security
- Dependency vulnerability scanning

### Security Test Tools
- Bandit for Python security issues
- Safety for dependency vulnerabilities
- Custom security validators
- Penetration testing scenarios

## Continuous Integration

### CI Pipeline Testing
```yaml
# Example CI test stages
stages:
  - lint_and_format
  - unit_tests
  - integration_tests
  - security_tests
  - performance_tests
  - e2e_tests
```

### Test Execution Order
1. **Fast feedback**: Linting and unit tests
2. **Integration**: Component integration tests
3. **Security**: Security scanning and validation
4. **Performance**: Performance benchmarks
5. **End-to-end**: Complete workflow validation

## Test Best Practices

### Writing Good Tests
1. **AAA Pattern**: Arrange, Act, Assert
2. **Single Responsibility**: One test, one concept
3. **Descriptive Names**: Clear test purpose
4. **Independent Tests**: No test dependencies
5. **Deterministic**: Consistent results

### Test Organization
1. **Group Related Tests**: Use test classes
2. **Parameterize**: Test multiple scenarios efficiently
3. **Use Fixtures**: Share setup code
4. **Mark Appropriately**: Use pytest markers
5. **Document Complex Tests**: Add docstrings

### Mock Usage Guidelines
1. **Mock External Dependencies**: Never real external calls
2. **Mock at Boundaries**: System boundaries, not internals
3. **Verify Interactions**: Assert mock calls when relevant
4. **Use Realistic Mocks**: Return realistic data
5. **Reset Mocks**: Clean state between tests

## Test Coverage

### Coverage Goals
- **Overall Coverage**: 90%+ line coverage
- **Critical Paths**: 100% coverage for core functionality
- **Error Handling**: All error paths tested
- **Integration Points**: All interfaces covered

### Coverage Reporting
- HTML reports: `htmlcov/index.html`
- Terminal reports: Coverage summary
- XML reports: For CI integration
- Coverage badges: Repository documentation

### Coverage Analysis
- Identify uncovered code
- Prioritize critical path coverage
- Review coverage gaps regularly
- Update tests for new features

## Test Maintenance

### Regular Maintenance Tasks
1. **Update Test Data**: Keep fixtures current
2. **Review Slow Tests**: Optimize or mark appropriately
3. **Update Dependencies**: Keep test tools current
4. **Review Coverage**: Maintain coverage goals
5. **Clean Up**: Remove obsolete tests

### Test Refactoring
- Extract common test utilities
- Consolidate similar test scenarios
- Update tests for API changes
- Improve test readability
- Optimize test performance

## Debugging Tests

### Common Issues
- **Flaky Tests**: Non-deterministic behavior
- **Slow Tests**: Performance bottlenecks
- **Mock Issues**: Incorrect mock configuration
- **Fixture Problems**: Setup/teardown issues
- **Environment Dependencies**: Platform-specific issues

### Debugging Tools
- `pytest --pdb`: Drop into debugger on failure
- `pytest -l`: Show local variables
- `pytest -v`: Verbose test output
- `pytest --tb=long`: Full traceback
- `pytest --capture=no`: Show print statements

## Integration with Development

### Pre-commit Testing
- Run fast tests before commit
- Automated linting and formatting
- Security scanning
- Basic functionality verification

### Development Workflow
1. **Write Test First**: TDD approach when possible
2. **Run Tests Frequently**: Fast feedback loop
3. **Fix Failures Immediately**: Don't accumulate technical debt
4. **Update Tests with Code**: Keep tests synchronized
5. **Review Test Coverage**: Ensure adequate coverage

## Resources

### Documentation
- [pytest documentation](https://pytest.org/)
- [Coverage.py documentation](https://coverage.readthedocs.io/)
- [Mock documentation](https://docs.python.org/3/library/unittest.mock.html)

### Tools and Libraries
- `pytest`: Testing framework
- `pytest-cov`: Coverage reporting
- `pytest-xdist`: Parallel test execution
- `pytest-mock`: Improved mocking
- `pytest-benchmark`: Performance testing
- `hypothesis`: Property-based testing

### Test Examples
See existing tests in the repository for examples of:
- Unit test patterns
- Integration test setup
- Performance test implementation
- Mock usage patterns
- Fixture design