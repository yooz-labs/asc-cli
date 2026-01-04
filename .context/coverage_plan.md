# Coverage Improvement Plan: 57% → 90%+

Current: 60% | Target: 90%+ | Last Update: 2026-01-04

## Coverage Analysis by Module

### ✅ Already at 90%+
- `cli.py`: 100%
- `__init__.py` files: 100%
- `api/auth.py`: 100% ✨ (Phase 1 complete)
- `apps.py`: 94%
- `schema.py`: 92%

### 🔴 Needs Improvement

| Module | Current | Missing Lines | Strategy |
|--------|---------|---------------|----------|
| `api/client.py` | 60% | Error paths, pagination | Add simulation edge cases |
| `commands/auth.py` | 18% | 27-138 | Mock credential operations |
| `commands/bulk.py` | 19% | 40-433 | Test bulk workflows |
| `commands/subscriptions.py` | 67% | Edge cases | Add error scenario tests |
| `commands/testflight.py` | 77% | 26-85 | Add TestFlight to simulator |

---

## Implementation Strategy

### ✅ Phase 1: Auth Module (69% → 100%) - COMPLETE
**Status:** Complete - 26 tests added

**Achieved:**
- Tested `from_file()` with temp files
- Tested `from_env()` with patched env vars
- Tested `save()` credential writing
- Tested token generation with real EC key

**Files created:**
- `tests/test_auth_coverage.py`

### Phase 2: Client Module (60% → 90%)
**Missing:** Error handling paths, pagination edge cases

**Approach:** Extend simulation engine
- Add error response scenarios to simulator
- Test pagination with large datasets
- Test network errors
- Test malformed responses

**Files to modify:**
- `tests/simulation/engine.py` - Add error injection
- `tests/test_client_errors.py` - New error tests

### Phase 3: Auth Commands (18% → 90%)
**Missing:** login, logout, status, test commands

**Approach:** Mock file operations + simulation
- Mock credential file operations
- Use existing AuthManager tests
- Test all CLI flows

**Files to create:**
- `tests/test_auth_commands.py`

### Phase 4: Bulk Commands (19% → 90%)
**Missing:** Apply logic, YAML processing, price calculations

**Approach:** Use simulation engine
- Test bulk init (already done)
- Test bulk validate with various YAML configs
- Test bulk apply with dry-run
- Test error scenarios (invalid YAML, missing fields)

**Files to create:**
- `tests/test_bulk_coverage.py`

### Phase 5: Subscriptions Commands (67% → 90%)
**Missing:** Error handling, edge cases

**Approach:** Add error scenarios to simulation
- Test error paths (subscription not found, etc.)
- Test edge cases (no localizations, no pricing)
- Test all command variations

**Files to modify:**
- `tests/test_cli_simulation.py` - Add edge cases

### Phase 6: TestFlight Commands (77% → 90%)
**Missing:** TestFlight endpoints not in simulator

**Approach:** Add TestFlight to simulation engine
- Add TestFlight route handlers
- Add build/tester fixtures
- Test all TestFlight commands

**Files to create:**
- `tests/simulation/routes/testflight.py`
- `tests/test_testflight_simulation.py`

---

## Detailed Task Breakdown

### Task 1: Auth Module Tests (Priority: High)
```python
# tests/test_auth_coverage.py

def test_credentials_from_file_valid(tmp_path):
    # Create temp credential file
    # Test loading

def test_credentials_from_file_missing():
    # Test with non-existent file

def test_credentials_from_env_valid():
    # Mock env vars
    # Test loading

def test_credentials_save(tmp_path):
    # Test saving credentials

def test_token_generation():
    # Test JWT token creation
```

### Task 2: Client Error Tests (Priority: High)
```python
# tests/test_client_errors.py

@pytest.mark.simulation
def test_client_handles_404(mock_asc_api):
    # Simulate 404 response

@pytest.mark.simulation
def test_client_handles_malformed_json(mock_asc_api):
    # Simulate invalid JSON

@pytest.mark.simulation
def test_pagination_large_dataset(mock_asc_api):
    # Test pagination with 1000+ items
```

### Task 3: Auth Commands Tests (Priority: Medium)
```python
# tests/test_auth_commands.py

def test_auth_login_success(runner, tmp_path):
    # Mock file operations
    # Test login command

def test_auth_logout(runner, tmp_path):
    # Test logout command

def test_auth_status(runner, tmp_path):
    # Test status command
```

### Task 4: Bulk Command Coverage (Priority: Medium)
```python
# tests/test_bulk_coverage.py

@pytest.mark.simulation
def test_bulk_apply_dry_run(runner, mock_asc_whisper, tmp_path):
    # Create YAML config
    # Test dry-run apply

@pytest.mark.simulation
def test_bulk_apply_invalid_yaml(runner, mock_asc_api, tmp_path):
    # Test with invalid YAML

@pytest.mark.simulation
def test_bulk_apply_missing_subscription(runner, mock_asc_api, tmp_path):
    # Test error handling
```

### Task 5: TestFlight Simulator (Priority: Low)
```python
# tests/simulation/routes/testflight.py

def handle_list_builds(request, state, app_id):
    # Return builds for app

def handle_list_beta_groups(request, state, app_id):
    # Return beta groups

def handle_list_beta_testers(request, state, group_id):
    # Return testers
```

---

## Expected Coverage After Each Phase

| Phase | Module | Before | After | Tests Added |
|-------|--------|--------|-------|-------------|
| 1 | api/auth.py | 69% | 92% | 8 |
| 2 | api/client.py | 60% | 85% | 10 |
| 3 | commands/auth.py | 18% | 90% | 6 |
| 4 | commands/bulk.py | 19% | 85% | 8 |
| 5 | commands/subscriptions.py | 67% | 90% | 12 |
| 6 | commands/testflight.py | 77% | 90% | 5 |

**Overall:** 57% → ~88%

To reach 90%+:
- Add more edge case tests for client.py
- Add more bulk operation scenarios
- Complete TestFlight implementation

---

## Implementation Order

1. **Auth module tests** (quick win, file mocking)
2. **Bulk command tests** (use existing simulation)
3. **Subscriptions edge cases** (use existing simulation)
4. **Client error tests** (extend simulation)
5. **Auth commands** (file mocking + simulation)
6. **TestFlight** (new simulation routes)

Each phase is independent and can be done incrementally.
