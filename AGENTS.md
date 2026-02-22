# Agent Guidelines for pyOpenSourceProjects

This file provides guidelines and commands for agentic coding agents working in this repository.

## Project Overview

Python library for checking open source projects for standard compliance (README, GitHub workflow, pyproject.toml). Creates badges for projects.

- **Main package**: `osprojects/`
- **Tests**: `tests/`
- **Python**: 3.10+

## Build & Installation

```bash
# Install package in development mode
pip install . -U

# Install with test dependencies
pip install . -U[test]
```

## Testing

### Run All Tests

```bash
# Using unittest discover (default)
python3 -m unittest discover

# Using the test script
./scripts/test
```

### Run Single Test

```bash
# Run a specific test file
python -m unittest tests.test_github

# Run a specific test class
python -m unittest tests.test_github.GitHubTest

# Run a specific test method
python -m unittest tests.test_github.GitHubTest.test_example

# Module-wise testing (runs each test file separately)
./scripts/test --module
```

### Other Test Runners

```bash
# Using green
./scripts/test --green

# Using tox
./scripts/test --tox
```

## Code Formatting

This project uses multiple formatters. Run all before committing:

```bash
# Format code with black, sort imports with isort, format docstrings with docformatter
./scripts/blackisort
```

Individual commands:
```bash
# Sort imports
isort tests/*.py osprojects/*.py

# Format code
black tests/*.py osprojects/*.py

# Format docstrings
docformatter --in-place tests/*.py osprojects/*.py
```

## Code Style Guidelines

### General

- Follow [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- Use type hints where appropriate
- Maximum line length: 88 characters (Black default)

### Imports

- Use `isort` for import sorting
- Order: standard library, third-party, local
- Example:
```python
import os
import time
from typing import Any, Optional

import requests
from git import Repo

from osprojects import __version__
from osprojects.github_api import GitHubAPI
```

### Docstrings

- Use Google-style docstrings
- Run `docformatter` before committing
- Example:
```python
def fetch_data(url: str, timeout: int = 30) -> dict:
    """Fetch data from the given URL.

    Args:
        url: The URL to fetch data from.
        timeout: Request timeout in seconds.

    Returns:
        A dictionary containing the response data.

    Raises:
        requests.RequestException: If the request fails.
    """
```

### Naming Conventions

- **Functions/methods**: `snake_case` (e.g., `fetch_data`, `get_project_info`)
- **Classes**: `PascalCase` (e.g., `GitHubAPI`, `ProjectChecker`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_TIMEOUT`, `API_VERSION`)
- **Private methods**: prefix with `_` (e.g., `_internal_method`)

### Error Handling

- Use specific exception types
- Include informative error messages
- Example:
```python
try:
    result = api.request(endpoint)
except requests.RequestException as e:
    raise APIError(f"Failed to fetch {endpoint}: {e}") from e
```

### Testing Guidelines

- Test files: `tests/test_*.py`
- Test classes: `Test*` (e.g., `GitHubTest`)
- Test methods: `test_*` (e.g., `test_fetch_projects`)
- Use the `BaseTest` class from `tests/basetest.py` for common functionality
- Include docstrings in tests explaining what is being tested

### Type Hints

- Use type hints for function signatures
- Prefer `Optional[X]` over `X | None`
- Use `Any` sparingly
- Example:
```python
def process_items(items: list[dict], filter_key: str) -> Optional[list[str]]:
    """Process items and return filtered values."""
    values = [item.get(filter_key) for item in items if filter_key in item]
    return values if values else None
```

## Version Bumping

The package version is stored in `osprojects/__init__.py` and mirrored in `osprojects/version.py`.

To bump the version:

1. Edit `osprojects/__init__.py` and update `__version__`
2. Edit `osprojects/version.py` and update the `version`, `updated` fields in the `Version` class

```python
# osprojects/__init__.py
__version__ = "0.5.1"

# osprojects/version.py  — Version class fields to update:
version = osprojects.__version__   # reads from __init__.py automatically
updated = "2026-02-22"             # set to today's date
```

Then run formatters, tests, commit and push (or use `scripts/release`).

## Git Workflow

1. Create a feature branch
2. Make changes following the code style guidelines
3. Run formatters: `./scripts/blackisort`
4. Run tests: `./scripts/test`
5. Commit with a descriptive message
6. Push and create a pull request

## Release

```bash
# Builds docs and commits + pushes
./scripts/release
```

## CLI Commands

The package provides these CLI entry points:

- `checkos`: Main CLI for checking open source projects
- `issue2ticket`: Convert issues to tickets
- `gitlog2wiki`: Convert git log to wiki format
