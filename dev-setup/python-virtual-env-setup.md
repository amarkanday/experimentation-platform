# Python Virtual Environment Setup Guide

This guide outlines how to set up and configure a Python virtual environment for the Experimentation Platform project.

## Directory Structure

Create a `requirements` directory with the following files to manage dependencies across different environments:

```
requirements/
├── base.txt        # Base dependencies used in all environments
├── dev.txt         # Development dependencies
├── test.txt        # Testing dependencies
└── prod.txt        # Production dependencies
```

## Requirements Files

### Base Requirements (requirements/base.txt)

```
# API Framework
fastapi==0.103.1
uvicorn[standard]==0.23.2
pydantic==2.3.0
pydantic-settings==2.0.3
email-validator==2.0.0.post2
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# Database & ORM
sqlalchemy==2.0.20
alembic==1.12.0
psycopg2-binary==2.9.7
asyncpg==0.28.0
redis==4.6.0
boto3==1.28.40

# Utilities
python-dateutil==2.8.2
pyyaml==6.0.1
jinja2==3.1.2
tenacity==8.2.3
structlog==23.1.0
orjson==3.9.5

# Analytics
numpy==1.25.2
scipy==1.11.2
pandas==2.1.0
```

### Development Requirements (requirements/dev.txt)

```
-r base.txt

# Development Tools
black==23.7.0
isort==5.12.0
mypy==1.5.1
flake8==6.1.0
pre-commit==3.4.0

# Documentation
mkdocs==1.5.3
mkdocs-material==9.2.8
mkdocstrings==0.22.0

# Debugging
ipython==8.15.0
debugpy==1.6.7
```

### Test Requirements (requirements/test.txt)

```
-r base.txt

# Testing
pytest==7.4.2
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-mock==3.11.1
httpx==0.24.1
faker==19.6.2
factory-boy==3.3.0
freezegun==1.2.2
```

### Production Requirements (requirements/prod.txt)

```
-r base.txt

# Monitoring & Tracing
opentelemetry-api==1.19.0
opentelemetry-sdk==1.19.0
opentelemetry-exporter-otlp==1.19.0
prometheus-client==0.17.1

# Production WSGI server
gunicorn==21.2.0
```

## Setup Scripts

### Unix/Linux/macOS Setup Script (setup_venv.sh)

```bash
#!/bin/bash
# Script to set up Python virtual environment

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Setting up Python virtual environment for Experimentation Platform...${NC}"

# Check if Python 3.9+ is installed
python_version=$(python3 --version 2>&1 | awk '{print $2}')
if [[ $(echo $python_version | cut -d. -f1-2 | sed 's/\.//') -lt 39 ]]; then
    echo "Python 3.9 or higher is required. You have $python_version"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
else
    echo -e "${YELLOW}Virtual environment already exists.${NC}"
fi

# Activate the virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies based on environment
if [ "$1" = "dev" ] || [ -z "$1" ]; then
    echo -e "${YELLOW}Installing development dependencies...${NC}"
    pip install -r requirements/dev.txt
elif [ "$1" = "test" ]; then
    echo -e "${YELLOW}Installing test dependencies...${NC}"
    pip install -r requirements/test.txt
elif [ "$1" = "prod" ]; then
    echo -e "${YELLOW}Installing production dependencies...${NC}"
    pip install -r requirements/prod.txt
else
    echo "Unknown environment: $1"
    echo "Usage: ./setup_venv.sh [dev|test|prod]"
    exit 1
fi

# Install pre-commit hooks if in dev environment
if [ "$1" = "dev" ] || [ -z "$1" ]; then
    echo -e "${YELLOW}Installing pre-commit hooks...${NC}"
    pre-commit install
fi

echo -e "${GREEN}Virtual environment setup complete!${NC}"
echo -e "${YELLOW}To activate the virtual environment, run:${NC} source venv/bin/activate"
```

### Windows Setup Script (setup_venv.bat)

```batch
@echo off
echo Setting up Python virtual environment for Experimentation Platform...

REM Check if Python 3.9+ is installed
for /f "tokens=2" %%I in ('python --version 2^>^&1') do set python_version=%%I
for /f "tokens=1,2 delims=." %%a in ("%python_version%") do (
    set major=%%a
    set minor=%%b
)
if %major% LSS 3 (
    echo Python 3.9 or higher is required. You have %python_version%
    exit /b 1
)
if %major%==3 if %minor% LSS 9 (
    echo Python 3.9 or higher is required. You have %python_version%
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
) else (
    echo Virtual environment already exists.
)

REM Activate the virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

REM Upgrade pip
echo Upgrading pip...
pip install --upgrade pip

REM Install dependencies based on environment
if "%1"=="dev" goto dev
if "%1"=="test" goto test
if "%1"=="prod" goto prod
if "%1"=="" goto dev

echo Unknown environment: %1
echo Usage: setup_venv.bat [dev^|test^|prod]
exit /b 1

:dev
echo Installing development dependencies...
pip install -r requirements\dev.txt
echo Installing pre-commit hooks...
pre-commit install
goto end

:test
echo Installing test dependencies...
pip install -r requirements\test.txt
goto end

:prod
echo Installing production dependencies...
pip install -r requirements\prod.txt
goto end

:end
echo Virtual environment setup complete!
echo To activate the virtual environment, run: venv\Scripts\activate
```

## Additional Configuration Files

### Python Version File (.python-version)

For pyenv users, create a `.python-version` file:

```
3.9.17
```

### Setup.py (for Development Mode Installation)

```python
from setuptools import find_packages, setup

setup(
    name="experimentation-platform",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.9",
    install_requires=[
        # Base dependencies are read from requirements files
    ],
)
```

## Usage Instructions

### Initial Setup

1. Make the setup script executable (Unix/Linux/macOS):

    ```bash
    chmod +x setup_venv.sh
    ```

2. Run the setup script:

    - Unix/Linux/macOS: `./setup_venv.sh`
    - Windows: `setup_venv.bat`

3. Activate the virtual environment:
    - Unix/Linux/macOS: `source venv/bin/activate`
    - Windows: `venv\Scripts\activate`

### Development Mode Installation

For development, you can install the package in editable mode:

```bash
pip install -e .
```

### Selecting Environment

You can specify which environment to set up:

-   Development (default):

    -   Unix/Linux/macOS: `./setup_venv.sh dev`
    -   Windows: `setup_venv.bat dev`

-   Testing:

    -   Unix/Linux/macOS: `./setup_venv.sh test`
    -   Windows: `setup_venv.bat test`

-   Production:
    -   Unix/Linux/macOS: `./setup_venv.sh prod`
    -   Windows: `setup_venv.bat prod`

## Benefits

This virtual environment configuration provides:

1. **Isolation**: Keeps project dependencies separate from system Python
2. **Reproducibility**: Explicitly defined dependencies with pinned versions
3. **Environment Separation**: Different configurations for development, testing, and production
4. **Easy Setup**: Scripts handle creation and configuration automatically
5. **Development Tools**: Pre-configured development tools like linters and formatters
