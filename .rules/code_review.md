# Code Review Standards

## PR Review Toolkit
When the `pr-review-toolkit` plugin is available, use it after creating PRs to catch issues before merge.

### Available Agents
- `code-reviewer` - Review for style, best practices, project guidelines
- `silent-failure-hunter` - Find inadequate error handling, silent failures
- `code-simplifier` - Simplify code while preserving functionality
- `comment-analyzer` - Check comment accuracy and maintainability
- `pr-test-analyzer` - Review test coverage quality
- `type-design-analyzer` - Analyze type design and invariants

### Workflow
1. Create PR with `gh pr create`
2. Run code review agent on the changes
3. Address critical findings before requesting human review
4. Document any intentionally skipped suggestions

## Manual Code Review Checklist

### Before Committing
- [ ] Code runs without errors
- [ ] Tests pass
- [ ] No debug code left (print statements, TODO hacks)
- [ ] No sensitive data in code or logs

### Logic & Safety
- [ ] Error cases handled appropriately
- [ ] No silent failures (empty except blocks)
- [ ] Resource cleanup (files, connections)
- [ ] API rate limits considered

### Code Quality
- [ ] Functions do one thing
- [ ] Clear naming (no abbreviations)
- [ ] No magic numbers (use constants)
- [ ] Comments explain "why", not "what"

### Python Specific
- [ ] Type hints on public functions
- [ ] Proper exception handling
- [ ] Context managers for resources
- [ ] Async where appropriate

### CLI Specific
- [ ] Help text is clear and useful
- [ ] Error messages are actionable
- [ ] Exit codes are appropriate
- [ ] Output format is consistent

## Review Comments
When leaving review comments:
- Be specific about the issue
- Suggest a fix when possible
- Distinguish blocking vs. non-blocking issues
- Reference documentation or examples

---
*Review early, review often, catch issues before they ship.*
