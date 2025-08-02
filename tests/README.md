# Testing Infrastructure

This directory contains the comprehensive test suite for the Multimodal Contract Extractor. The testing infrastructure is designed to ensure code quality, reliability, and performance across all components.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py                 # Pytest configuration and fixtures
├── utils.py                   # Test utilities and helpers
├── test_config.py            # Test configuration classes
├── README.md                 # This file
├── fixtures/                 # Test data and fixtures
│   ├── README.md
│   ├── contracts/           # Sample contract files
│   ├── images/              # Sample image files
│   └── data/                # JSON test data
├── mocks/                   # Mock objects and services
│   ├── __init__.py
│   └── mock_services.py     # Mock implementations
├── unit/                    # Unit tests
│   ├── __init__.py
│   └── test_*.py           # Individual unit tests
├── integration/             # Integration tests
│   ├── __init__.py
│   ├── test_cli_end_to_end.py
│   ├── test_pipeline_integration.py
│   └── test_web_app_integration.py
├── e2e/                     # End-to-end tests
│   ├── __init__.py
│   └── test_end_to_end_workflows.py
├── performance/             # Performance tests
│   ├── __init__.py
│   └── test_benchmarks.py
├── contracts/               # Contract validation tests
│   ├── __init__.py
│   └── test_contract_validation.py
└── [individual test files]  # Direct test files
```

## Test Categories

### Unit Tests
- **Location**: `tests/unit/` and root-level `test_*.py` files
- **Marker**: `@pytest.mark.unit`
- **Purpose**: Test individual functions and classes in isolation
- **Characteristics**: Fast, isolated, mocked dependencies
- **Run with**: `pytest -m unit`

### Integration Tests
- **Location**: `tests/integration/`
- **Marker**: `@pytest.mark.integration`
- **Purpose**: Test component interactions and data flow
- **Characteristics**: Medium speed, real dependencies where possible
- **Run with**: `pytest -m integration`

### End-to-End Tests
- **Location**: `tests/e2e/`
- **Marker**: `@pytest.mark.e2e`
- **Purpose**: Test complete workflows from user perspective
- **Characteristics**: Slower, full system tests
- **Run with**: `pytest -m e2e`

### Performance Tests
- **Location**: `tests/performance/`
- **Marker**: `@pytest.mark.performance`
- **Purpose**: Benchmark performance and detect regressions
- **Characteristics**: Timing-sensitive, resource monitoring
- **Run with**: `pytest -m performance`

### Security Tests
- **Marker**: `@pytest.mark.security`
- **Purpose**: Test security features and vulnerability resistance
- **Characteristics**: Input validation, authentication, authorization
- **Run with**: `pytest -m security`

## Test Configuration

### Environment Variables
```bash
# Test execution control
export TEST_TYPE=unit                    # unit|integration|performance|e2e
export RUN_SLOW_TESTS=false             # Enable/disable slow tests
export RUN_INTEGRATION_TESTS=true       # Enable/disable integration tests
export RUN_PERFORMANCE_TESTS=false      # Enable/disable performance tests
export RUN_E2E_TESTS=false              # Enable/disable E2E tests

# Test environment settings
export MCE_ENV=test                      # Set environment to test mode
export MCE_DEBUG=true                    # Enable debug mode
export MCE_LOG_LEVEL=DEBUG               # Set log level for tests
```

### Configuration Classes
The test suite uses configuration classes to manage different test environments:

- `UnitTestConfig`: Fast, minimal settings for unit tests
- `IntegrationTestConfig`: Realistic settings for integration tests
- `PerformanceTestConfig`: Production-like settings for performance tests
- `E2ETestConfig`: Full system settings for end-to-end tests

## Running Tests

### Quick Commands
```bash
# Run all tests
make test
pytest

# Run specific test categories
pytest -m unit                    # Unit tests only
pytest -m integration            # Integration tests only
pytest -m "not slow"             # Exclude slow tests
pytest -m "unit or integration"  # Multiple categories

# Run with coverage
make test-cov
pytest --cov=src --cov-report=html

# Run performance tests
pytest -m performance --benchmark-only

# Run specific test file
pytest tests/test_config.py
pytest tests/integration/test_cli_end_to_end.py

