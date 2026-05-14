---
name: devops-engineer
description: >
  CI/CD pipeline design, containerization (Docker/Helm/K8s), infrastructure as code (Terraform),
  observability (logging/metrics/tracing/SLO), and performance profiling for production systems.

  Auto-invoke when Bond asks: CI/CD pipeline, GitHub Actions, set up Docker, Dockerfile, docker-compose,
  Kubernetes, Helm chart, Terraform, infrastructure as code, deploy to production, deployment pipeline,
  observability, logging setup, metrics, tracing, SLO, SLI, alert, performance profiling, slow query,
  flame graph, memory leak, CPU spike, container, containerize this app, staging environment, secrets management.
---

# DevOps Engineer

Five modes: **CI/CD** (pipelines), **Container** (Docker/Helm/K8s), **IaC** (Terraform), **Observe** (logging/metrics/tracing/SLO), **Profile** (performance diagnosis).

Reference files:
- `references/ci-cd-patterns.md` — GitHub Actions, pipeline stages, caching, secrets, multi-env
- `references/infrastructure-patterns.md` — Docker best practices, Helm chart structure, Terraform modules
- `references/observability.md` — structured logging, metrics, tracing, SLO/SLI, alerting

---

## Mode Detection

| Input | Mode |
|---|---|
| "CI/CD", "pipeline", "GitHub Actions", "CircleCI", "build + deploy" | **CI/CD** |
| "Docker", "Dockerfile", "docker-compose", "container", "Helm", "K8s" | **Container** |
| "Terraform", "IaC", "infrastructure", "provision", "cloud resource" | **IaC** |
| "logging", "metrics", "tracing", "SLO", "SLI", "alert", "observability" | **Observe** |
| "slow", "flame graph", "CPU spike", "memory leak", "profile", "perf" | **Profile** |

---

## Mode 1 — CI/CD

Read `references/ci-cd-patterns.md` fully before executing.

**Default stack:** GitHub Actions (use unless other CI specified)

**Standard pipeline stages:**
1. `lint` — ESLint/prettier/mypy (fast, run on every push)
2. `test` — unit + integration (parallelized by module)
3. `build` — compile/bundle with layer caching
4. `security-scan` — npm audit / snyk / trivy (non-blocking on feature branches)
5. `deploy-staging` — auto on `main` merge
6. `deploy-prod` — manual approval gate or tag-based

**Rules:**
- Cache dependencies: `node_modules`, `.gradle`, pip venv → 60-80% faster
- Fail fast: lint before tests (catches formatting before spending test time)
- Secrets via env vars only — never hardcode in workflow files
- Use `concurrency` to cancel stale runs on same branch

---

## Mode 2 — Container

Read `references/infrastructure-patterns.md` (Docker section) fully before executing.

**Dockerfile rules:**
- Multi-stage build (builder → runner) — separate build deps from runtime
- Non-root user in runtime stage
- Layer order: deps first, app code last (maximize cache hits)
- Health check in every production Dockerfile

**docker-compose dev pattern:** app + db + redis + mail (mailhog) — all local, isolated, one command start

**Helm:** create chart → values.yaml for per-env config → `helm template` to validate locally before apply

---

## Mode 3 — IaC (Terraform)

Read `references/infrastructure-patterns.md` (Terraform section) fully before executing.

**Structure:** `modules/` (reusable) + `environments/staging/` + `environments/prod/`

**Workflow:** `terraform plan` → review → `terraform apply` (never apply without plan review)

**State:** remote backend (S3/GCS) with locking — never local state for shared infra

---

## Mode 4 — Observe

Read `references/observability.md` fully before executing.

**Three pillars:**
- **Logs** — structured JSON (never free-text), correlation IDs across services
- **Metrics** — RED (Rate, Errors, Duration) per service + USE (Utilization, Saturation, Errors) per resource
- **Traces** — OpenTelemetry, propagate trace context through all service boundaries

**SLO design:** define SLI (what you measure) → set SLO (target %) → calculate error budget → alert when budget burning fast

---

## Mode 5 — Profile

Read `references/observability.md` (Performance section) fully before executing.

**Diagnosis sequence:**
1. Identify: is this CPU, memory, I/O, or network?
2. CPU: generate flame graph (`py-spy`, `0x`)
3. Memory: heap dump → look for retained objects
4. I/O: check for N+1 queries (see database-architect skill), slow disk writes
5. Network: trace slow external calls, add timeout + circuit breaker

---

## Global Rules

- Every production deploy must have a rollback plan defined before deploying
- Secrets never in code, git history, or workflow env vars visible in logs
- Staging must be a functional clone of prod (same IaC, different sizing)
- Infrastructure changes: plan → PR review → apply (no manual console edits)
