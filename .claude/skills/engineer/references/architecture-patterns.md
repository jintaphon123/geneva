# Architecture Patterns

## Pattern Selection Guide

| Team Size | Starting Point | When to Evolve |
|---|---|---|
| 1-3 devs | Modular Monolith | When a module needs 10× different scaling |
| 4-10 devs | Modular Monolith or SOA | When teams need independent deployment |
| 10+ devs | Consider Microservices | When domain boundaries are well-understood |

**Default:** Modular Monolith. Extract services only when you have a concrete reason, not a hypothetical one.

## Modular Monolith Structure

```
src/
├── modules/
│   ├── users/
│   │   ├── users.controller.ts
│   │   ├── users.service.ts
│   │   ├── users.repository.ts
│   │   └── users.types.ts
│   ├── orders/
│   └── payments/
├── shared/
│   ├── database/
│   ├── auth/
│   ├── errors/
│   └── logger/
└── app.ts
```

**Key rule:** Modules communicate through their public API only — never access another module's internal files directly. This is the migration path to microservices.

## Clean Architecture (for complex domains)

```
Presentation (Controllers/Routes)
    ↓ calls
Application (Use Cases / Services)
    ↓ calls
Domain (Entities, Business Rules)
    ↓ calls (through interfaces)
Infrastructure (Database, APIs, File System)
```

**Dependency rule:** Dependencies only point inward. Domain has zero external dependencies. Infrastructure implements interfaces defined by the domain.

## CQRS (Command Query Responsibility Segregation)

Use when: read/write ratio is very uneven (e.g., 100:1 reads to writes).

```typescript
// Command (write)
class CreateOrderCommand {
  constructor(
    public readonly userId: string,
    public readonly items: OrderItem[]
  ) {}
}

// Query (read — optimized separately)
class GetUserOrdersQuery {
  constructor(public readonly userId: string) {}
}
```

## Event-Driven Patterns

```typescript
// Domain events — decouple modules
class OrderCreatedEvent {
  constructor(
    public readonly orderId: string,
    public readonly userId: string,
    public readonly timestamp: Date
  ) {}
}

// Handler in another module
class EmailNotificationHandler {
  async handle(event: OrderCreatedEvent) {
    await this.emailService.send(event.userId, 'Order confirmed');
  }
}
```

## ADR Template (Architecture Decision Record)

```markdown
## ADR-[N]: [Title]
**Date:** YYYY-MM-DD  **Status:** Proposed | Accepted | Superseded

**Context:** [Problem being solved]
**Decision:** [What was decided]
**Rationale:** [Why this option over alternatives]
**Trade-offs:** [What we accept by choosing this]
**Alternatives considered:** [What was rejected and why]
```

## Database Selection Quick Reference

```
Default choice:    PostgreSQL (ACID, complex queries, joins)
Document store:    MongoDB (flexible schema, rapid iteration)
Cache/sessions:    Redis
Time-series:       TimescaleDB (SQL interface on top of Postgres)
Serverless/AWS:    DynamoDB (auto-scaling, but NoSQL tradeoffs)

Scale thresholds:
  <1M rows         → PostgreSQL, single instance
  1M–100M rows     → PostgreSQL + read replicas
  >100M rows       → CockroachDB, Cassandra, or DynamoDB
```
