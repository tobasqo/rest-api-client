# Restic

[![PyPI version](https://badge.fury.io/py/restic.svg)](https://pypi.org/project/restic/)
[![Python versions](https://img.shields.io/pypi/pyversions/restic.svg)](https://pypi.org/project/restic/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A modern, type-safe Python library for building robust REST API clients with automatic Pydantic validation, async support, and extensible route patterns.

## Features

- **Type Safety**: Full type hints and Pydantic model validation for requests and responses
- **Async Support**: Both synchronous and asynchronous operations
- **Generic Routes**: Reusable route classes for common REST operations (CRUD)
- **Error Handling**: Comprehensive exception handling with detailed error messages
- **Flexible Configuration**: Customizable timeouts, authentication, and headers
- **Extensible**: Easy to extend with custom mixins and route logic

## Installation

**Requirements:** Python 3.10+

```bash
pip install restic
```

Or with UV:

```bash
uv add restic
```

## Dependencies

- **httpx**: HTTP client for making requests
- **pydantic**: Data validation and serialization
- **typing-extensions**: Enhanced type hints for older Python versions

## Usage & Examples

The package provides a `ResticClient` base class and reusable route mixins for building type-safe API clients. Routes are composed using mixins for different HTTP operations, with automatic request/response validation via Pydantic models.

See the `examples/` directory for complete usage examples:

- `json_placeholder.py`: Full example with JSONPlaceholder API

The code is simple enough that users can learn how to use it directly from the source code and examples.

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/tobasqo/restic.git
cd restic

# Install with UV
uv sync
```

### Testing

```bash
# Run tests
uv run pytest

# Run linting
uv run ruff check .

# Run formatting
uv run ruff format .

# Run type checking
uv run mypy .
```

### Building

```bash
# Build the package
uv build
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## References

These libraries are not integrated into the package but are worth mentioning for users who want to extend functionality:

- [Tenacity](https://tenacity.readthedocs.io/en/latest/) - retry on errors
- [HTTPX Limiter](https://pypi.org/project/httpx-limiter/) - rate limiting
- [Async usage of httpx](https://oneuptime.com/blog/post/2026-02-03-python-httpx-async-requests/view)
