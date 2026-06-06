---
name: testing-framework-pro
description: >-
  Comprehensive testing methodology covering strategy, frameworks, patterns,
  and debugging. Unit, integration, E2E, load, contract, property-based, and
  mutation testing. Python (pytest) and TypeScript (Vitest/Playwright/k6).
  Fix flaky tests, design test strategies, set up CI integration.
triggers:
  - "write tests for"
  - "set up testing framework"
  - "unit test"
  - "integration test"
  - "end-to-end test"
  - "e2e"
  - "TDD"
  - "pytest"
  - "Jest"
  - "Vitest"
  - "Playwright"
  - "load test"
  - "k6"
  - "test coverage"
  - "mock"
  - "fixture"
  - "flaky test"
  - "test strategy"
  - "my tests are slow"
  - "how do I test this"
tags: [testing, pytest, vitest, playwright, k6, tdd, coverage, mocking, ci]
author: next-gen
---

# Testing Framework Pro

## Identity

Tests are the safety net that makes refactoring possible. Follow the pyramid: many fast unit tests, fewer integration tests, minimal E2E. Fix flaky tests immediately — they erode trust faster than no tests. Never test implementation; test behavior.

## Stack Defaults

| Test Type | Python | TypeScript |
|-----------|--------|-----------|
| Unit | pytest | Vitest |
| Integration | pytest + TestClient | Vitest + supertest |
| E2E | Playwright | Playwright |
| Load | k6 | k6 |
| Mocking | unittest.mock / pytest-mock | vi.mock / vi.spyOn |
| Test DB | testcontainers / SQLite | testcontainers |
| Contract | Pact | Pact |
| Property | hypothesis | fast-check |
| Mutation | mutmut | Stryker |

## Decision Framework

```
IF writing new code:
  → TDD for well-defined logic: test → fail → implement → refactor
  → Test behavior (inputs/outputs), not implementation (internal calls)
  → Name: test_<what>_<condition>_<expected_outcome>

IF choosing test type:
  → Unit (70%): pure functions, no I/O, mocked dependencies
  → Integration (20%): real DB (transaction-rollback), real API routes
  → E2E (10%): critical user journeys only (login, checkout, signup)
  → Load: before major releases or when SLA is latency-sensitive

IF test is flaky:
  → Find root cause: shared state? timing? network? random data?
  → Fix: isolate state, mock time, deterministic data, explicit waits
  → Never mark as skip — flaky tests are bugs

IF mocking:
  → Mock external services (APIs, email, S3)
  → Do NOT mock the code under test
  → Do NOT over-mock (couples tests to implementation)
```

## Anti-Patterns

| Anti-Pattern | Use Instead |
|--------------|-------------|
| "Ice cream cone" (mostly E2E) | Test pyramid: 70% unit, 20% integration, 10% E2E |
| Testing implementation details | Test behavior (public API inputs/outputs) |
| Global shared test data | Each test owns its data; factories not fixed fixtures |
| Flaky test marked as `skip` | Fix root cause (shared state, timing, network) |
| No test isolation (DB not cleaned) | Transaction rollback per test or testcontainers |
| 100% line coverage as goal | Focus on branch coverage + mutation testing |
| `mock.patch` entire modules | Patch at the injection point; test real logic |

## Quality Gates

- [ ] Business logic: ≥ 90% coverage
- [ ] API handlers: ≥ 80% coverage
- [ ] DB queries: 100% (via integration tests)
- [ ] No flaky tests in CI (max 0 retries on passing suite)
- [ ] Test names describe behavior (not `test_function_2`)
- [ ] Load test passes SLA thresholds before production release
- [ ] Mutation score > 70% for critical modules

→ See `cicd-pipeline` for parallel test execution in GitHub Actions  
→ See `full-sdlc` for test pyramid in SDLC context

---

## Unit Testing

### Python (pytest)

```python
# tests/test_payment.py
import pytest
from src.payment import process_payment, PaymentError

class TestProcessPayment:
    def test_successful_charge_returns_transaction_id(self):
        result = process_payment(amount=100, token="tok_valid")
        assert result.transaction_id is not None
        assert result.success is True

    def test_expired_card_raises_payment_error(self):
        with pytest.raises(PaymentError, match="card_expired"):
            process_payment(amount=100, token="tok_expired")

    @pytest.mark.parametrize("amount,expected_fee", [
        (100, 2.9),
        (1000, 29.0),
        (0, 0),
    ])
    def test_fee_calculation(self, amount, expected_fee):
        assert process_payment(amount, "tok_valid").fee == pytest.approx(expected_fee, rel=0.01)
```

Run: `pytest tests/ -x -v` | `pytest -k "test_expired"` | `pytest --pdb`

### TypeScript (Vitest)

```typescript
// payment.test.ts
import { describe, it, expect } from 'vitest'
import { processPayment } from './payment'

describe('processPayment', () => {
  it('returns transaction id on success', async () => {
    const result = await processPayment({ amount: 100, token: 'tok_valid' })
    expect(result.transactionId).toMatch(/^ch_/)
    expect(result.success).toBe(true)
  })

  it('throws on expired card', async () => {
    await expect(
      processPayment({ amount: 100, token: 'tok_expired' })
    ).rejects.toThrow('card_expired')
  })

  it.each([
    [100, 2.9],
    [1000, 29.0],
    [0, 0],
  ])('fee for $%i is $%d', async (amount, expectedFee) => {
    const result = await processPayment({ amount, token: 'tok_valid' })
    expect(result.fee).toBeCloseTo(expectedFee, 1)
  })
})
```

---

## Fixtures & Test Data

### pytest Fixtures

