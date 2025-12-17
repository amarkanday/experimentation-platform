# VSCode Configuration for Experimentation Platform

This document provides the recommended VSCode settings for the experimentation platform project. These settings ensure a consistent development experience for all team members and enforce the project's coding standards automatically.

## Setup Instruction

1. Create a `.vscode` folder in the project root directory:

```bash
mkdir -p .vscode
```

2. Create a `settings.json` file in the `.vscode` folder:

```bash
touch .vscode/settings.json
```

3. Copy and paste the following configuration into the `settings.json` file:

```json
{
    "editor.rulers": [88],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": "explicit"
    },
    "editor.renderWhitespace": "boundary",
    "editor.renderControlCharacters": true,
    "editor.tabSize": 4,
    "editor.indentSize": 4,
    "editor.insertSpaces": true,
    "editor.detectIndentation": false,

    "files.exclude": {
        "**/__pycache__": true,
        "**/.pytest_cache": true,
        "**/*.pyc": true,
        ".mypy_cache": true,
        ".coverage": true,
        "htmlcov": true,
        ".venv": false
    },
    "files.trimTrailingWhitespace": true,
    "files.insertFinalNewline": true,
    "files.trimFinalNewlines": true,

    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.linting.pylintEnabled": false,
    "python.linting.banditEnabled": true,
    "python.linting.flake8Args": ["--max-line-length=88"],

    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length", "88"],

    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.testing.nosetestsEnabled": false,
    "python.testing.pytestArgs": ["tests", "--no-cov"],

    "python.analysis.typeCheckingMode": "basic",
    "python.analysis.extraPaths": ["${workspaceFolder}"],

    "[python]": {
        "editor.defaultFormatter": "ms-python.black-formatter",
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.organizeImports": "explicit"
        }
    },

    "[javascript]": {
        "editor.defaultFormatter": "esbenp.prettier-vscode",
        "editor.formatOnSave": true,
        "editor.tabSize": 2
    },

    "[typescript]": {
        "editor.defaultFormatter": "esbenp.prettier-vscode",
        "editor.formatOnSave": true,
        "editor.tabSize": 2
    },

    "[typescriptreact]": {
        "editor.defaultFormatter": "esbenp.prettier-vscode",
        "editor.formatOnSave": true,
        "editor.tabSize": 2
    },

    "[json]": {
        "editor.defaultFormatter": "esbenp.prettier-vscode",
        "editor.formatOnSave": true,
        "editor.tabSize": 2
    },

    "[yaml]": {
        "editor.defaultFormatter": "esbenp.prettier-vscode",
        "editor.formatOnSave": true,
        "editor.tabSize": 2
    },

    "yaml.schemas": {
        "https://json.schemastore.org/github-workflow.json": ".github/workflows/*.yml"
    },

    "prettier.singleQuote": true,
    "prettier.trailingComma": "es5",

    "git.enableSmartCommit": true,
    "git.confirmSync": false,

    "explorer.compactFolders": false,

    "terminal.integrated.env.linux": {
        "PYTHONPATH": "${workspaceFolder}"
    },
    "terminal.integrated.env.osx": {
        "PYTHONPATH": "${workspaceFolder}"
    },
    "terminal.integrated.env.windows": {
        "PYTHONPATH": "${workspaceFolder}"
    },

    "autoDocstring.docstringFormat": "google",
    "autoDocstring.startOnNewLine": true
}
```

## Required Extensions

The following VSCode extensions are recommended for this project:

1. **Python Tools**:

    - Microsoft Python (`ms-python.python`)
    - Black Formatter (`ms-python.black-formatter`)
    - Flake8 (`ms-python.flake8`)
    - Mypy (`matangover.mypy`)
    - autoDocstring (`njpwerner.autodocstring`)

2. **JavaScript/TypeScript/Frontend Tools**:

    - ESLint (`dbaeumer.vscode-eslint`)
    - Prettier (`esbenp.prettier-vscode`)
    - TypeScript Vue Plugin (`Vue.vscode-typescript-vue-plugin`)

3. **DevOps & Others**:
    - Docker (`ms-azuretools.vscode-docker`)
    - YAML (`redhat.vscode-yaml`)
    - AWS Toolkit (`amazonwebservices.aws-toolkit-vscode`)
    - GitLens (`eamodio.gitlens`)
    - EditorConfig (`editorconfig.editorconfig`)

## Settings Explained

### Editor Configuration

-   **Line Length**: 88 characters (matching Black's default)
-   **Format on Save**: Automatically formats code when saving files
-   **Import Organizing**: Sorts imports on save
-   **Indentation**: 4 spaces for Python, 2 spaces for JS/TS/JSON/YAML

### Python Development

-   **Linting**: Flake8, Mypy, and Bandit enabled
-   **Formatting**: Black configured with 88 character line length
-   **Testing**: Pytest integration
-   **Type Checking**: Basic type checking enabled

### JavaScript/TypeScript Development

-   **Formatting**: Prettier configured with single quotes
-   **Style**: 2-space indentation, ES5 trailing commas

### Other Settings

-   **Git Integration**: Smart commit and automatic sync
-   **File Management**: Excludes cache files and bytecode
-   **Environment**: PYTHONPATH configured for proper imports
-   **Documentation**: Google-style docstring format

## Customization

Team members can override these settings in their user settings if needed, but the project settings should be respected for consistency. Any proposed changes to these settings should be discussed with the team before implementation.
