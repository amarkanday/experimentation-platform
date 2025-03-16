#!/usr/bin/env python3
"""
Configuration Files Generator for Experimentation Platform

This script generates all necessary code style and configuration files
for the experimentation platform backend and places them in the appropriate
locations.
"""

import os
import sys

# Configuration file contents
CONFIG_FILES = {
    ".editorconfig": """# EditorConfig is awesome: https://EditorConfig.org

# top-most EditorConfig file
root = true

# Unix-style newlines with a newline ending every file
[*]
end_of_line = lf
insert_final_newline = true
charset = utf-8
trim_trailing_whitespace = true
indent_style = space
indent_size = 4

# 2 space indentation for specific file types
[*.{yml,yaml,json,js,jsx,ts,tsx,css,scss,html}]
indent_size = 2

# Tab indentation for Makefiles
[Makefile]
indent_style = tab

# Markdown files
[*.md]
trim_trailing_whitespace = false
""",
    ".flake8": """[flake8]
max-line-length = 88
exclude = .git,__pycache__,docs/,old/,build/,dist/,venv/,.venv/,alembic/
ignore = E203, E266, E501, W503
# E203: whitespace before ':'
# E266: too many leading '#' for block comment
# E501: line too long
# W503: line break before binary operator
select = B,C,E,F,W,T4,B9
""",
    "pyproject.toml": r"""[tool.black]
line-length = 88
target-version = ['py39']
include = '\.pyi?$'
exclude = '''
/(
    \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | _build
  | buck-out
  | build
  | dist
  | alembic
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true
line_length = 88
skip_glob = ["*/alembic/*"]

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
strict_optional = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
disallow_incomplete_defs = false

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_functions = "test_*"
python_classes = "Test*"
addopts = "--cov=app --cov-report=term-missing --no-cov-on-fail"
""",
    ".pre-commit-config.yaml": """repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
    -   id: trailing-whitespace
    -   id: end-of-file-fixer
    -   id: check-yaml
    -   id: check-added-large-files
    -   id: debug-statements

-   repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
    -   id: isort

-   repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
    -   id: black

-   repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
    -   id: flake8
        additional_dependencies: [flake8-docstrings]

-   repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.1
    hooks:
    -   id: mypy
        additional_dependencies: [types-requests, types-PyYAML, pydantic]
""",
    ".gitignore": """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
ENV/
env.bak/
venv.bak/
.pytest_cache/
.coverage
htmlcov/
.tox/
.nox/
.hypothesis/
.pytest_cache/
cover/
*.cover
*.py,cover
.hypothesis/
.pytest_cache/

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Environments
.env
.env.*
!.env.example

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# IDEs
.idea
.vscode
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Databases
*.sqlite3
*.db

# Logs
logs/
*.log
""",
    "setup.cfg": """[metadata]
name = experimentation-platform
version = 0.1.0
description = Experimentation platform for A/B testing and feature flags
author = Your Name
author_email = your.email@example.com
license = MIT

[options]
packages = find:
python_requires = >=3.9

[options.packages.find]
exclude =
    tests
    tests.*

[bdist_wheel]
universal = 0
""",
    ".vscode/settings.json": """{
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "python.testing.nosetestsEnabled": false,
  "python.testing.pytestArgs": [
    "tests"
  ],
  "[python]": {
    "editor.rulers": [
      88
    ]
  },
  "files.exclude": {
    "**/__pycache__": true,
    "**/.pytest_cache": true,
    "**/*.pyc": true,
    "**/.mypy_cache": true
  }
}
""",
    ".env.example": """# Development settings
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/experimentation
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=experimentation
REDIS_HOST=localhost
REDIS_PORT=6379
AWS_PROFILE=experimentation-dev
AWS_REGION=us-east-1
SECRET_KEY=development_secret_key_change_in_production
ENVIRONMENT=development
LOG_LEVEL=DEBUG
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
""",
}


def create_directory(path):
    """Create a directory if it doesn't exist."""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")
    else:
        print(f"Directory already exists: {path}")


def create_file(path, content):
    """Create a file with the given content."""
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        create_directory(directory)

    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write(content)
        print(f"Created file: {path}")
    else:
        print(f"File already exists: {path}")


def generate_config_files(base_dir):
    """Generate all configuration files in the appropriate locations."""
    print(f"Generating configuration files in: {base_dir}")

    # Create base directory if it doesn't exist
    create_directory(base_dir)

    # Create root level configuration files
    for filename, content in CONFIG_FILES.items():
        # Handle .vscode directory specially
        if filename.startswith(".vscode/"):
            rel_path = os.path.join(base_dir, filename)
            create_file(rel_path, content)
        else:
            rel_path = os.path.join(base_dir, filename)
            create_file(rel_path, content)

    print("\nConfiguration file generation complete!")


if __name__ == "__main__":
    # Get base directory from command line or use current directory
    if len(sys.argv) > 1:
        base_directory = sys.argv[1]
    else:
        base_directory = os.getcwd()

    generate_config_files(base_directory)
