# ADR 006: Mandatory Type Hints and MyPy Static Type Checking

## Status
Accepted

## Context
The multimodal contract extractor is a complex Python application with multiple components, external integrations, and a growing codebase. As the project scales and more developers contribute, we need to ensure:

- **Code Quality**: Prevent type-related bugs and improve code reliability
- **Developer Experience**: Better IDE support with autocomplete and error detection
- **Documentation**: Types serve as inline documentation for function signatures
- **Refactoring Safety**: Safe refactoring with confidence in type consistency
- **API Contracts**: Clear contracts between different modules and components

Python's dynamic typing system provides flexibility but can lead to runtime errors that static typing could prevent.

## Decision
We will mandate comprehensive type hints throughout the codebase and use MyPy for static type checking in our CI/CD pipeline.

## Rationale

### Benefits of Type Hints:
- **Error Prevention**: Catch type-related errors before runtime
- **Improved IDE Support**: Better autocomplete, navigation, and refactoring tools
- **Self-documenting Code**: Type hints serve as inline documentation
- **Easier Onboarding**: New developers can understand code contracts more quickly
- **Refactoring Safety**: Confident refactoring with type checking validation
- **API Design**: Forces consideration of clear interfaces and data structures

### MyPy Benefits:
- **Gradual Typing**: Can be adopted incrementally without breaking existing code
- **Powerful Type System**: Supports advanced features like generics, unions, and protocols
- **Configurable**: Flexible configuration for different strictness levels
- **IDE Integration**: Works with popular IDEs and editors
- **Active Development**: Continuously improved with new Python features

### Considered Alternatives:
- **PyRight/Pylance**: Microsoft's type checker with excellent performance
- **Pyre**: Facebook's type checker with focus on performance
- **No Type Checking**: Maintain current dynamic typing approach
- **Partial Adoption**: Optional type hints without enforcement

## Implementation Strategy

### Type Hint Requirements:

#### 1. Function Signatures:
```python
# Required: All public functions must have type hints
def process_document(
    file_path: Path,
    config: ProcessingConfig,
    output_format: OutputFormat = OutputFormat.JSON
) -> ProcessingResult:
    """Process a document and extract clauses."""
    pass

# Required: Private functions should have type hints
def _validate_file_size(file_path: Path, max_size: int) -> bool:
    """Validate that file size is within limits."""
    pass
```

#### 2. Class Definitions:
```python
from typing import Protocol, TypeVar, Generic
from dataclasses import dataclass

@dataclass
class ProcessingConfig:
    """Configuration for document processing."""
    ocr_confidence_threshold: float
    max_file_size_mb: int
    output_format: OutputFormat
    enable_caching: bool = True

T = TypeVar('T')

class DocumentProcessor(Generic[T]):
    """Generic document processor."""
    
    def __init__(self, config: ProcessingConfig) -> None:
        self.config = config
    
    def process(self, document: Document) -> T:
        """Process document and return result."""
        pass
```

#### 3. Module-level Variables:
```python
from typing import Final, Dict, List

# Constants should be typed
DEFAULT_TIMEOUT: Final[int] = 30
SUPPORTED_FORMATS: Final[List[str]] = ['.pdf', '.png', '.jpg', '.jpeg']
ERROR_CODES: Final[Dict[str, int]] = {
    'INVALID_FILE': 400,
    'PROCESSING_ERROR': 500,
}
```

### MyPy Configuration:

#### `pyproject.toml` Configuration:
```toml
[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true
show_error_codes = true

# Per-module configuration for external libraries
[[tool.mypy.overrides]]
module = [
    "streamlit.*",
    "pdf2image.*",
    "pytesseract.*",
    "prometheus_client.*",
]
ignore_missing_imports = true

# Stricter settings for core modules
[[tool.mypy.overrides]]
module = "multimodal_contract_extractor.*"
disallow_any_generics = true
disallow_subclassing_any = true
disallow_untyped_calls = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
warn_return_any = true
```

### Gradual Adoption Strategy:

#### Phase 1: Core Modules (Weeks 1-2)
- Add type hints to `src/multimodal_contract_extractor/config.py`
- Add type hints to `src/multimodal_contract_extractor/security.py`
- Add type hints to `src/multimodal_contract_extractor/metrics.py`
- Configure basic MyPy checking

#### Phase 2: Processing Components (Weeks 3-4)
- Add type hints to `src/multimodal_contract_extractor/document.py`
- Add type hints to `src/multimodal_contract_extractor/extraction.py`
- Add type hints to `src/multimodal_contract_extractor/clause_detection.py`
- Enable stricter MyPy settings

#### Phase 3: Interfaces and CLI (Weeks 5-6)
- Add type hints to CLI utilities and web application
- Add type hints to serialization and health check modules
- Enable full MyPy enforcement in CI/CD

#### Phase 4: Tests and Utilities (Weeks 7-8)
- Add type hints to test files
- Add type hints to utility scripts
- Achieve 100% type coverage

### Advanced Type System Usage:

#### 1. Protocols for Duck Typing:
```python
from typing import Protocol

class Extractable(Protocol):
    """Protocol for objects that can extract text."""
    
    def extract_text(self, confidence_threshold: float) -> str:
        """Extract text with minimum confidence."""
        ...
    
    def get_confidence_score(self) -> float:
        """Get overall confidence score."""
        ...
```

#### 2. Generic Types for Reusability:
```python
from typing import TypeVar, Generic, List

T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')

class ProcessingPipeline(Generic[T]):
    """Generic processing pipeline."""
    
    def __init__(self, processors: List[Processor[T]]) -> None:
        self.processors = processors
    
    def process(self, input_data: T) -> T:
        """Process data through pipeline."""
        result = input_data
        for processor in self.processors:
            result = processor.process(result)
        return result
```

