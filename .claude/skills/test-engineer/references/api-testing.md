# API Testing Patterns

## Route Detection

```bash
# Next.js App Router
find ./app/api -name "route.ts" | while read f; do
    route=$(echo $f | sed 's|./app||;s|/route.ts||')
    methods=$(grep -oE "export (async )?function (GET|POST|PUT|PATCH|DELETE)" "$f" | grep -oE "(GET|POST|PUT|PATCH|DELETE)")
    echo "$methods $route"
done

# Express/FastAPI — grep for route decorators
grep -rn "@router\|app\.get\|app\.post\|@app\.route" src/
```

## Test Matrix Template

For every route, cover:

| Category | Tests |
|---|---|
| **Auth** | valid token ✅, no token → 401, expired token → 401, wrong role → 403 |
| **Validation** | missing required field → 422, wrong type → 422, boundary values, injection attempt |
| **Happy path** | valid input → 200/201 with expected shape |
| **Not found** | unknown ID → 404 |
| **Conflict** | duplicate create → 409 |
| **Server error** | db failure → 500 (mock the dependency) |

## Node.js — Vitest + Supertest

```typescript
// tests/api/users.test.ts
import { describe, it, expect, beforeAll, afterAll, vi } from 'vitest';
import request from 'supertest';
import app from '../../src/app';
import { db } from '../../src/db';

describe('POST /api/users', () => {
    it('creates user and returns 201', async () => {
        const res = await request(app)
            .post('/api/users')
            .send({ email: 'new@example.com', name: 'Bond' });

        expect(res.status).toBe(201);
        expect(res.body).toMatchObject({
            id: expect.any(String),
            email: 'new@example.com',
        });
        expect(res.body.password).toBeUndefined(); // never expose password
    });

    it('returns 422 when email is missing', async () => {
        const res = await request(app)
            .post('/api/users')
            .send({ name: 'Bond' });  // no email

        expect(res.status).toBe(422);
        expect(res.body.errors).toContainEqual(
            expect.objectContaining({ field: 'email' })
        );
    });

    it('returns 409 on duplicate email', async () => {
        await request(app).post('/api/users').send({ email: 'dup@example.com', name: 'A' });
        const res = await request(app).post('/api/users').send({ email: 'dup@example.com', name: 'B' });
        expect(res.status).toBe(409);
    });
});

describe('GET /api/users/:id', () => {
    it('returns 404 for unknown user', async () => {
        const res = await request(app).get('/api/users/nonexistent-id');
        expect(res.status).toBe(404);
    });

    it('returns 401 without auth token', async () => {
        const res = await request(app).get('/api/users/me');
        expect(res.status).toBe(401);
    });

    it('returns 403 when accessing another user as non-admin', async () => {
        const res = await request(app)
            .get('/api/users/other-user-id')
            .set('Authorization', `Bearer ${userToken}`);
        expect(res.status).toBe(403);
    });
});
```

## Python — pytest + httpx

```python
# tests/test_api_users.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_user_success():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/users", json={
            "email": "bond@example.com",
            "name": "Bond"
        })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "bond@example.com"
    assert "password" not in data

@pytest.mark.asyncio
async def test_create_user_missing_email():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/users", json={"name": "Bond"})
    assert response.status_code == 422
    assert any(e["loc"] == ["body", "email"] for e in response.json()["detail"])

@pytest.mark.asyncio
async def test_get_user_unauthenticated():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/users/me")
    assert response.status_code == 401
```

## Pagination Tests

```typescript
it('returns first page with correct cursor', async () => {
    const res = await request(app).get('/api/posts?limit=10');
    expect(res.body.data).toHaveLength(10);
    expect(res.body.next_cursor).toBeDefined();
});

it('returns empty data at end of list', async () => {
    const res = await request(app).get(`/api/posts?cursor=${lastCursor}&limit=10`);
    expect(res.body.data).toHaveLength(0);
    expect(res.body.next_cursor).toBeNull();
});
```

## Contract Testing (response shape)

```typescript
// Validate exact response shape — catches breaking changes
const USER_SCHEMA = {
    id: expect.any(String),
    email: expect.any(String),
    name: expect.any(String),
    created_at: expect.any(String),
    // password must NOT appear
};

it('GET /api/users/:id matches user contract', async () => {
    const res = await request(app)
        .get(`/api/users/${userId}`)
        .set('Authorization', `Bearer ${adminToken}`);
    
    expect(res.status).toBe(200);
    expect(res.body).toMatchObject(USER_SCHEMA);
    expect(res.body).not.toHaveProperty('password');
    expect(res.body).not.toHaveProperty('password_hash');
});
```

## Error Response Shape (enforce consistently)

```typescript
// All error responses should follow this shape
const ERROR_SCHEMA = {
    error: expect.any(String),   // human-readable message
    code: expect.any(String),    // machine-readable code  
};

// Optionally for 422:
const VALIDATION_ERROR_SCHEMA = {
    errors: expect.arrayContaining([
        expect.objectContaining({ field: expect.any(String), message: expect.any(String) })
    ])
};
```
