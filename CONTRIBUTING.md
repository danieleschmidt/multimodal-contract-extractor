# Contributing to Multimodal Contract Extractor

Thank you for your interest in contributing to the Multimodal Contract Extractor! We welcome contributions from the community and appreciate your help in making this project better.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Security](#security)
- [Community and Support](#community-and-support)

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Git
- Docker (optional, for containerized development)
- Node.js (for documentation builds)

### Local Environment Setup

1. **Fork and clone the repository**:
   ```bash
   git clone https://github.com/your-username/multimodal-contract-extractor.git
   cd multimodal-contract-extractor
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   pip install -e .
   ```

4. **Install pre-commit hooks** (recommended):
   ```bash
   pre-commit install
   ```

5. **Verify setup**:
   ```bash
   python -c "import multimodal_contract_extractor; print('Setup successful!')"
   pytest --version
   ruff --version
   ```

### Docker Development (Alternative)

```bash
# Build development container
docker-compose -f docker-compose.dev.yml build

# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# Access development container
docker-compose -f docker-compose.dev.yml exec app bash
```

## Development Workflow

### Branch Strategy

- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/<name>`: New features
- `bugfix/<name>`: Bug fixes
- `hotfix/<name>`: Critical fixes for production

### Making Changes

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the coding standards

3. **Run quality checks**:
   ```bash
   # Code formatting and linting
   ruff check .
   ruff format .
   
   # Security checks
   bandit -r src -q
   
   # Type checking
   mypy src/
   
   # Run tests
   pytest -v
   ```

4. **Commit your changes** with clear commit messages:
   ```bash
   git add .
   git commit -m "feat: add new clause detection algorithm"
   ```

5. **Push and create pull request**:
   ```bash
   git push origin feature/your-feature-name
   ```

## Pull Request Process

### Before Submitting

- [ ] Code follows project style guidelines
- [ ] Tests pass locally (`pytest`)
- [ ] Security checks pass (`bandit -r src`)
- [ ] Type checks pass (`mypy src/`)
- [ ] Documentation is updated if needed
- [ ] Commit messages follow conventional format

### Pull Request Template

```markdown
## Description
Brief description of changes and motivation.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work)
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Tests pass locally
- [ ] Documentation updated
```

### Review Process

1. **Automated Checks**: CI/CD pipeline runs automated tests
2. **Code Review**: Maintainers review code for quality and design
3. **Testing**: Changes are tested in staging environment
4. **Approval**: Required approvals from maintainers
5. **Merge**: Changes merged to main branch

## Coding Standards

### Python Style Guide

- Follow [PEP 8](https://pep8.org/) style guide
- Use [ruff](https://docs.astral.sh/ruff/) for linting and formatting
- Maximum line length: 88 characters
- Use type hints for all function signatures
- Write descriptive docstrings for public APIs

### Naming Conventions

- **Functions and variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private methods**: `_leading_underscore`
- **Modules**: `lowercase` or `snake_case`

### Code Organization

```python
"""Module docstring describing purpose and usage."""

import standard_library
import third_party_packages
import local_modules

# Constants
DEFAULT_TIMEOUT = 30

# Type definitions
ConfigType = Dict[str, Any]

class ExampleClass:
    """Class docstring with usage examples."""
    
    def __init__(self, config: ConfigType) -> None:
        """Initialize with configuration."""
        self.config = config
    
    def public_method(self, param: str) -> bool:
        """Public method with clear docstring."""
        return self._private_method(param)
    
    def _private_method(self, param: str) -> bool:
        """Private method implementation."""
        return len(param) > 0
```

### Error Handling

- Use specific exception types
- Include helpful error messages
- Log errors with appropriate severity
- Clean up resources in finally blocks

```python
try:
    result = process_document(file_path)
except FileNotFoundError:
    logger.error(f"Document not found: {file_path}")
    raise DocumentProcessingError(f"File not found: {file_path}")
except Exception as e:
    logger.exception(f"Unexpected error processing {file_path}")
    raise DocumentProcessingError(f"Processing failed: {e}") from e
```

## Testing Guidelines

### Test Structure

```
tests/
├── unit/                 # Unit tests for individual components
├── integration/          # Integration tests for component interaction
├── e2e/                 # End-to-end tests for full workflows
├── performance/         # Performance and load tests
├── fixtures/            # Test data and fixtures
└── conftest.py          # Shared test configuration
```

### Writing Tests

- Use descriptive test names: `test_should_extract_clauses_when_pdf_is_valid`
- Follow AAA pattern: Arrange, Act, Assert
- Use fixtures for common test data
- Mock external dependencies
- Test both happy path and error conditions

```python
def test_should_extract_clauses_when_pdf_is_valid():
    # Arrange
    document = load_test_document("sample_contract.pdf")
    extractor = ClauseExtractor()
    
    # Act
    clauses = extractor.extract(document)
    
    # Assert
    assert len(clauses) > 0
    assert all(clause.confidence > 0.7 for clause in clauses)
```

### Test Coverage

- Maintain >90% code coverage
- Focus on critical business logic
- Include edge cases and error conditions
- Use coverage reports to identify gaps

```bash
# Run tests with coverage
pytest --cov=src --cov-report=html --cov-report=term

# View coverage report
open htmlcov/index.html
```

## Documentation

### Types of Documentation

1. **Code Documentation**: Docstrings, comments, type hints
2. **API Documentation**: Automatically generated from docstrings
3. **User Guide**: Setup, usage examples, best practices
4. **Developer Guide**: Architecture, contributing, deployment

### Documentation Standards

- Use clear, concise language
- Include code examples
- Keep documentation up-to-date with code changes
- Use consistent formatting and style

### Building Documentation

```bash
# Install documentation dependencies
pip install -r requirements-docs.txt

# Build documentation
mkdocs build

# Serve documentation locally
mkdocs serve
```

## Security

### Security Guidelines

- Never commit secrets or credentials
- Use environment variables for configuration
- Validate all user inputs
- Follow secure coding practices
- Report security issues privately

### Security Testing

```bash
# Security vulnerability scanning
bandit -r src/

# Dependency vulnerability checking
safety check

# License compatibility checking
pip-licenses --with-license-file --no-license-path
```

### Reporting Security Issues

Please report security vulnerabilities to security@example.com. Do not file public issues for security vulnerabilities.

## Community and Support

### Getting Help

- **GitHub Issues**: Bug reports and feature requests
- **Discussions**: General questions and community support
- **Documentation**: Comprehensive guides and API reference
- **Email**: Direct contact for sensitive issues

### Contributing Areas

We welcome contributions in these areas:

- **Core Features**: OCR improvements, ML model enhancements
- **Integrations**: Third-party service connectors
- **Documentation**: User guides, tutorials, examples
- **Testing**: Test coverage, performance tests
- **Localization**: Multi-language support
- **Accessibility**: UI/UX improvements

### Recognition

Contributors are recognized through:

- GitHub contributor graphs
- Release notes acknowledgments
- Community showcases
- Swag and rewards for significant contributions

### Communication Channels

- **GitHub**: Issues, pull requests, discussions
- **Email**: project-maintainers@example.com
- **Community**: Monthly contributor calls

## Getting Started Ideas

Looking for ways to contribute? Here are some good first issues:

- **Documentation**: Improve setup guides or add examples
- **Testing**: Add test cases for edge conditions
- **Bug Fixes**: Address issues labeled "good first issue"
- **Features**: Implement features labeled "help wanted"

Thank you for contributing to the Multimodal Contract Extractor! Your contributions help make legal document processing more accessible and efficient for everyone.
