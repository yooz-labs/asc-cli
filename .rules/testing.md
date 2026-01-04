# Testing Standards - NO MOCKS Policy

## Core Philosophy: Test Reality, Not Fiction
**Why NO MOCKS?** Mocks test your assumptions, not your code.
**Real bugs** hide in integration points, not unit logic.
**Better approach:** No test is better than a false-confidence mock test.

## [STRICT] NO MOCKS, NO FAKE DATA
Never use mocks, stubs, or fake datasets. If real testing isn't possible, don't write tests.
- **No mock objects** - Use real implementations
- **No mock datasets** - Use actual API responses
- **No stub services** - Connect to real test instances
- **Alternative:** Ask for test credentials or sandbox access

## When to Write Tests
- **DO:** Test with real data and actual dependencies
- **DO:** Use recorded API responses (VCR pattern) if sandbox unavailable
- **DO:** Test against App Store Connect sandbox environment
- **DON'T:** Write tests if only mocks would work
- **DON'T:** Create artificial test scenarios

## Test Structure
```
tests/
  conftest.py          # Real test fixtures
  sample_data/         # Actual API response samples
    apps/
    subscriptions/
  integration/         # Tests with real API
    test_auth.py       # Real JWT generation
    test_client.py     # Real API calls
  unit/                # Pure logic tests (no I/O)
    test_parsing.py    # Response parsing
```

## Frameworks
- **pytest:** Test runner
- **pytest-cov:** Coverage reporting (95% target)
- **pytest-asyncio:** Async test support
- **respx:** HTTP recording (NOT mocking - recording real responses)

## Writing Real Tests
```python
# GOOD: Tests actual JWT generation
def test_jwt_token_generation(real_credentials):
    """Tests that JWT tokens are valid and can authenticate."""
    token = generate_token(real_credentials)
    # This catches: JWT encoding issues, credential problems
    assert token.startswith("eyJ")
    assert len(token.split(".")) == 3

# BAD: Tests nothing meaningful
# def test_jwt_token(mock_jwt):  # NO!
#     mock_jwt.return_value = "fake"  # Tests that Python works?
```

## Test Data Management
- **Sample data:** Request from user or use real API responses
- **Credentials:** Store in .env (never commit)
- **Recorded responses:** Use respx to record real API calls
- **Skip if unavailable:** `pytest.mark.skipif` for missing credentials

## CI Integration
- Run tests with real test environment when credentials available
- Skip integration tests in CI if credentials unavailable
- Document required test infrastructure

## When Real Testing Seems Impossible
**Think creatively before giving up:**
- Can you use App Store Connect sandbox?
- Can you record real API responses for replay?
- Can you test the parsing logic separately from API calls?

**If truly impossible:**
1. Document needs in test file
2. Explain to user what's needed
3. Ask for:
   - Sandbox API credentials
   - Sample API responses
4. **Be honest:** "Without real test data, I cannot verify this works"

---
*NO MOCKS. Real tests build real confidence. When in doubt, ask for real data.*
