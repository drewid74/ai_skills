---
name: testing-framework
description: "Use this skill whenever the user wants to write, organize, debug, or improve tests for their software. Triggers include: any mention of 'test', 'testing', 'unit test', 'integration test', 'end-to-end', 'e2e', 'TDD', 'test-driven', 'BDD', 'pytest', 'Jest', 'Vitest', 'Mocha', 'Cypress', 'Playwright', 'Selenium', 'k6', 'load test', 'performance test', 'stress test', 'benchmark', 'test coverage', 'coverage report', 'mock', 'stub', 'spy', 'fixture', 'factory', 'conftest', 'beforeEach', 'afterAll', 'describe', 'it', 'expect', 'assert', 'snapshot test', 'visual regression', 'contract test', 'Pact', 'API test', 'smoke test', 'regression test', 'flaky test', 'test strategy', 'test pyramid', 'test plan', 'mutation testing', 'property-based testing', 'fuzzing', 'test data', 'test isolation', 'test parallelism', 'CI test', or any request to add tests, fix failing tests, improve test coverage, debug test failures, set up a testing framework, or design a testing strategy. Also use when the user says 'this test is flaky', 'how do I test this?', 'my tests are slow', or shares code and asks about testability. If someone needs any kind of software testing guidance, use this skill."
---

# Testing Framework

Comprehensive testing methodology covering strategy, frameworks, patterns, and debugging across unit, integration, e2e, load, and specialty testing. Framework-agnostic principles with practical examples for Python (pytest) and JavaScript/TypeScript (Jest/Vitest/Playwright).

## Testing Strategy

### The Testing Pyramid

Structure tests as a pyramid, not an ice cream cone:

- **Unit tests (70%)**: fast, isolated, test single functions/classes. Run in seconds.
- **Integration tests (20%)**: test component interactions—API + database, service + service. Run in seconds to minutes.
- **E2E tests (10%)**: full user workflows through real UI. Run in minutes.

Why this ratio? Unit tests give fast feedback and cheap maintenance. Integration tests catch real-world interaction bugs. E2E tests verify complete features but are slow and brittle.

Anti-pattern: "Ice cream cone" (mostly e2e, few unit tests) means slow CI, flaky tests, and painful debugging.

### When to Write Tests

**Test-Driven Development (TDD)**: write test → watch it fail → write minimum code to pass → refactor. Best for well-defined requirements, complex logic, and APIs.

**After code**: write tests for existing code to prevent regressions. Best for legacy code and rapid prototyping that needs stabilization.

**What to test**: business logic, edge cases, error handling, security-critical paths, complex algorithms.

**What NOT to test**: framework internals, trivial getters/setters, third-party library behavior. Test behavior and outputs, not implementation details.

## Unit Testing

### Python (pytest)

```python
# tests/test_calculator.py
import pytest
from src.calculator import Calculator

class TestCalculator:
    def test_add_positive_numbers(self):
        calc = Calculator()
        assert calc.add(2, 3) == 5

    def test_divide_by_zero_raises(self):
        calc = Calculator()
        with pytest.raises(ZeroDivisionError):
            calc.divide(10, 0)

    @pytest.mark.parametrize("a,b,expected", [
        (1, 1, 2), (0, 0, 0), (-1, 1, 0), (100, 200, 300)
    ])
    def test_add_parametrized(self, a, b, expected):
        assert Calculator().add(a, b) == expected
```

Run with: `pytest tests/` or `pytest tests/test_calculator.py::TestCalculator::test_add_positive_numbers`

### JavaScript/TypeScript (Vitest/Jest)

```typescript
// calculator.test.ts
import { describe, it, expect } from 'vitest'
import { Calculator } from './calculator'

describe('Calculator', () => {
  it('adds positive numbers', () => {
    const calc = new Calculator()
    expect(calc.add(2, 3)).toBe(5)
  })

  it('throws on divide by zero', () => {
    const calc = new Calculator()
    expect(() => calc.divide(10, 0)).toThrow('Division by zero')
  })

  it.each([
    [1, 1, 2], [0, 0, 0], [-1, 1, 0]
  ])('add(%i, %i) = %i', (a, b, expected) => {
    expect(new Calculator().add(a, b)).toBe(expected)
  })
})
```

Run with: `vitest` or `npm test`

### Naming Conventions

