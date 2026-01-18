# Phase 4 Quick Start Guide

Get started with headless mode automation and multi-Claude workflows in 5 minutes.

## 🚀 Quick Links

- **Full Plan**: [PHASE_4_PLAN.md](PHASE_4_PLAN.md)
- **Slash Commands**: [commands/README.md](commands/README.md)
- **Main Guide**: [../CLAUDE.md](../CLAUDE.md)

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Immediate Usage](#immediate-usage)
3. [Common Workflows](#common-workflows)
4. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Ensure you have:
- ✅ Claude Code CLI installed
- ✅ Git repository initialized
- ✅ Scripts are executable (`chmod +x scripts/*.sh`)

---

## Immediate Usage

### 1. Run Claude Linter

Check your code for subjective quality issues:

```bash
# Lint staged files (pre-commit use)
./scripts/claude-lint.sh

# Lint specific files
./scripts/claude-lint.sh backend/app/api/v1/endpoints/experiments.py

# Lint all Python files in a directory
./scripts/claude-lint.sh backend/app/services/*.py
```

**What it checks**:
- Typos in comments and docstrings
- Misleading variable/function names
- Stale or outdated comments
- Unclear error messages
- Missing edge case handling

### 2. Create Git Worktree for Parallel Development

Work on multiple features simultaneously:

```bash
# Create worktree for new feature
./scripts/worktree-manager.sh create authentication-refactor

# List all active worktrees
./scripts/worktree-manager.sh list

# Open worktree in new terminal tab
./scripts/worktree-manager.sh open authentication-refactor

# When done, cleanup
./scripts/worktree-manager.sh cleanup authentication-refactor
```

### 3. Multi-Claude Code Review

Use multiple Claude instances for better code quality:

**Terminal 1 - Writer Claude**:
```bash
claude
# Prompt: "Implement user role-based permissions for experiments"
```

**Terminal 2 - Reviewer Claude** (after writer is done):
```bash
/clear
claude
# Prompt: "Review the recent permission implementation.
# Check for security issues, edge cases, and code quality.
# Write feedback to .claude/review-feedback.md"
```

**Terminal 3 - Implementer Claude** (after review):
```bash
/clear
claude
# Prompt: "Read .claude/review-feedback.md and apply suggested improvements.
# Ensure all tests pass after changes."
```

---

## Common Workflows

### Workflow A: Feature Development with Review

1. **Create dedicated worktree**:
   ```bash
   ./scripts/worktree-manager.sh create my-feature
   cd ../experimentation-platform-worktrees/my-feature
   ```

2. **Develop with Claude**:
   ```bash
   claude
   # Implement your feature
   ```

3. **Self-review with fresh Claude**:
   ```bash
   /clear
   claude
   # Review your own changes with fresh context
   ```

4. **Run quality checks**:
   ```bash
   ./scripts/claude-lint.sh
   /quality fix
   /test-backend
   ```

5. **Create PR**:
   ```bash
   /commit "Implement my feature"
   # Then create PR with: gh pr create
   ```

### Workflow B: Parallel Feature Development

Open 3 terminal tabs:

**Tab 1 - Authentication**:
```bash
./scripts/worktree-manager.sh create auth-improvement
cd ../experimentation-platform-worktrees/auth-improvement
claude
```

**Tab 2 - Metrics Dashboard**:
```bash
./scripts/worktree-manager.sh create metrics-dashboard
cd ../experimentation-platform-worktrees/metrics-dashboard
claude
```

**Tab 3 - API Rate Limiting**:
```bash
./scripts/worktree-manager.sh create rate-limiting
cd ../experimentation-platform-worktrees/rate-limiting
claude
```

All three features develop independently!

### Workflow C: Code Review Before Merge

Before merging a big PR:

```bash
# Terminal 1: Run comprehensive review
claude -p "Review all changes in this PR for:
1. Security vulnerabilities
2. Performance implications
3. Breaking changes
4. Missing tests
5. Documentation needs

Write detailed review to .claude/pr-review.md" \
--allowedTools Read Grep Bash

# Terminal 2: Check what reviewer found
cat .claude/pr-review.md

# Terminal 3: Apply fixes
claude -p "Read .claude/pr-review.md and fix all issues found.
Prioritize security and breaking changes." \
--allowedTools Read Edit Bash
```

### Workflow D: Batch Test Migration

Migrate many test files to new patterns:

```bash
# Create list of files to migrate
find backend/tests -name "test_*.py" > tests-to-migrate.txt

# Process in batches (headless mode)
cat tests-to-migrate.txt | while read file; do
  echo "Migrating: $file"

  claude -p "Migrate $file to use new fixture patterns.
  Update imports and ensure tests pass.
  Return 'OK' if successful, 'FAIL: reason' if not." \
  --allowedTools Edit Bash

  # Check result and log
done
```

---

## Advanced Patterns

### Headless Mode Examples

#### Example 1: Generate Issue Labels

```bash
gh issue view 42 --json title,body | \
  claude -p "Analyze this issue and suggest labels.
  Return JSON array: [\"bug\", \"backend\"]" \
  --output-format stream-json
```

#### Example 2: Analyze Experiment Results

```bash
python scripts/export-results.py | \
  claude -p "Analyze experiment results and generate insights.
  Return structured JSON report." \
  --output-format stream-json > analysis.json

# Use results in next step
python scripts/update-dashboard.py analysis.json
```

#### Example 3: Pre-commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash
./scripts/claude-lint.sh || exit 0  # Non-blocking

# Other checks
black --check backend/ || exit 1
pytest backend/tests/unit -x || exit 1
```

---

## Script Reference

### claude-lint.sh

```bash
# Lint staged files
./scripts/claude-lint.sh

# Lint specific files
./scripts/claude-lint.sh file1.py file2.py

# Results saved to .claude/lint-results.json for CI
```

### worktree-manager.sh

```bash
# Create new worktree
./scripts/worktree-manager.sh create <task-name>

# List all worktrees
./scripts/worktree-manager.sh list

# Show detailed status
./scripts/worktree-manager.sh status

# Open in new terminal
./scripts/worktree-manager.sh open <task-name>

# Cleanup when done
./scripts/worktree-manager.sh cleanup <task-name>

# Sync all with remote
./scripts/worktree-manager.sh sync
```

---

## Best Practices

### ✅ Do's

- **Use `/clear`** between different tasks to get fresh context
- **Run linter** before committing code
- **Create worktrees** for independent features
- **Use headless mode** for automation and CI/CD
- **Document decisions** in scratchpads for other Claudes to read
- **Test after changes** to ensure Claude's edits work

### ❌ Don'ts

- **Don't mix contexts** - use /clear or separate Claudes for distinct tasks
- **Don't skip testing** - always verify Claude's code works
- **Don't ignore linter** - subjective issues matter for maintainability
- **Don't forget cleanup** - remove worktrees when done
- **Don't use headless for interactive** - use regular mode for exploration

---

## Troubleshooting

### Issue: Claude linter returns empty results

**Solution**: Ensure:
1. Files actually exist
2. Claude Code CLI is in PATH
3. Try with `--verbose` flag to see errors

```bash
claude -p "..." --verbose
```

### Issue: Worktree creation fails

**Solution**: Check if:
1. Branch already exists
2. Worktree path already used
3. Run `git worktree prune` to cleanup stale references

```bash
git worktree prune
./scripts/worktree-manager.sh list
```

### Issue: Headless mode hangs

**Solution**:
1. Add timeout: `timeout 300 claude -p "..."`
2. Check if waiting for approval
3. Ensure all tools are in allowlist

### Issue: Multiple Claudes conflict

**Solution**:
- Use separate worktrees for independent work
- Use scratchpads for communication between Claudes
- Coordinate manually for dependent changes

---

## Tips & Tricks

### iTerm2 Notifications

Get notified when Claude needs attention:

```bash
# In iTerm2: Preferences > Profiles > Terminal > Notifications
# Enable: "Notify on activity"
```

### VS Code Integration

Open each worktree in separate VS Code window:

```bash
code ../experimentation-platform-worktrees/feature-a
code ../experimentation-platform-worktrees/feature-b
```

### Scratchpad Communication

Have Claudes communicate via files:

```bash
# Claude 1 writes plan
claude -p "Create implementation plan.
Write to .claude/scratchpads/plan.md"

# Claude 2 reads and implements
claude -p "Read .claude/scratchpads/plan.md and implement.
Write progress to .claude/scratchpads/progress.md"

# Claude 3 reviews both
claude -p "Read plan and progress.
Review implementation quality."
```

### Batch Processing Template

```bash
#!/bin/bash
# Process items in parallel

cat items.txt | xargs -P 4 -I {} bash -c '
  claude -p "Process: {}" --output-format stream-json
'
```

---

## Next Steps

1. ✅ **Try the linter**: `./scripts/claude-lint.sh`
2. ✅ **Create a worktree**: `./scripts/worktree-manager.sh create test-feature`
3. ✅ **Run multi-Claude review** on a recent PR
4. ✅ **Set up pre-commit hook** with Claude linter
5. ✅ **Read full plan**: [PHASE_4_PLAN.md](PHASE_4_PLAN.md)

---

## Questions?

- Check [PHASE_4_PLAN.md](PHASE_4_PLAN.md) for detailed explanations
- Review [CLAUDE.md](../CLAUDE.md) for project-specific guidance
- See [commands/README.md](commands/README.md) for slash commands

---

**Happy automating! 🚀**
