# Custom Claude Code Slash Commands

This directory contains custom slash commands for the experimentation platform project. These commands provide shortcuts for common development tasks and ensure consistent execution patterns.

## Available Commands

### `/test-backend [arguments]`
Run backend tests with proper environment setup.

**Examples:**
```bash
/test-backend                          # Run all backend tests
/test-backend backend/tests/unit/      # Run all unit tests
/test-backend backend/tests/unit/services/test_audit_service.py  # Run specific file
/test-backend -k "test_feature"        # Run tests matching pattern
/test-backend -m "unit"                # Run tests with marker
```

**What it does:**
- Activates virtual environment
- Sets APP_ENV=test and TESTING=true
- Runs pytest with verbose output and short tracebacks
- Reports clear pass/fail results

---

### `/migration "description"`
Create and apply a database migration safely.

**Examples:**
```bash
/migration "add user preferences table"
/migration "add index on experiment_assignments user_id"
```

**What it does:**
- Sets PostgreSQL environment variables
- Generates Alembic migration with autogenerate
- Reviews generated migration for accuracy
- Applies migration to database
- Verifies successful application
- Shows migration history

**Safety features:**
- Checks down_revision chain integrity
- Reviews for unintended changes
- Verifies schema is set correctly

---

### `/fix-imports [check|fix]`
Standardize and verify metrics model imports.

**Examples:**
```bash
/fix-imports              # Check for issues
/fix-imports check        # Explicit check only
/fix-imports fix          # Apply fixes and verify
```

**What it does:**
- Runs standardize_metrics_imports.py script
- Identifies inconsistent import paths
- Optionally applies fixes
- Runs verification tests
- Reports standardization results

**Why this matters:**
Prevents SQLAlchemy "Class is not mapped" errors caused by inconsistent import paths.

---

### `/start-api [docker]`
Start the FastAPI backend development server.

**Examples:**
```bash
/start-api              # Start local uvicorn server
/start-api docker       # Start with Docker Compose
```

**What it does:**
- Local mode: Activates venv, sets APP_ENV=dev, runs uvicorn with hot-reload
- Docker mode: Starts docker-compose services, shows logs
- Reports server URLs (API, docs, health endpoints)
- Monitors for startup errors

**URLs reported:**
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

---

### `/quality [check|fix|tool-name]`
Run code quality checks on the backend.

**Examples:**
```bash
/quality                # Check all quality metrics (dry-run)
/quality check          # Same as above
/quality fix            # Apply formatting and sorting fixes
/quality black          # Run only black formatter
/quality mypy           # Run only type checking
```

**What it does:**
- Runs black (formatting), isort (imports), mypy (types), flake8 (linting)
- Check mode: Reports issues without changes
- Fix mode: Applies black and isort fixes automatically
- Tool-specific: Runs individual tools

**Tools used:**
- **black**: PEP 8 code formatting
- **isort**: Import statement sorting
- **mypy**: Static type checking
- **flake8**: Linting and style checking

---

### `/commit [message]`
Create a well-formatted git commit following project standards.

**Examples:**
```bash
/commit                           # Analyze changes and create commit
/commit "Add safety monitoring"   # Create commit with this summary
```

**What it does:**
- Reviews git status and diff
- Analyzes recent commit style
- Stages appropriate files
- Generates detailed commit message following project format:
  - Concise summary (≤50 chars)
  - Detailed explanation (what, why, technical details)
  - Claude Code attribution footer
- Creates commit with proper formatting
- Verifies commit creation

**Commit message format:**
```
Brief summary (50 chars or less)

Detailed explanation:
- What was changed
- Why it was changed
- Technical details

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## How to Use Slash Commands

1. **Type the command**: Start typing `/` in Claude Code to see available commands
2. **Use tab completion**: Press tab to autocomplete command names
3. **Pass arguments**: Add arguments after the command (some are optional)
4. **Check results**: Commands provide detailed feedback on execution

## Creating New Commands

To add new custom commands:

1. Create a new `.md` file in `.claude/commands/`
2. Use `$ARGUMENTS` keyword to accept parameters
3. Write clear step-by-step instructions
4. Include examples and safety notes
5. Update this README with documentation

**Command file template:**
```markdown
Brief description of what this command does.

Longer explanation with context.

Arguments: $ARGUMENTS (optional/required - description)

Steps to execute:
1. First step
2. Second step
3. etc.

Example usage:
- /commandname → default behavior
- /commandname arg → behavior with argument
```

## Best Practices

- **Use specific commands** instead of manually typing repetitive tasks
- **Check before fix** when using quality or import commands
- **Review migrations** before applying (safety critical)
- **Test before commit** to ensure changes work
- **Chain commands** for workflows (e.g., quality → test-backend → commit)

## Workflow Examples

### Feature Development Workflow
```bash
1. /start-api                    # Start development server
2. [Make changes to code]
3. /quality fix                  # Format and lint code
4. /test-backend -k "new_feature"  # Test new feature
5. /commit "Add new feature"     # Create commit
```

### Database Migration Workflow
```bash
1. [Update SQLAlchemy models]
2. /migration "add new table"    # Create and apply migration
3. /test-backend backend/tests/integration/  # Test database changes
4. /commit "Add database migration"
```

### Code Quality Workflow
```bash
1. /quality check                # Check for issues
2. /fix-imports fix              # Fix import inconsistencies
3. /quality fix                  # Apply formatting fixes
4. /test-backend                 # Ensure tests still pass
5. /commit "Standardize code quality"
```

## Troubleshooting

**Command not found:**
- Ensure you're in the project root directory
- Check that `.claude/commands/` directory exists
- Verify the command file has `.md` extension

**Command fails:**
- Read error messages carefully
- Check that prerequisites are met (e.g., virtualenv exists, Docker is running)
- Verify environment variables are set correctly

**Need to modify a command:**
- Edit the `.md` file directly
- Changes take effect immediately
- Test the modified command

## Contributing

These commands are checked into git and shared with the team. When adding new commands:

1. Make them general enough for all developers
2. Include clear documentation and examples
3. Test thoroughly before committing
4. Update this README

For personal commands, add them to `~/.claude/commands/` instead of `.claude/commands/`.
