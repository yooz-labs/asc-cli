# Git & Version Control Standards

## Commit Messages
- **Format:** `<type>: <description>`
- **Length:** <50 characters
- **No emojis** in commits or PR titles
- **No Co-Authored-By headers**
- **Types:**
  - `feat:` New feature
  - `fix:` Bug fix
  - `docs:` Documentation only
  - `refactor:` Code restructuring
  - `test:` Adding tests (real tests only)
  - `chore:` Maintenance tasks

## Branch Strategy
- **Feature branches:** `feature/short-description`
- **Bugfix branches:** `fix/issue-description`
- **No spaces** in branch names, use hyphens
- **Delete after merge**

## Commit Practice
- **Atomic commits** - One logical change per commit
- **Test before commit** - Ensure code works
- **No broken commits** - Each commit should work independently

## Pull Request Process
1. Create issue first (for significant changes)
2. Branch from main
3. Make atomic commits
4. Push branch
5. Create PR with:
   - Clear title (no issue numbers in title)
   - Description with "Fixes #123"
   - Test results
   - No emojis

## Git Commands
```bash
# Start feature
git checkout -b feature/new-thing

# Atomic commits
git add -p  # Stage selectively
git commit -m "feat: add subscription pricing endpoint"

# Update branch
git fetch origin
git rebase origin/main

# Push and create PR
git push -u origin feature/new-thing
gh pr create
```

## .gitignore Essentials
```
# Development context (version controlled in this project)
# .context/ is tracked for this project

# Python
__pycache__/
*.py[cod]
.venv/

# Credentials
*.p8
.env

# IDE
.idea/
.vscode/
```

---
*Atomic commits, clear messages, clean history.*