```python
# conftest.py
import pytest
from sqlalchemy.orm import Session

@pytest.fixture
def db_session():
    """Clean session per test via transaction rollback."""
    session = create_test_session()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def user_factory(db_session):
    """Factory: create users with overridable defaults."""
    def _factory(**kwargs):
        defaults = {"name": "Test User", "email": "test@example.com", "role": "user"}
        user = User(**{**defaults, **kwargs})
        db_session.add(user)
        db_session.flush()
        return user
    return _factory

def test_admin_can_delete_post(user_factory, db_session):
    admin = user_factory(role="admin")
    post = Post(author_id=admin.id, content="hello")
    db_session.add(post)
    db_session.flush()
    assert delete_post(admin, post.id) is True
```

### Test Data Principles

- **Tests own their data** — never depend on shared global state
- **Factories over fixtures** — `create_user(role="admin")` beats a fixed `admin_user` fixture
- **Minimal data** — create only what the test requires
- **Deterministic** — no random data in assertions; use `faker.seed(42)` if needed

---

## Mocking

### Python

```python
from unittest.mock import patch, AsyncMock

@patch('src.services.payment.stripe.Charge.create')
def test_payment_calls_stripe(mock_stripe):
    mock_stripe.return_value = Mock(id='ch_123', status='succeeded')
    result = process_payment(amount=1000, token='tok_test')
    assert result.success is True
    mock_stripe.assert_called_once_with(amount=1000, source='tok_test')

@patch('src.services.api.fetch_user', new_callable=AsyncMock)
async def test_profile_uses_fetched_data(mock_fetch):
    mock_fetch.return_value = {"name": "Drew", "role": "admin"}
    profile = await get_profile(user_id=1)
    assert profile.role == "admin"
```

### TypeScript

```typescript
import { vi, describe, it, expect, beforeEach } from 'vitest'
import { fetchUser } from './api'

vi.mock('./api', () => ({
  fetchUser: vi.fn()
}))

describe('getProfile', () => {
  beforeEach(() => vi.clearAllMocks())

  it('returns profile from fetched user', async () => {
    vi.mocked(fetchUser).mockResolvedValue({ name: 'Drew', role: 'admin' })
    const profile = await getProfile(1)
    expect(profile.role).toBe('admin')
  })
})
```

---

## Integration Testing

### FastAPI + Real DB

```python
# tests/integration/test_users_api.py
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

def test_create_user():
    resp = client.post("/users", json={"name": "Drew", "email": "drew@example.com"})
    assert resp.status_code == 201
    assert resp.json()["name"] == "Drew"

def test_duplicate_email_returns_409():
    client.post("/users", json={"name": "Drew", "email": "drew@example.com"})
    resp = client.post("/users", json={"name": "Drew2", "email": "drew@example.com"})
    assert resp.status_code == 409
```

### Testcontainers (Real Docker DB)

```python
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg.get_connection_url()
```

---

## E2E Testing (Playwright)

```python
from playwright.sync_api import expect

def test_login_redirects_to_dashboard(page):
    page.goto("/login")
    page.fill("#email", "user@example.com")
    page.fill("#password", "password123")
    page.click("button[type='submit']")
    expect(page).to_have_url("/dashboard")
    expect(page.locator("h1")).to_have_text("Welcome back")
```

**Best practices:**
- Test critical flows only (login, checkout, signup) — not every feature
- Use `data-testid` attributes for selectors (stable across UI refactors)
- Page Object Model for reusable page interactions
- Reset DB state between E2E test runs
- Playwright auto-retries assertions; set explicit timeouts for slow ops

---

## Load Testing (k6)

```javascript
import http from 'k6/http'
import { check, sleep } from 'k6'

export const options = {
  stages: [
    { duration: '30s', target: 20 },   // Ramp up
    { duration: '1m', target: 20 },    // Steady state
    { duration: '10s', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],  // 95th percentile < 500ms
    http_req_failed: ['rate<0.01'],    // Error rate < 1%
  }
}

export default function () {
  const res = http.get('http://localhost:8080/api/users')
  check(res, { 'status 200': (r) => r.status === 200 })
  sleep(1)
}
```

Run: `k6 run load_test.js`

| Test Type | Purpose |
|-----------|---------|
| Smoke | Minimal load — verify system works at all |
| Load | Expected prod traffic — verify perf targets |
| Stress | Beyond expected — find breaking point |
| Soak | Hours of sustained load — find memory leaks |
| Spike | Sudden burst — verify recovery |

---

## CI Integration

```yaml
# .github/workflows/test.yml
jobs:
  unit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.txt
      - run: pytest tests/unit/ -x --tb=short -q

  integration:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.txt
      - run: pytest tests/integration/ --tb=short

  e2e:
    needs: [unit, integration]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install playwright && playwright install chromium
      - run: pytest tests/e2e/
```

**Coverage reporting:**

```bash
coverage run -m pytest && coverage report --fail-under=80
coverage xml -o coverage.xml   # For CI artifact upload
```

---

## Debugging Failing Tests

| Symptom | Cause | Fix |
|---------|-------|-----|
| Flaky (random pass/fail) | Shared state / timing | Isolate state, mock time, deterministic seeds |
| Pass locally, fail in CI | OS/timezone/deps diff | Docker-based CI, pin all deps |
| Slow suite | Too many E2E, no parallelism | Move to unit, parallelize: `pytest -n auto` |
| Tests break on refactor | Testing implementation | Test behavior (public API), not internals |
| Timeout on external call | Unmocked network | Mock external services in unit/integration |
| Coverage gap found | Mutation survived | Add test that kills the mutant |

**pytest flags:**
- `-x` stop on first fail
- `-s` show print output
- `--pdb` debugger on fail
- `-k "test_name"` run specific test
- `--lf` re-run last failures only