Write test names as documentation: `test_<what>_<condition>_<expected>`

Examples: `test_login_with_invalid_password_returns_401`, `test_empty_cart_shows_message`

Group related tests using pytest classes or describe blocks.

## Fixtures and Test Data

### pytest Fixtures

Create reusable test setup:

```python
# conftest.py
import pytest

@pytest.fixture
def db_session():
    """Provide a clean database session for each test."""
    session = create_test_session()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def sample_user(db_session):
    """Create a sample user for tests that need one."""
    user = User(name="Test User", email="test@example.com")
    db_session.add(user)
    db_session.flush()
    return user

def test_user_has_name(sample_user):
    assert sample_user.name == "Test User"
```

- `conftest.py`: shared fixtures auto-discovered by pytest
- Scope: `function` (default), `class`, `module`, `session`
- Use factories (faker, factory_boy) for variable test data, not fixed fixtures

### Jest/Vitest Setup

```typescript
let db: Database

beforeEach(async () => {
  db = await createTestDatabase()
})

afterEach(async () => {
  await db.cleanup()
})
```

### Test Data Principles

- **Tests own their data**: never depend on shared/global test data
- **Factories over fixtures**: `createUser({admin: true})` beats a fixed `adminUser` fixture
- **Minimal data**: create only what the test needs, not a "kitchen sink"
- **Deterministic**: no random data in assertions (use seeds if randomness needed)

## Mocking and Isolation

### When to Mock

Mock external services (APIs, databases, file systems, email), time-dependent behavior (dates, timers), expensive operations (network calls, computation), and non-deterministic behavior (random, OS-level).

Do NOT mock the code under test (you'd be testing nothing), simple data structures (just create real ones), or everything (over-mocking makes tests brittle and coupled to implementation).

### Python Mocking

```python
from unittest.mock import Mock, patch, AsyncMock

# Patch external dependency
@patch('src.services.payment.stripe.Charge.create')
def test_process_payment(mock_stripe):
    mock_stripe.return_value = Mock(id='ch_123', status='succeeded')
    result = process_payment(amount=1000, token='tok_test')
    assert result.success is True
    mock_stripe.assert_called_once_with(amount=1000, source='tok_test')

# Async mock
@patch('src.services.api.fetch_user', new_callable=AsyncMock)
async def test_get_profile(mock_fetch):
    mock_fetch.return_value = {"name": "Drew", "role": "admin"}
    profile = await get_profile(user_id=1)
    assert profile.name == "Drew"
```

### JavaScript Mocking

```typescript
import { vi, describe, it, expect } from 'vitest'

// Mock module
vi.mock('./api', () => ({
  fetchUser: vi.fn().mockResolvedValue({ name: 'Drew', role: 'admin' })
}))

// Spy on existing method
const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
// ... test code ...
expect(spy).toHaveBeenCalledWith('expected error message')
```

## Integration Testing

### Database Integration Tests

- Use a real database (testcontainers or Docker Compose for CI)
- Wrap each test in a transaction and rollback after (fast cleanup)
- Dedicated test database: never mix with development data
- Seed known state before test suite, clean between tests

### API Integration Tests

```python
# FastAPI example with TestClient
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

def test_create_user():
    response = client.post("/users", json={"name": "Drew", "email": "drew@example.com"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Drew"
    assert "id" in data

def test_create_user_duplicate_email():
    client.post("/users", json={"name": "Drew", "email": "drew@example.com"})
    response = client.post("/users", json={"name": "Drew2", "email": "drew@example.com"})
    assert response.status_code == 409
```

### Testcontainers

Spin up real Docker containers (PostgreSQL, Redis, etc.) for tests. Clean, isolated, matches production. Python: `testcontainers` library; JS: `testcontainers` npm package. Slower than mocks but higher confidence in integration correctness.

## End-to-End Testing

### Playwright (Recommended)

```python
from playwright.sync_api import expect

def test_user_login_flow(page):
    page.goto("/login")
    page.fill("#email", "user@example.com")
    page.fill("#password", "password123")
    page.click("button[type='submit']")
    expect(page).to_have_url("/dashboard")
    expect(page.locator("h1")).to_have_text("Welcome back")
```

### E2E Best Practices

- Test critical user journeys (login, checkout, signup), not every feature
- Use `data-testid` attributes for selectors (stable across UI changes)
- Page Object Model: abstract page interactions into reusable classes
- Reset state between tests (clean database, fresh session)
- Keep E2E tests independent (no test ordering dependencies)
- Playwright auto-retries flaky assertions; configure timeout as needed

### Visual Regression Testing

- Screenshot comparison between test runs catches unintended CSS changes
- Tools: Playwright `toHaveScreenshot()`, Percy, Chromatic, BackstopJS
- Maintain baseline screenshots in git or CI artifact storage
- Review visual diffs on PR

## Load and Performance Testing

### k6 (Recommended)

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
    http_req_duration: ['p(95)<500'], // 95th percentile under 500ms
    http_req_failed: ['rate<0.01'],   // Error rate under 1%
  }
}

