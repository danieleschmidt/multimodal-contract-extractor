# Development Guide

## Quick Setup

```bash
# Clone and setup
git clone <repository-url>
cd <repository-name>
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pip install -e .
```

## Development Workflow

1. **Code Quality**: Run `ruff check .` before commits
2. **Security**: Run `bandit -r src` for security analysis  
3. **Testing**: Run `pytest -q` for test suite
4. **Type Checking**: Use `mypy` for static type checking

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed system design.

## Resources

* [Contributing Guidelines](../CONTRIBUTING.md)
* [Security Policy](../SECURITY.md)
* [API Documentation](../API.md)
* [Python Development Guide](https://docs.python.org/3/tutorial/)
* [Testing Best Practices](https://docs.pytest.org/)