# Run tests matching pattern
pytest -k "test_document"
pytest -k "extract"
```

### Development Workflow
```bash
# Quick feedback during development
pytest -x --tb=short -q          # Stop on first failure, short traceback

# Full quality check
pytest --cov=src --cov-report=term --cov-fail-under=90

# Parallel execution (faster)
pytest -n auto                   # Use all CPU cores
pytest -n 4                      # Use 4 processes
```

### CI/CD Commands
```bash
# Complete test suite for CI
pytest --cov=src --cov-report=xml --junitxml=junit.xml

# Performance regression detection
pytest -m performance --benchmark-compare

# Security test suite
pytest -m security
```

## Test Data and Fixtures

### Fixtures
Common fixtures are defined in `conftest.py`:

- `test_config`: Test-specific configuration
- `temp_dir`: Temporary directory for test files
- `sample_pdf_path`: Sample PDF file for testing
- `sample_image_path`: Sample image file for testing
- `sample_contract_data`: Mock contract data structure
- `mock_ocr_result`: Mock OCR results
- `performance_timer`: Performance measurement utility

### Test Data
- **Real Files**: Sample PDFs and images in `tests/fixtures/`
- **Mock Data**: Generated test data for various scenarios
- **JSON Fixtures**: Structured test data in JSON format

### Creating Test Data
```python
# Using fixtures
def test_document_processing(sample_pdf_path, sample_contract_data):
    # Test using provided fixtures
    pass

# Using test data factory
def test_multiple_contracts(test_data_factory):
    contract = test_data_factory("contract", confidence=0.9)
    clause = test_data_factory("clause", type="termination")
```

## Mock Services

The test suite includes comprehensive mock implementations:

- `MockOCREngine`: Simulates OCR processing
- `MockVisionLanguageModel`: Simulates ML model inference
- `MockDocumentProcessor`: Complete document processing pipeline
- `MockHealthChecker`: Health check simulation
- `MockMetricsCollector`: Metrics collection simulation
- `MockFileStorage`: File storage operations
- `MockConfiguration`: Configuration management

### Using Mocks
```python
from tests.mocks.mock_services import create_mock_document_processor

def test_with_mock_processor():
    processor = create_mock_document_processor(ocr_confidence=0.9)
    result = processor.process_document("test.pdf")
    assert result["document_info"]["overall_confidence"] == 0.9
```

## Test Utilities

### Decorators
```python
from tests.utils import performance_test, with_temp_dir, skip_if_no_gpu

@performance_test(max_duration=5.0)
def test_fast_processing():
    # Test that must complete within 5 seconds
    pass

@with_temp_dir
def test_file_operations(temp_dir):
    # Test with temporary directory provided
    pass

@skip_if_no_gpu
def test_gpu_acceleration():
    # Test that requires GPU hardware
    pass
```

### Assertions
```python
from tests.utils import assert_contract_data_valid, assert_confidence_scores_valid

def test_contract_validation():
    contract_data = process_contract("test.pdf")
    assert_contract_data_valid(contract_data)
    assert_confidence_scores_valid(contract_data, min_confidence=0.7)
```

### Performance Monitoring
```python
from tests.utils import PerformanceMonitor, benchmark_function

def test_performance_monitoring():
    monitor = PerformanceMonitor()
    monitor.start("processing")
    # ... processing code ...
    duration = monitor.stop("processing")
    assert duration < 10.0

def test_benchmarking():
    stats = benchmark_function(my_function, arg1, arg2, iterations=10)
    assert stats["avg"] < 1.0
```

## Performance Testing

### Benchmarking
Performance tests use `pytest-benchmark` for accurate measurements:

```python
def test_document_processing_performance(benchmark):
    result = benchmark(process_document, "sample.pdf")
    assert result is not None

def test_batch_processing_performance(benchmark):
    files = ["file1.pdf", "file2.pdf", "file3.pdf"]
    result = benchmark(batch_process, files)
    assert len(result) == 3
```

### Performance Thresholds
Each test type has performance thresholds defined:

- Unit tests: < 5 seconds per operation
- Integration tests: < 30 seconds per workflow
- Performance tests: < 60 seconds per document
- E2E tests: < 120 seconds per complete workflow

## Security Testing

### Input Validation
```python
@pytest.mark.security
def test_file_upload_validation():
    # Test file type restrictions
    with pytest.raises(ValidationError):
        process_file("malicious.exe")

