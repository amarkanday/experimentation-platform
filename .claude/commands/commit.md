Create a well-formatted git commit following project standards.

Review changes, stage files, and create a detailed commit with proper formatting.

Arguments: $ARGUMENTS (optional - commit message summary, will be expanded)

Steps to execute:
1. Run git status to show current state
2. Run git diff to review staged and unstaged changes
3. Run git log --oneline -5 to see recent commit style
4. If files need staging:
   - Identify relevant changed files
   - Stage with: git add <files>
   - Confirm staged changes with git status

5. Analyze changes and draft commit message:
   - Determine change type: feature, fix, refactor, test, docs, etc.
   - Write concise summary (50 chars or less)
   - Add detailed explanation covering:
     * What was changed
     * Why it was changed
     * Technical details and decisions
   - Include footer with Claude Code attribution

6. Create commit using HEREDOC format:
   ```bash
   git commit -m "$(cat <<'EOF'
   Brief summary (50 chars or less)

   Detailed explanation:
   - What was changed
   - Why it was changed
   - Technical details

   🤖 Generated with [Claude Code](https://claude.com/claude-code)

   Co-Authored-By: Claude <noreply@anthropic.com>
   EOF
   )"
   ```

7. Verify commit with: git log -1 --stat

Important notes:
- Never commit files with secrets (.env, credentials.json, etc.)
- Focus commit message on "why" rather than "what"
- Keep summary line under 50 characters
- Add blank line between summary and body
- Use bullet points for clarity

Example usage:
- /commit → analyze changes and create commit
- /commit "Add safety monitoring" → create commit with this summary
