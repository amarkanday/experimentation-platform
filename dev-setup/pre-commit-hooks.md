# Pre-commit Hooks for Code Quality

This document describes the pre-commit hooks configuration for the experimentation platform project. These hooks automatically check code quality before each commit, preventing code that doesn't meet quality standards from being committed.

## Setup Instructions

1. Install pre-commit:

```bash
pip install pre-commit
```

2. Create a `.pre-commit-config.yaml` file in the project root with the following content:

```yaml
repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
    -   id: trailing-whitespace
    -   id: end-of-file-fixer
    -   id: check-yaml
    -   id: check-json
    -   id: check-added-large-files
    -   id: check-merge-conflict
    -   id: debug-statements
    -   id: detect-private-key
    -   id: check-toml
    -   id: check-case-conflict

-   repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
    -   id: isort
        args: ["--profile", "black"]

-   repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
    -   id: black

-   repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
    -   id: flake8
        additional_dependencies: [
            flake8-docstrings,
            flake8-comprehensions,
            flake8-bugbear,
            flake8-annotations,
            flake8-builtins,
            pep8-naming,
        ]

-   repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.1
    hooks:
    -   id: mypy
        additional_dependencies: [
            types-requests,
            types-PyYAML,
            pydantic>=2.0.0,
            types-setuptools,
            sqlalchemy[mypy]>=2.0.0,
        ]
        exclude: ^(alembic/|tests/)

-   repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
    -   id: bandit
        args: ["-c", "pyproject.toml"]
        additional_dependencies: ["bandit[toml]"]

-   repo: https://github.com/pycqa/pylint
    rev: v2.17.5
    hooks:
    -   id: pylint
        args: ["--disable=C0111", "--disable=C0103", "--disable=C0303", "--disable=C0330", "--disable=C0326"]
        exclude: ^(tests/|alembic/)

-   repo: https://github.com/nbQA-dev/nbQA
    rev: 1.7.0
    hooks:
    -   id: nbqa-black
        additional_dependencies: [black==23.7.0]
    -   id: nbqa-isort
        additional_dependencies: [isort==5.12.0]

-   repo: https://github.com/asottile/pyupgrade
    rev: v3.10.1
    hooks:
    -   id: pyupgrade
        args: [--py39-plus]

# Frontend checks
-   repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.0.3
    hooks:
    -   id: prettier
        types_or: [javascript, jsx, ts, tsx, json, yaml, css, scss, html, markdown]

-   repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.48.0
    hooks:
    -   id: eslint
        files: \.(js|jsx|ts|tsx)$
        types: [file]
        additional_dependencies:
        -   eslint@8.48.0
        -   eslint-config-prettier@9.0.0
        -   eslint-plugin-react@7.33.2
        -   eslint-plugin-react-hooks@4.6.0
        -   eslint-plugin-import@2.28.1
        -   typescript@5.2.2
        -   @typescript-eslint/eslint-plugin@6.6.0
        -   @typescript-eslint/parser@6.6.0
```

3. Install the pre-commit hooks:

```bash
pre-commit install
```

4. (Optional) Run the hooks on all files:

```bash
pre-commit run --all-files
```

## Included Hooks

### Basic File Checks

-   `trailing-whitespace`: Trims trailing whitespace
-   `end-of-file-fixer`: Ensures files end with a newline
-   `check-yaml`: Validates YAML syntax
-   `check-json`: Validates JSON syntax
-   `check-added-large-files`: Prevents large files from being committed
-   `check-merge-conflict`: Checks for merge conflict strings
-   `debug-statements`: Checks for debugger imports and py.test breakpoints
-   `detect-private-key`: Checks for private keys
-   `check-toml`: Validates TOML syntax
-   `check-case-conflict`: Checks for files with names that would conflict on case-insensitive filesystems

### Python Formatting

-   `isort`: Sorts imports alphabetically and automatically separated into sections
-   `black`: Formats Python code according to the Black style

### Python Linting

-   `flake8`: Checks code against PEP 8 style guide with additional plugins for:
    -   `flake8-docstrings`: Validates docstrings
    -   `flake8-comprehensions`: Helps write better list/set/dict comprehensions
    -   `flake8-bugbear`: Finds likely bugs and design problems
    -   `flake8-annotations`: Checks for presence of type annotations
    -   `flake8-builtins`: Checks for uses of Python builtins as variables or parameters
    -   `pep8-naming`: Checks PEP 8 naming conventions
-   `mypy`: Static type checker for Python
-   `bandit`: Finds common security issues in Python code
-   `pylint`: Python static code analyzer

### Python Modernization

-   `pyupgrade`: Automatically upgrades syntax for newer versions of Python

### Notebook Quality

-   `nbqa-black`: Runs Black on Jupyter Notebooks
-   `nbqa-isort`: Runs isort on Jupyter Notebooks

### Frontend Checks

-   `prettier`: Formats JavaScript, TypeScript, CSS, HTML, and JSON files
-   `eslint`: Lints JavaScript and TypeScript files with React support

## Usage Tips

1. **Skipping Hooks**: In rare cases when you need to bypass the hooks, you can use:

    ```bash
    git commit -m "Your message" --no-verify
    ```

    But this should be avoided whenever possible.

2. **Handling Large Changes**: If you're making large-scale formatting changes:

    ```bash
    pre-commit run isort --all-files
    pre-commit run black --all-files
    ```

3. **Updating Hooks**: Periodically update your hooks to the latest versions:

    ```bash
    pre-commit autoupdate
    ```

4. **Configuring Specific Hooks**: Most hooks can be configured in their respective configuration files:
    - Black and isort: `pyproject.toml`
    - Flake8: `.flake8`
    - MyPy: `pyproject.toml`
    - ESLint: `.eslintrc.js`
    - Prettier: `.prettierrc`

## Benefits of Using Pre-commit Hooks

-   **Consistency**: Ensures all code follows the same style guidelines
-   **Quality**: Catches common errors and anti-patterns before they're committed
-   **Security**: Identifies potential security issues early
-   **Efficiency**: Automates routine code review tasks
-   **Learning**: Helps developers learn best practices through immediate feedback
