# CI/CD Patterns

## GitHub Actions — Standard Node.js Pipeline

```yaml
# .github/workflows/ci.yml
name: CI/CD
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true   # cancel stale runs on same branch

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: 'npm' }
      - run: npm ci
      - run: npm run lint
      - run: npm run typecheck

  test:
    needs: lint
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports: ['5432:5432']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: 'npm' }
      - run: npm ci
      - run: npm test -- --coverage
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/test_db
      - uses: codecov/codecov-action@v4

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: 'npm' }
      - run: npm ci
      - run: npm run build
      - uses: actions/upload-artifact@v4
        with: { name: build-output, path: .next/ }

  deploy-staging:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with: { name: build-output, path: .next/ }
      - run: ./scripts/deploy.sh staging
        env:
          DEPLOY_KEY: ${{ secrets.STAGING_DEPLOY_KEY }}

  deploy-prod:
    needs: deploy-staging
    if: startsWith(github.ref, 'refs/tags/v')   # tag-based release
    runs-on: ubuntu-latest
    environment: production     # requires manual approval in GitHub
    steps:
      - run: ./scripts/deploy.sh production
        env:
          DEPLOY_KEY: ${{ secrets.PROD_DEPLOY_KEY }}
```

## Caching Strategies

```yaml
# Node.js — cache node_modules via package-lock.json hash
- uses: actions/setup-node@v4
  with:
    node-version: 20
    cache: 'npm'   # built-in cache by setup-node

# Python — pip cache
- uses: actions/setup-python@v5
  with:
    python-version: '3.12'
    cache: 'pip'

# Docker layer cache (buildx)
- uses: docker/setup-buildx-action@v3
- uses: actions/cache@v4
  with:
    path: /tmp/.buildx-cache
    key: ${{ runner.os }}-buildx-${{ github.sha }}
    restore-keys: ${{ runner.os }}-buildx-
- uses: docker/build-push-action@v5
  with:
    cache-from: type=local,src=/tmp/.buildx-cache
    cache-to: type=local,dest=/tmp/.buildx-cache-new,mode=max
```

## Secrets — Rules

```yaml
# ✅ Correct — env var from GitHub Secrets
env:
  DATABASE_URL: ${{ secrets.DATABASE_URL }}
  API_KEY: ${{ secrets.API_KEY }}

# ❌ Never: hardcoded values
env:
  DATABASE_URL: postgresql://user:password@host/db   # WRONG

# ❌ Never: echo secrets (shows in logs)
- run: echo "KEY=${{ secrets.API_KEY }}"   # WRONG — prints to log

# Mask custom values that aren't secrets (added at job level)
- run: echo "::add-mask::$COMPUTED_VALUE"
```

## Parallel Test Matrix

```yaml
test:
  strategy:
    matrix:
      node: [18, 20, 22]
      os: [ubuntu-latest, windows-latest]
  runs-on: ${{ matrix.os }}
  steps:
    - uses: actions/setup-node@v4
      with: { node-version: ${{ matrix.node }} }
    - run: npm test

# Shard tests for faster CI (split into 4 shards)
test:
  strategy:
    matrix:
      shard: [1, 2, 3, 4]
  steps:
    - run: npx jest --shard=${{ matrix.shard }}/4
```

## Docker Build + Push

```yaml
docker:
  steps:
    - uses: docker/login-action@v3
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - uses: docker/metadata-action@v5
      id: meta
      with:
        images: ghcr.io/${{ github.repository }}
        tags: |
          type=sha,prefix=sha-
          type=semver,pattern={{version}}
          type=raw,value=latest,enable=${{ github.ref == 'refs/heads/main' }}

    - uses: docker/build-push-action@v5
      with:
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
```
