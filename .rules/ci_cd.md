# CI/CD Workflow Standards

## Purpose: Automated Quality Gates
**Why CI/CD?** Catch issues before users do.
**Think:** Every pipeline failure is a production bug prevented.
**Goal:** Fast feedback, high confidence, zero surprises.

## Essential Workflows

### 1. Testing (`test.yml`)
**Triggers:** `on: [push, pull_request]` to main
**Jobs (in order):**
- **Lint:** `ruff check` (fails fast)
- **Type Check:** `mypy --strict`
- **Test:** Real tests only, matrix for Python versions
- **Coverage:** Report to stdout, fail under 95%

### 2. Release (`release.yml`)
**Triggers:** Tag creation or manual
**Jobs:** Build -> Create release -> Publish to PyPI

## Python CI Example
```yaml
name: CI
on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with: { python-version: '3.12', cache: 'pip' }
    - run: pip install ruff && ruff check .

  type-check:
    needs: lint
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with: { python-version: '3.12', cache: 'pip' }
    - run: pip install -e ".[dev]" && mypy src/

  test:
    needs: type-check
    runs-on: ubuntu-latest
    strategy:
      matrix: { python-version: ['3.10', '3.11', '3.12', '3.13'] }
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with: { python-version: '${{ matrix.python-version }}', cache: 'pip' }
    - run: pip install -e ".[dev]"
    - run: pytest --cov=src/asc_cli --cov-fail-under=95
```

## Key Practices
- **Pin versions:** `actions/checkout@v4` (reproducibility)
- **Cache deps:** Speed matters for developer happiness
- **Fail fast:** Lint -> Type -> Test -> Deploy
- **Matrix testing:** Test all supported Python versions
- **Secrets:** Never commit credentials, use GitHub secrets
- **Conditional:** Deploy only from protected branches

## Local Testing
```bash
# Run same checks as CI
ruff check . && ruff format --check .
mypy src/
pytest --cov

# Or use act for local GitHub Actions
act -j lint
```

## Pipeline Philosophy
**Fast feedback:** Developers should know in <5 min
**Clear failures:** Error messages should guide fixes
**No surprises:** If it passes CI, it works in production

---
*Automated quality gates prevent production incidents.*
