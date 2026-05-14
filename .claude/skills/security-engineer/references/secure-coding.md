# Secure Coding Patterns

## Injection Prevention

### SQL Injection
```typescript
// ❌ WRONG — string interpolation = injection
const query = `SELECT * FROM users WHERE email = '${email}'`;

// ✅ CORRECT — parameterized query
const user = await db.query('SELECT * FROM users WHERE email = $1', [email]);

// With Prisma (auto-parameterized)
const user = await prisma.user.findUnique({ where: { email } });

// Raw SQL with Prisma (still safe if using Prisma.sql)
const users = await prisma.$queryRaw`SELECT * FROM users WHERE email = ${email}`;
```

### Command Injection
```typescript
// ❌ WRONG
exec(`convert ${userFilename} output.pdf`);

// ✅ CORRECT — use array form (no shell interpretation)
execFile('convert', [userFilename, 'output.pdf']);

// Or validate against allowlist
const ALLOWED_FORMATS = ['jpg', 'png', 'gif'] as const;
if (!ALLOWED_FORMATS.includes(fileExt)) throw new Error('Invalid format');
```

## Authentication & Sessions

### JWT Security
```typescript
import jwt from 'jsonwebtoken';

// ❌ WRONG — weak algorithm, short secret, no expiry
const token = jwt.sign({ userId }, 'secret', { algorithm: 'HS256' });

// ✅ CORRECT
const ACCESS_TOKEN_EXPIRY = '15m';   // short-lived
const REFRESH_TOKEN_EXPIRY = '7d';

function issueAccessToken(userId: string): string {
    return jwt.sign(
        { sub: userId, type: 'access' },
        process.env.JWT_SECRET!,     // min 256-bit secret
        { expiresIn: ACCESS_TOKEN_EXPIRY, algorithm: 'HS256' }
    );
}

function verifyToken(token: string): { sub: string; type: string } {
    try {
        return jwt.verify(token, process.env.JWT_SECRET!) as any;
    } catch (err) {
        throw new UnauthorizedError('Invalid or expired token');
    }
}

// Never trust role from token client-side — recheck DB
async function requireRole(userId: string, role: string) {
    const user = await db.user.findUnique({ where: { id: userId } });
    if (user?.role !== role) throw new ForbiddenError();
}
```

### Password Hashing
```typescript
import bcrypt from 'bcrypt';
const SALT_ROUNDS = 12;  // 10 minimum, 12 recommended (balance security/speed)

async function hashPassword(password: string): Promise<string> {
    return bcrypt.hash(password, SALT_ROUNDS);
}

async function verifyPassword(password: string, hash: string): Promise<boolean> {
    return bcrypt.compare(password, hash);
}

// Never: md5, sha1, sha256 for passwords — use bcrypt/argon2/scrypt only
```

### Rate Limiting
```typescript
import rateLimit from 'express-rate-limit';

// Auth endpoints — strict
const authLimiter = rateLimit({
    windowMs: 15 * 60 * 1000,   // 15 min
    max: 5,                       // 5 attempts per window
    skipSuccessfulRequests: true, // don't count successful logins
    message: { error: 'Too many login attempts, try again in 15 minutes' },
});

// API endpoints — general
const apiLimiter = rateLimit({
    windowMs: 60 * 1000,  // 1 min
    max: 100,
});

app.use('/api/auth', authLimiter);
app.use('/api', apiLimiter);
```

## Access Control (IDOR Prevention)

```typescript
// ❌ WRONG — trusts user-supplied ID
app.get('/api/documents/:id', async (req, res) => {
    const doc = await db.document.findUnique({ where: { id: req.params.id } });
    res.json(doc);
});

// ✅ CORRECT — always scope to authenticated user
app.get('/api/documents/:id', authenticate, async (req, res) => {
    const doc = await db.document.findFirst({
        where: {
            id: req.params.id,
            userId: req.user.id,   // MUST include ownership check
        },
    });
    if (!doc) throw new NotFoundError();  // same error for not-found and not-authorized
    res.json(doc);
});
```

## Sensitive Data Protection

```typescript
// Mask PII in logs
function maskEmail(email: string): string {
    const [local, domain] = email.split('@');
    return `${local[0]}***@${domain}`;
}

logger.info({ user: maskEmail(user.email), action: 'login' }, 'Auth event');

// Never log: passwords, tokens, credit cards, SSN, full emails in production
// Check: search logs for /bearer /password /token /secret — should return 0 matches

// Encrypt sensitive fields at rest
import { createCipheriv, createDecipheriv, randomBytes } from 'crypto';

function encrypt(text: string): string {
    const iv = randomBytes(16);
    const cipher = createCipheriv('aes-256-gcm', Buffer.from(ENCRYPTION_KEY, 'hex'), iv);
    const encrypted = Buffer.concat([cipher.update(text, 'utf8'), cipher.final()]);
    const tag = cipher.getAuthTag();
    return `${iv.toString('hex')}:${encrypted.toString('hex')}:${tag.toString('hex')}`;
}
```

## Security Headers (Express)

```typescript
import helmet from 'helmet';

app.use(helmet({
    contentSecurityPolicy: {
        directives: {
            defaultSrc: ["'self'"],
            scriptSrc: ["'self'"],      // no inline scripts
            styleSrc: ["'self'", "'unsafe-inline'"],
            imgSrc: ["'self'", 'data:', 'https:'],
            connectSrc: ["'self'"],
        },
    },
    hsts: { maxAge: 31536000, includeSubDomains: true },
}));

// CORS — explicit allowlist
app.use(cors({
    origin: process.env.ALLOWED_ORIGINS?.split(',') ?? [],
    credentials: true,
}));
```

## OWASP Top 10 Quick Reference

| # | Vulnerability | Key Defense |
|---|---|---|
| A01 | Broken Access Control | Scope every query to authenticated user; deny by default |
| A02 | Cryptographic Failures | bcrypt passwords; TLS everywhere; encrypt sensitive fields |
| A03 | Injection | Parameterized queries; ORM; input validation |
| A04 | Insecure Design | Threat model before building; principle of least privilege |
| A05 | Security Misconfiguration | `helmet`; CORS allowlist; disable debug in prod |
| A06 | Vulnerable Components | `npm audit`; Dependabot/Renovate; pin versions |
| A07 | Auth/Session Failures | Short JWT expiry; rate limit auth; bcrypt |
| A08 | Integrity Failures | Verify external content; signed packages; SRI hashes |
| A09 | Logging Failures | Structured logs; mask PII; alert on anomalies |
| A10 | SSRF | Validate/allowlist URLs; block private IP ranges |