@pytest.mark.security  
def test_path_traversal_protection():
    # Test path traversal attacks
    with pytest.raises(SecurityError):
        process_file("../../../etc/passwd")
```

### Authentication and Authorization
```python
@pytest.mark.security
def test_unauthorized_access():
    # Test access control
    with pytest.raises(UnauthorizedError):
        api_client.get("/admin/config")
```

## Continuous Integration

### GitHub Actions Integration
The test suite integrates with GitHub Actions for automated testing:

```yaml
# .github/workflows/test.yml
- name: Run test suite
  run: |
    pytest --cov=src --cov-report=xml --junitxml=junit.xml
    
- name: Upload coverage
  uses: codecov/codecov-action@v1
  with:
    file: ./coverage.xml
```

### Test Matrix
Tests run across multiple environments:
- Python versions: 3.8, 3.9, 3.10, 3.11, 3.12
- Operating systems: Ubuntu, Windows, macOS
- Dependencies: Minimum and latest versions

## Test Quality Metrics

### Coverage Requirements
- **Minimum Coverage**: 90%
- **Branch Coverage**: Enabled
- **Line Coverage**: Required for all new code
- **Missing Coverage**: Reported in CI

### Performance Requirements
- **Unit Tests**: < 5 seconds total
- **Integration Tests**: < 5 minutes total
- **Full Test Suite**: < 15 minutes total
- **Performance Tests**: Baseline comparison

### Quality Gates
- All tests must pass
- Coverage must meet minimum threshold
- Performance must not regress
- Security tests must pass
- No critical linting issues

## Debugging Tests

### Running Single Tests
```bash
# Run single test with detailed output
pytest tests/test_config.py::TestConfigDefaults::test_default_config_values -v -s

# Run with debugger
pytest --pdb tests/test_config.py::test_failing_function

# Run with debugging output
pytest -s --log-cli-level=DEBUG tests/test_config.py
```

### Test Debugging Tips
1. Use `pytest -s` to see print statements
2. Use `pytest --pdb` to drop into debugger on failure
3. Use `pytest -x` to stop on first failure
4. Use `pytest --lf` to run only last failed tests
5. Use `pytest --tb=long` for detailed tracebacks

## Best Practices

### Writing Tests
1. **Test Naming**: Use descriptive names that explain what is being tested
2. **Test Structure**: Follow Arrange-Act-Assert pattern
3. **Test Isolation**: Each test should be independent
4. **Mock External Dependencies**: Use mocks for external services
5. **Test Edge Cases**: Include boundary conditions and error cases

### Test Organization
1. **Group Related Tests**: Use classes to group related test methods
2. **Use Appropriate Markers**: Mark tests with appropriate categories
3. **Share Setup**: Use fixtures for common setup code
4. **Parameterize Tests**: Use `@pytest.mark.parametrize` for multiple inputs
5. **Document Complex Tests**: Add docstrings explaining complex test logic

### Performance Considerations
1. **Fast Unit Tests**: Keep unit tests under 1 second each
2. **Minimize I/O**: Use in-memory data structures when possible
3. **Parallel Execution**: Ensure tests can run in parallel
4. **Resource Cleanup**: Always clean up resources in teardown
5. **Benchmark Regressions**: Monitor performance over time

## Troubleshooting

### Common Issues
1. **Import Errors**: Check PYTHONPATH and module installation
2. **Fixture Not Found**: Ensure fixture is in `conftest.py` or imported
3. **Tests Hanging**: Check for infinite loops or missing timeouts
4. **Flaky Tests**: Identify timing issues and race conditions
5. **Memory Issues**: Monitor memory usage in long-running tests

### Getting Help
1. Check test logs for detailed error messages
2. Run with increased verbosity: `pytest -v -s`
3. Use test debugging commands listed above
4. Check the test configuration and environment variables
5. Consult the main project documentation

## Contributing

When adding new tests:
1. Follow the existing test structure and naming conventions
2. Add appropriate markers for test categorization
3. Update this README if adding new test categories or utilities
4. Ensure new tests pass in all environments
5. Add performance tests for new features that process data

For questions or suggestions about the testing infrastructure, please open an issue or contact the development team.