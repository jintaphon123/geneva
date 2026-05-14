# Testing Patterns

## Unit Testing — React/TypeScript (Jest + RTL)

### Component Test Template
```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LoginForm } from './LoginForm';

describe('LoginForm', () => {
    it('shows error when submitting empty email', async () => {
        const user = userEvent.setup();
        render(<LoginForm onSubmit={jest.fn()} />);
        
        await user.click(screen.getByRole('button', { name: /sign in/i }));
        
        expect(screen.getByText(/email is required/i)).toBeInTheDocument();
    });

    it('calls onSubmit with credentials on valid form', async () => {
        const user = userEvent.setup();
        const onSubmit = jest.fn();
        render(<LoginForm onSubmit={onSubmit} />);
        
        await user.type(screen.getByLabelText(/email/i), 'test@example.com');
        await user.type(screen.getByLabelText(/password/i), 'password123');
        await user.click(screen.getByRole('button', { name: /sign in/i }));
        
        expect(onSubmit).toHaveBeenCalledWith({
            email: 'test@example.com',
            password: 'password123',
        });
    });
});
```

### Custom Hook Test (renderHook)
```typescript
import { renderHook, act } from '@testing-library/react';
import { useCounter } from './useCounter';

it('increments count', () => {
    const { result } = renderHook(() => useCounter(0));
    act(() => { result.current.increment(); });
    expect(result.current.count).toBe(1);
});
```

### API Mock with MSW
```typescript
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';

const server = setupServer(
    http.get('/api/users', () => HttpResponse.json([{ id: 1, name: 'Bond' }])),
    http.post('/api/login', () => HttpResponse.json({ token: 'fake-jwt' })),
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// Override for specific test
it('handles 500 error', async () => {
    server.use(http.get('/api/users', () => new HttpResponse(null, { status: 500 })));
    // ... test error state
});
```

### Async Testing Patterns
```typescript
// waitFor — polling assertions
await waitFor(() => expect(screen.getByText('Loaded')).toBeInTheDocument());

// findBy — returns promise (waitFor shortcut)
const item = await screen.findByText('Loaded');

// Avoid: waitFor wrapping fireEvent
// Use: act() for state-updating code outside RTL
```

## Unit Testing — Python (pytest)

### Basic Pattern
```python
import pytest
from unittest.mock import Mock, patch, AsyncMock

class TestUserService:
    def test_creates_user_with_hashed_password(self, db_session):
        service = UserService(db_session)
        user = service.create_user(email='test@example.com', password='raw-pass')
        assert user.email == 'test@example.com'
        assert user.password_hash != 'raw-pass'
        assert bcrypt.checkpw(b'raw-pass', user.password_hash.encode())

    def test_raises_on_duplicate_email(self, db_session, existing_user):
        service = UserService(db_session)
        with pytest.raises(DuplicateEmailError):
            service.create_user(email=existing_user.email, password='any')

    @pytest.mark.asyncio
    async def test_async_fetch(self):
        with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value.json.return_value = {'data': []}
            result = await fetch_external_data()
            assert result == []
```

### Fixtures (conftest.py)
```python
@pytest.fixture
def db_session():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()

@pytest.fixture
def existing_user(db_session):
    user = User(email='existing@example.com', password_hash='hashed')
    db_session.add(user)
    db_session.commit()
    return user
```

## TDD Workflow

### RED — Write a Failing Test
```typescript
// Write this BEFORE the implementation exists
it('calculates 20% discount on orders above ฿1000', () => {
    const order = { total: 1500, items: 3 };
    expect(calculateDiscount(order)).toBe(300); // 20% of 1500
});
// Run: jest — expect it to fail (function doesn't exist yet)
```

### GREEN — Minimal Implementation
```typescript
// Write EXACTLY enough to pass — no more
export function calculateDiscount(order: { total: number }): number {
    if (order.total > 1000) return order.total * 0.2;
    return 0;
}
// Run: jest — should pass now
```

### REFACTOR — Clean Without Breaking
```typescript
// Safe: extract constant, rename variable, add type
const BULK_DISCOUNT_THRESHOLD = 1000;
const BULK_DISCOUNT_RATE = 0.2;

export function calculateDiscount(order: Order): number {
    return order.total > BULK_DISCOUNT_THRESHOLD
        ? order.total * BULK_DISCOUNT_RATE
        : 0;
}
// Run: jest — all tests must still pass
```

## Coverage Analysis

```bash
# Jest
npx jest --coverage --coverageReporters=text-summary

# Look for: Branches column — uncovered branches are usually bugs
# Red flag: covered lines but uncovered branches = if/else not tested

# Vitest
npx vitest run --coverage

# Istanbul: branches < 70% → priority to add edge case tests
```

### Coverage Priorities (by impact)
1. **Untested error paths** — most bugs live here
2. **Uncovered branches** (`if`/`else`/`switch` arms not reached)
3. **Zero-coverage files** — often completely untested modules
4. Skip: getters/setters, framework boilerplate, generated code

## Common Anti-Patterns

| Anti-Pattern | Fix |
|---|---|
| `renders correctly` test | Test actual content the user sees |
| Testing implementation (`useState` value) | Test rendered output or user-visible behavior |
| Snapshot tests for complex components | Explicit assertions on specific elements |
| `beforeEach` that sets up what only one test needs | Move setup into the test that needs it |
| `any` type in test assertions | Explicit type or `as ExpectedType` |
| Sleeping to wait for async (`setTimeout`) | `waitFor` or `findBy` |
