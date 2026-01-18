#!/bin/bash
# Claude Code Linter - Subjective code quality checks
# Usage: ./scripts/claude-lint.sh [files...]
# If no files specified, checks staged files

set -e

FILES_TO_CHECK=$@

if [ -z "$FILES_TO_CHECK" ]; then
  FILES_TO_CHECK=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(py|js|ts|tsx)$')
fi

if [ -z "$FILES_TO_CHECK" ]; then
  echo "✅ No files to lint"
  exit 0
fi

echo "🔍 Running Claude Code Linter on:"
echo "$FILES_TO_CHECK" | tr ' ' '\n' | sed 's/^/  - /'
echo ""

# Create temp file for results
TEMP_RESULTS=$(mktemp)

claude -p "Review these files for subjective code quality issues:

Files to review:
$(echo "$FILES_TO_CHECK" | tr ' ' '\n')

Look for:
1. **Typos in comments, docstrings, and error messages**
2. **Misleading variable or function names**
3. **Stale or outdated comments**
4. **Unclear error messages**
5. **Missing edge case handling**
6. **Confusing code organization**
7. **Inconsistent naming conventions**
8. **Missing documentation for complex logic**

For each issue found, provide:
- File path and line number
- Issue category
- Current code snippet (keep it brief)
- Suggested improvement
- Brief reasoning

Return JSON array format:
[
  {
    \"file\": \"path/to/file.py\",
    \"line\": 42,
    \"category\": \"misleading_name\",
    \"current\": \"def process(x):\",
    \"suggested\": \"def process_user_assignment(user_context):\",
    \"reason\": \"Function name doesn't indicate what it processes\"
  }
]

If no issues found, return empty array: []
" --output-format stream-json > "$TEMP_RESULTS" 2>/dev/null || true

# Check if results file exists and has content
if [ ! -s "$TEMP_RESULTS" ]; then
  echo "✅ No subjective code quality issues found"
  rm "$TEMP_RESULTS"
  exit 0
fi

# Parse results
ISSUES_COUNT=$(cat "$TEMP_RESULTS" | jq '. | length' 2>/dev/null || echo "0")

if [ "$ISSUES_COUNT" -gt 0 ]; then
  echo "⚠️  Found $ISSUES_COUNT subjective code quality issue(s):"
  echo ""

  cat "$TEMP_RESULTS" | jq -r '.[] | "
📍 \(.file):\(.line)
   Category: \(.category)
   Current:  \(.current)
   Suggested: \(.suggested)
   Reason:   \(.reason)
"'

  echo ""
  echo "💡 Consider addressing these suggestions before committing."
  echo "   These are recommendations, not blocking errors."

  # Save results for CI
  cp "$TEMP_RESULTS" .claude/lint-results.json 2>/dev/null || true
else
  echo "✅ No subjective code quality issues found"
fi

rm "$TEMP_RESULTS"
exit 0
