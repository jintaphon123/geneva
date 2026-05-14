# API Design Patterns

## REST Conventions

### URL Structure
```
✅ Good
GET    /api/v1/users               — list
POST   /api/v1/users               — create
GET    /api/v1/users/:id           — get one
PUT    /api/v1/users/:id           — full replace
PATCH  /api/v1/users/:id          — partial update
DELETE /api/v1/users/:id          — delete

GET    /api/v1/users/:id/orders   — nested resource
POST   /api/v1/orders/:id/cancel  — action (POST on action noun, not PUT/PATCH)

❌ Wrong
GET    /api/getUsers               — verb in URL
POST   /api/user/create            — singular + action
DELETE /api/users/deleteAll        — danger: mass delete without safety
```

### HTTP Status Codes
```
200 OK            — successful GET, PUT, PATCH
201 Created       — successful POST (include Location header with new resource URL)
204 No Content    — successful DELETE, or PUT/PATCH with no response body
400 Bad Request   — malformed request (syntax, missing fields)
401 Unauthorized  — not authenticated (no valid token)
403 Forbidden     — authenticated but not authorized (wrong role/ownership)
404 Not Found     — resource doesn't exist (also use for 403 on sensitive resources)
409 Conflict      — duplicate creation (unique constraint violation)
422 Unprocessable — validation failed (correct syntax, invalid data)
429 Too Many      — rate limit exceeded
500 Server Error  — unexpected server failure
503 Unavailable   — maintenance, overload
```

### Error Response Shape (consistent across ALL endpoints)
```json
// 4xx errors
{
  "error": "Resource not found",
  "code": "NOT_FOUND"
}

// 422 validation errors
{
  "errors": [
    { "field": "email", "message": "Invalid email format" },
    { "field": "password", "message": "Password must be at least 8 characters" }
  ]
}

// 500 errors (never expose internals)
{
  "error": "Internal server error",
  "request_id": "req_abc123"   // for log correlation only
}
```

### Pagination — Cursor-Based (preferred for large/dynamic datasets)
```json
// Request: GET /api/v1/posts?limit=20&cursor=eyJpZCI6MTAwfQ
// Response
{
  "data": [...],
  "pagination": {
    "limit": 20,
    "next_cursor": "eyJpZCI6MTIwfQ",   // null when no more pages
    "has_next_page": true
  }
}
```

```typescript
// Cursor implementation
async function getPostsCursor(cursor?: string, limit = 20) {
    const decodedCursor = cursor ? JSON.parse(Buffer.from(cursor, 'base64').toString()) : null;
    
    const posts = await db.post.findMany({
        take: limit + 1,    // fetch one extra to detect next page
        where: decodedCursor ? { id: { gt: decodedCursor.id } } : undefined,
        orderBy: { id: 'asc' },
    });

    const hasNextPage = posts.length > limit;
    const data = hasNextPage ? posts.slice(0, -1) : posts;
    const nextCursor = hasNextPage
        ? Buffer.from(JSON.stringify({ id: data[data.length - 1].id })).toString('base64')
        : null;

    return { data, pagination: { limit, next_cursor: nextCursor, has_next_page: hasNextPage } };
}
```

## Versioning Strategy

| Strategy | Example | When |
|---|---|---|
| URL versioning | `/api/v1/users` | Default — explicit, easy to debug |
| Header versioning | `Accept-Version: 1` | API consumed by single client team |
| Query param | `/api/users?version=1` | Only for public APIs with backward compat |

**Breaking vs non-breaking changes:**
```
Non-breaking (safe to ship):
  - Adding new optional fields to response
  - Adding new optional query parameters
  - Adding new endpoints
  - Adding new values to enums (careful)

Breaking (require version bump):
  - Removing fields from response
  - Renaming fields
  - Changing field types
  - Changing required status of fields
  - Changing status codes
  - Removing endpoints
```

## API Scorecard

Rate each dimension (0-10):

| Dimension | Weight | What to Check |
|---|---|---|
| **Consistency** | 30% | Same naming across all endpoints, same response shape, same error format |
| **Security** | 20% | Auth on all endpoints, ownership checks, rate limiting |
| **Documentation** | 20% | Every endpoint described, all params documented, examples provided |
| **Usability** | 15% | Can a developer understand the API without reading the source? |
| **Performance** | 15% | Pagination on list endpoints, no returning full objects when partial works |

Score < 70 → redesign before shipping  
Score 70-85 → ship with documented caveats  
Score > 85 → production-ready  
