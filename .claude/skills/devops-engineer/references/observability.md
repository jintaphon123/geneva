# Observability Patterns

## Structured Logging

```typescript
// Use structured JSON — never free-text log strings
import pino from 'pino';

const logger = pino({
    level: process.env.LOG_LEVEL || 'info',
    formatters: {
        level: (label) => ({ level: label }),
    },
    base: { service: 'second-brain-api', version: process.env.APP_VERSION },
});

// ✅ Correct — structured fields
logger.info({ user_id: userId, action: 'login', duration_ms: 142 }, 'User authenticated');
logger.error({ err, request_id: req.id, route: req.path }, 'Request failed');

// ❌ Wrong — free-text
logger.info(`User ${userId} logged in after 142ms`);  // unqueryable

// Correlation ID — pass through all service calls
app.use((req, res, next) => {
    req.id = req.headers['x-request-id'] || crypto.randomUUID();
    req.log = logger.child({ request_id: req.id });
    next();
});
```

**Log levels:**
- `error` — unexpected failures that need investigation
- `warn` — degraded behavior (retry succeeded, rate limit hit, deprecated usage)
- `info` — business events (user created, payment processed)
- `debug` — dev-only (SQL queries, cache hits) — disabled in prod

## RED Metrics (per service)

```typescript
// Rate, Errors, Duration — the three metrics every service needs
import { Counter, Histogram, register } from 'prom-client';

const requestRate = new Counter({
    name: 'http_requests_total',
    help: 'Total HTTP requests',
    labelNames: ['method', 'route', 'status_code'],
});

const requestDuration = new Histogram({
    name: 'http_request_duration_seconds',
    help: 'Request duration in seconds',
    labelNames: ['method', 'route'],
    buckets: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5],
});

// Express middleware
app.use((req, res, next) => {
    const end = requestDuration.startTimer({ method: req.method, route: req.route?.path });
    res.on('finish', () => {
        requestRate.inc({ method: req.method, route: req.route?.path, status_code: res.statusCode });
        end();
    });
    next();
});

// Prometheus endpoint
app.get('/metrics', async (req, res) => {
    res.set('Content-Type', register.contentType);
    res.end(await register.metrics());
});
```

## OpenTelemetry Tracing

```typescript
// Initialize at app start (before imports)
import { NodeSDK } from '@opentelemetry/sdk-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { HttpInstrumentation } from '@opentelemetry/instrumentation-http';
import { PgInstrumentation } from '@opentelemetry/instrumentation-pg';

const sdk = new NodeSDK({
    traceExporter: new OTLPTraceExporter({
        url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT,
    }),
    instrumentations: [
        new HttpInstrumentation(),  // auto-instruments Express
        new PgInstrumentation(),    // auto-instruments pg queries
    ],
    serviceName: 'second-brain-api',
});

sdk.start();

// Manual span for business operations
import { trace, context } from '@opentelemetry/api';

async function processMemory(userId: string, content: string) {
    const tracer = trace.getTracer('memory-service');
    return tracer.startActiveSpan('process-memory', async (span) => {
        span.setAttributes({ 'user.id': userId, 'content.length': content.length });
        try {
            const result = await doWork(content);
            span.setStatus({ code: SpanStatusCode.OK });
            return result;
        } catch (err) {
            span.recordException(err);
            span.setStatus({ code: SpanStatusCode.ERROR });
            throw err;
        } finally {
            span.end();
        }
    });
}
```

## SLO Design

```
SLI (what you measure) → SLO (target %) → Error Budget → Alerting

Example SLOs for Second Brain API:
- API Availability: 99.9% (8.7h downtime/year budget)
- API Latency p99 < 2s: 99%
- LLM Request Success Rate: 98%

Error Budget calculation:
  Budget = (1 - SLO) × period
  99.9% monthly = 0.1% × 43,200 min = 43 min/month
```

```yaml
# Prometheus alerting rule — burn rate alert
# Fires when error budget is burning 6x faster than expected (15m window)
- name: slo_alerts
  rules:
    - alert: HighErrorBudgetBurnRate
      expr: |
        sum(rate(http_requests_total{status_code=~"5.."}[15m]))
        / sum(rate(http_requests_total[15m])) > 6 * (1 - 0.999)
      for: 2m
      labels:
        severity: page
      annotations:
        summary: Error budget burning 6x faster than expected
```

## Performance Profiling

### CPU Profiling (Node.js)
```bash
# py-spy (Python)
pip install py-spy
py-spy record -o flamegraph.svg --pid <PID>

# Node.js — clinic.js
npm install -g clinic
clinic flame -- node server.js
clinic doctor -- node server.js   # CPU + event loop diagnosis

# Quick: 0x (generates flame graph automatically)
npm install -g 0x
0x server.js
```

### Memory Diagnosis
```typescript
// Detect memory leak: heap snapshot comparison
import v8 from 'v8';

// Take snapshots at t=0 and t=5min
// Load both in Chrome DevTools → Memory tab → Compare heaps
// Look for: growing object counts, retained DOM nodes, unclosed closures

// Quick heap stats
setInterval(() => {
    const { heapUsed, heapTotal, external } = process.memoryUsage();
    logger.debug({
        heap_used_mb: Math.round(heapUsed / 1024 / 1024),
        heap_total_mb: Math.round(heapTotal / 1024 / 1024),
    }, 'Memory stats');
}, 60_000);
```

### Benchmark Table (p99 targets by type)

| Operation | Target p99 | Alert Threshold |
|---|---|---|
| API response (simple query) | < 100ms | > 500ms |
| API response (with LLM) | < 3s | > 10s |
| DB query (indexed) | < 10ms | > 100ms |
| DB query (aggregate) | < 200ms | > 1s |
| File upload | < 5s | > 30s |
| Background job | < 30s | > 5min |
