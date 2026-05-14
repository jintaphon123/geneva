# Backend Patterns

## API Design

### REST Conventions
```
GET    /users          → list
GET    /users/:id      → single
POST   /users          → create
PUT    /users/:id      → full replace
PATCH  /users/:id      → partial update
DELETE /users/:id      → delete

Nested: GET /users/:id/orders → user's orders
Action: POST /users/:id/activate → non-CRUD action
```

### Versioning
```
# URL versioning (most common)
/api/v1/users
/api/v2/users

# Header versioning
Accept: application/vnd.api+json;version=2
```

### Pagination
```json
{
  "data": [...],
  "pagination": {
    "page": 2,
    "per_page": 20,
    "total": 150,
    "next_cursor": "eyJpZCI6MTAwfQ"  // cursor preferred for large datasets
  }
}
```

## Authentication Patterns

### JWT (stateless)
```typescript
// Generate
const token = jwt.sign(
  { userId: user.id, role: user.role },
  process.env.JWT_SECRET!,
  { expiresIn: '1h', algorithm: 'RS256' }
);

// Verify middleware
const authenticate = async (req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(401).json({ error: 'UNAUTHORIZED' });
  try {
    req.user = jwt.verify(token, process.env.JWT_PUBLIC_KEY!);
    next();
  } catch {
    return res.status(401).json({ error: 'INVALID_TOKEN' });
  }
};
```

### Refresh Token Pattern
```
Access token: 15-60 min expiry (in memory / Authorization header)
Refresh token: 7-30 days (httpOnly cookie, never in localStorage)
Rotation: issue new refresh token on each use
```

## Database Patterns

### Repository Pattern
```typescript
// Abstract away the data layer
interface UserRepository {
  findById(id: string): Promise<User | null>;
  findByEmail(email: string): Promise<User | null>;
  create(data: CreateUserDto): Promise<User>;
  update(id: string, data: UpdateUserDto): Promise<User>;
}

// Implementation (Prisma)
class PrismaUserRepository implements UserRepository {
  async findById(id: string) {
    return prisma.user.findUnique({ where: { id } });
  }
}
```

### Transaction Pattern
```typescript
// Prisma transaction — atomic operations
const result = await prisma.$transaction(async (tx) => {
  const order = await tx.order.create({ data: orderData });
  await tx.inventory.update({
    where: { id: orderData.productId },
    data: { quantity: { decrement: orderData.quantity } }
  });
  return order;
});
```

## Error Handling

### Structured error responses
```typescript
class AppError extends Error {
  constructor(
    public code: string,
    public message: string,
    public statusCode: number,
    public details?: unknown
  ) {
    super(message);
  }
}

// Global error handler (Express)
app.use((err, req, res, next) => {
  if (err instanceof AppError) {
    return res.status(err.statusCode).json({
      error: { code: err.code, message: err.message, details: err.details }
    });
  }
  // Unexpected error — don't leak internals
  res.status(500).json({ error: { code: 'INTERNAL_ERROR', message: 'Something went wrong' } });
});
```

## Caching Strategy

```
L1 (in-process): node-cache / Map — sub-millisecond, process-local
L2 (distributed): Redis — milliseconds, shared across instances
L3 (CDN): Cloudflare / Fastly — seconds to minutes, edge

Cache patterns:
- Cache-aside: app reads cache, on miss reads DB and populates cache
- Write-through: write to cache and DB simultaneously
- TTL strategy: aggressive (1min) for volatile data, long (1hr+) for static
```
