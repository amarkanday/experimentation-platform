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

# Upgrade pip and setuptools
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip setuptools wheel
pip install pre-commit

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