#### 3. Union Types for Flexible APIs:
```python
from typing import Union, Optional
from pathlib import Path

FileInput = Union[str, Path, bytes]
ProcessingResult = Union[SuccessResult, ErrorResult]

def load_document(
    source: FileInput,
    encoding: Optional[str] = None
) -> ProcessingResult:
    """Load document from various input types."""
    pass
```

### Type Checking Integration:

#### CI/CD Integration:
```yaml
# .github/workflows/ci.yml
- name: Type checking with MyPy
  run: |
    mypy src/
    mypy tests/ --ignore-missing-imports
```

#### Pre-commit Hook:
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-Pillow, types-requests]
        args: [--strict, --ignore-missing-imports]
```

#### IDE Integration:
```json
// .vscode/settings.json
{
  "python.linting.mypyEnabled": true,
  "python.linting.enabled": true,
  "python.analysis.typeCheckingMode": "strict"
}
```

## Type Hint Standards

### Required Patterns:

#### 1. Function Return Types:
```python
# Good: Explicit return type
def calculate_confidence(scores: List[float]) -> float:
    return sum(scores) / len(scores)

# Bad: Missing return type
def calculate_confidence(scores: List[float]):
    return sum(scores) / len(scores)
```

#### 2. Exception Handling:
```python
from typing import Optional

def safe_division(a: float, b: float) -> Optional[float]:
    """Safely divide two numbers."""
    try:
        return a / b
    except ZeroDivisionError:
        return None
```

#### 3. Async Functions:
```python
from typing import Awaitable
import asyncio

async def process_document_async(
    document: Document
) -> ProcessingResult:
    """Asynchronously process document."""
    await asyncio.sleep(0.1)  # Simulate async work
    return ProcessingResult()
```

### Forbidden Patterns:

#### 1. Any Type Usage:
```python
from typing import Any

# Avoid: Using Any defeats the purpose of type checking
def process_data(data: Any) -> Any:
    return data

# Prefer: Specific types or generics
T = TypeVar('T')
def process_data(data: T) -> T:
    return data
```

#### 2. Bare Except Clauses:
```python
# Avoid: Bare except with no type information
try:
    result = risky_operation()
except:
    return None

# Prefer: Specific exception types
try:
    result = risky_operation()
except (ValueError, TypeError) as e:
    logger.error(f"Operation failed: {e}")
    return None
```

## Development Workflow

### Type Checking Commands:
```bash
# Check entire codebase
mypy src/

# Check specific module with verbose output
mypy src/multimodal_contract_extractor/config.py --verbose

# Generate type coverage report
mypy src/ --html-report mypy-report/

# Check for unused type ignores
mypy src/ --warn-unused-ignores
```

### Type Stub Management:
```bash
# Install type stubs for external libraries
pip install types-Pillow types-requests

# Generate stub files for libraries without stubs
stubgen -p external_library -o stubs/
```

## Quality Metrics

### Type Coverage Targets:
- **Core modules**: 100% type coverage
- **Utility modules**: 95% type coverage
- **Test files**: 90% type coverage
- **Script files**: 85% type coverage

### MyPy Error Tolerance:
- **Production code**: 0 MyPy errors allowed
- **Test code**: 0 MyPy errors allowed (with appropriate ignores)
- **Legacy code**: Gradual improvement plan with tracked progress

## Consequences

### Positive:
- **Bug Prevention**: Significant reduction in type-related runtime errors
- **Development Speed**: Faster development with better IDE support
- **Code Quality**: Improved overall code quality and maintainability
- **Documentation**: Types serve as always-up-to-date documentation
- **Refactoring Confidence**: Safe large-scale refactoring operations
- **New Developer Onboarding**: Easier for new developers to understand codebase

### Negative:
- **Initial Investment**: Significant time required for initial type hint addition
- **Maintenance Overhead**: Types need to be maintained alongside code changes
- **Learning Curve**: Team needs to learn advanced typing concepts
- **CI/CD Complexity**: Additional step in build pipeline
- **External Dependencies**: Some libraries lack good type stub support

### Risks and Mitigations:
- **Risk**: Developer resistance due to perceived overhead
  - **Mitigation**: Gradual adoption, training, and demonstrating benefits
- **Risk**: False sense of security from type checking
  - **Mitigation**: Combine with comprehensive testing and runtime validation
- **Risk**: Over-complicated type annotations
  - **Mitigation**: Establish clear guidelines and code review standards

## Training and Documentation

### Developer Training:
1. **Type Hints Basics**: Introduction to Python type hints
2. **MyPy Usage**: Practical MyPy usage and configuration
3. **Advanced Types**: Generics, protocols, and advanced patterns
4. **Best Practices**: Team-specific guidelines and standards

### Documentation Requirements:
- **Type Hint Guidelines**: Comprehensive style guide
- **MyPy Configuration**: Detailed explanation of settings
- **Common Patterns**: Library of common typing patterns
- **Troubleshooting**: Common MyPy errors and solutions

## References
- [PEP 484 - Type Hints](https://www.python.org/dev/peps/pep-0484/)
- [MyPy Documentation](https://mypy.readthedocs.io/)
- [Python Type Checking Guide](https://realpython.com/python-type-checking/)
- [Typing Best Practices](https://typing.readthedocs.io/en/latest/spec/best_practices.html)

## Revision History
- 2024-01-18: Initial version
- 2024-01-20: Added gradual adoption strategy and advanced patterns
- 2024-01-22: Updated with training and documentation requirements