export default function () {
  const res = http.get('http://localhost:8080/api/users')
  check(res, { 'status 200': (r) => r.status === 200 })
  sleep(1)
}
```

Run with: `k6 run load_test.js`

### Load Test Types

- **Smoke test**: minimal load, verify system works at all
- **Load test**: expected production traffic, verify performance targets
- **Stress test**: beyond expected load, find breaking point
- **Soak test**: sustained load over hours, find memory leaks
- **Spike test**: sudden burst, verify recovery

### Performance Metrics

- **Response time** (p50, p95, p99): most requests fast, but watch the tail
- **Throughput** (requests/second): capacity
- **Error rate**: percentage of failed requests
- **Resource utilization**: CPU, memory, connections during load

## Specialty Testing

### Contract Testing (Pact)

Verify API consumers and providers agree on interface. Consumer writes expectations, provider verifies against them. Catches breaking API changes before deployment. Use when multiple services depend on each other's APIs.

### Property-Based Testing

Generate random inputs, verify properties always hold. Python: `hypothesis`; JS: `fast-check`. Example: "sorting any list produces a list of the same length with same elements in non-decreasing order." Finds edge cases you wouldn't think to test manually.

### Mutation Testing

Introduce small code changes (mutations) and verify tests catch them. If a mutation survives, you have a coverage gap. Tools: mutmut (Python), Stryker (JS/TS). More meaningful than line coverage.

## Test Organization and CI

### Project Structure

```
tests/
├── unit/              # Fast, isolated tests
│   ├── test_models.py
│   └── test_services.py
├── integration/       # Tests with real dependencies
│   ├── test_api.py
│   └── test_database.py
├── e2e/              # Full workflow tests
│   └── test_user_flows.py
├── load/             # Performance tests
│   └── load_test.js
├── conftest.py       # Shared fixtures
└── factories.py      # Test data factories
```

### CI Integration

- Run unit tests on every push (fast feedback, seconds)
- Run integration tests on PR (before merge, minutes)
- Run e2e tests on merge to main (before deploy, minutes)
- Run load tests on schedule or before major releases
- Parallel execution: split tests across workers

### Coverage

- Target 80% line coverage as a floor, not a ceiling
- Focus on branch coverage (does every if/else path execute?)
- Configure CI to report coverage but don't block on it
- Exclude: generated code, migrations, type stubs, config files

## Debugging Failing Tests

### Common Issues and Fixes

- **Flaky tests** (pass/fail randomly): caused by shared state, timing dependencies, network calls, random data. Fix: isolate state, mock time, use deterministic data.
- **Tests pass locally, fail in CI**: environment differences (OS, timezone, locale, dependency versions). Fix: Docker-based CI, pin all dependencies.
- **Slow test suite**: too many e2e tests, no parallelism, repeated expensive setup. Fix: follow pyramid, parallelize, share expensive fixtures at higher scope.
- **Tests coupled to implementation**: tests break on refactoring even though behavior unchanged. Fix: test behavior (inputs/outputs), not implementation (internal method calls).
- **Intermittent timeout**: external dependency slow or unreachable. Fix: mock external services in unit/integration tests, set explicit timeouts.

### Debugging Tools

**pytest**: `-x` (stop on first failure), `-s` (show print output), `--pdb` (debugger on failure), `-k "test_name"` (run specific test)

**Vitest/Jest**: `.only` (single test), `--watch` (rerun on changes), `--verbose` (detailed output)

**Playwright**: `--headed` (show browser), `--debug` (step through), trace viewer for recorded runs
