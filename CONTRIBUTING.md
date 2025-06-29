# Contributing

Thank you for considering a contribution! Please follow these guidelines:

## Setup

1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   pip install -e .
   ```
2. Run quality checks before submitting a pull request:
   ```bash
   ruff check .
   bandit -r src
   pytest -q
   ```

## Pull Requests

- Keep changes focused and write descriptive commit messages.
- Update or add tests for new features.
- Ensure `pytest -q` passes locally.
- Reference any related issues in the PR description.

Happy coding!
