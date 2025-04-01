# Setting Up GitHub Actions for Python Backend Testing

This guide explains how to set up and configure a comprehensive GitHub Actions workflow for testing your Python backend code.

## What This Workflow Does

The workflow we've created:

1. **Automates testing** on pull requests and pushes to main
2. **Tests against multiple Python versions** (3.9 and 3.10)
3. **Sets up a PostgreSQL database** for integration tests
4. **Collects and reports code coverage**
5. **Publishes detailed test reports** in GitHub's UI
6. **Optimizes testing performance** with caching and parallel execution

## File Structure

Place these files in your repository:

```
.github/
  workflows/
    backend-tests.yml  # Main workflow file
pytest.ini            # Pytest configuration
.coveragerc           # Coverage configuration
```

## Setup Steps

### 1. Create the Workflow File

Create the directory `.github/workflows/` in your repository and save the `backend-tests.yml` file there.

This workflow is triggered on:
- Pushes to the `main` branch
- Pull requests targeting the `main` branch

But only when relevant files change (Python files, requirements, or the workflow itself).

### 2. Configure Pytest

Add the `pytest.ini` file to your repository root. This configures:
- Where to find tests
- Test markers for categorizing tests
- Environment variables for testing
- Coverage settings

### 3. Configure Coverage

Add the `.coveragerc` file to your repository root to configure:
- What files to include/exclude from coverage
- Which lines to exclude from coverage calculation
- How to format coverage reports

## How It Works

When a PR is created or code is pushed to main:

1. **GitHub starts the workflow** with separate jobs for each Python version
2. **Dependencies are installed** (cached for faster runs)
3. **A PostgreSQL database** is started for integration tests
4. **Tests run with pytest** in parallel with coverage measurement
5. **Test results are uploaded** as artifacts
6. **Test report is generated** showing pass/fail status
7. **Coverage data is uploaded** to Codecov (if configured)

## Key Features

### Matrix Testing

The workflow tests against multiple Python versions simultaneously:

```yaml
strategy:
  matrix:
    python-version: ["3.9", "3.10"]
```

Add more versions as needed.

### Dependency Caching

The workflow caches pip dependencies to speed up subsequent runs:

```yaml
- uses: actions/setup-python@v4
  with:
    python-version: ${{ matrix.python-version }}
    cache: 'pip'  # Built-in pip caching
    
- uses: actions/cache@v3  # Additional caching layer
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}-${{ matrix.python-version }}
```

### Database Services

The workflow spins up a PostgreSQL database for integration tests:

```yaml
services:
  postgres:
    image: postgres:14
    env:
      POSTGRES_PASSWORD: postgres
      POSTGRES_USER: postgres
      POSTGRES_DB: test_db
    ports:
      - 5432:5432
```

Access it in tests via `postgresql://postgres:postgres@localhost:5432/test_db`.

### Parallel Test Execution

Tests run in parallel with pytest-xdist:

```bash
python -m pytest \
  --cov=. \
  --cov-report=xml \
  --cov-report=term \
  -v \
  --junitxml=pytest.xml \
  -n auto
```

The `-n auto` flag distributes tests across available CPU cores.

### Test Reporting

The workflow publishes detailed test reports using action-junit-report:

```yaml
- uses: mikepenz/action-junit-report@v3
  with:
    report_paths: 'pytest.xml'
    check_name: Test Results - Python ${{ matrix.python-version }}
```

This shows test results directly in the GitHub UI.

## Customizing the Workflow

### Adding Testing Dependencies

If you need additional test libraries, add them to the installation step:

```yaml
pip install pytest pytest-cov pytest-xdist pytest-env pytest-mock pytest-django
```

### Adding More Services

For Redis or other services, add them to the services section:

```yaml
services:
  postgres:
    # existing config
  redis:
    image: redis:7
    ports:
      - 6379:6379
```

### Running Specific Test Subsets

To run different test groups, modify the pytest command:

```yaml
# Run only unit tests
python -m pytest -m unit --cov=.

# Run only specific modules
python -m pytest path/to/specific/tests
```

### Configuration for Different Environments

For different environments (dev/staging/prod), use environment-specific variables:

```yaml
env:
  ENVIRONMENT: ${{ github.ref == 'refs/heads/main' && 'prod' || 'dev' }}
```

## Test Writing Best Practices

1. **Use markers** to categorize tests:
   ```python
   @pytest.mark.unit
   def test_my_function():
       # Test implementation
   ```

2. **Use fixtures** for common setup:
   ```python
   @pytest.fixture
   def db_connection():
       # Setup database connection
       yield connection
       # Cleanup
   ```

3. **Mock external services**:
   ```python
   @pytest.fixture
   def mock_aws():
       with patch('boto3.client') as mock:
           yield mock
   ```

4. **Parametrize tests** for multiple inputs:
   ```python
   @pytest.mark.parametrize("input,expected", [
       (1, 1),
       (2, 4),
       (3, 9)
   ])
   def test_square(input, expected):
       assert square(input) == expected
   ```

## Troubleshooting

- **Tests pass locally but fail in CI**: Check environment differences or add `-v` to see more details
- **Missing dependencies**: Ensure all requirements are in requirements.txt
- **Database connection errors**: Verify service configuration and connection string
- **Slow tests**: Use `-n auto` for parallel execution and consider skipping slow tests with markers

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
