# Infrastructure Patterns

## Docker — Best Practices

### Multi-Stage Dockerfile (Node.js)
```dockerfile
# Stage 1: Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production=false
COPY . .
RUN npm run build

# Stage 2: Runtime (minimal)
FROM node:20-alpine AS runner
WORKDIR /app

# Non-root user — security best practice
RUN addgroup -g 1001 -S nodejs && adduser -S nextjs -u 1001

COPY --from=builder --chown=nextjs:nodejs /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./

USER nextjs
EXPOSE 3000
ENV NODE_ENV=production

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -qO- http://localhost:3000/api/health || exit 1

CMD ["node_modules/.bin/next", "start"]
```

### docker-compose (Local Dev Stack)
```yaml
# docker-compose.yml
services:
  app:
    build: .
    ports: ['3000:3000']
    environment:
      DATABASE_URL: postgresql://user:pass@db:5432/myapp
      REDIS_URL: redis://cache:6379
    depends_on:
      db:
        condition: service_healthy
      cache:
        condition: service_started
    volumes:
      - .:/app
      - /app/node_modules   # preserve node_modules from image

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ['CMD-SHELL', 'pg_isready -U user -d myapp']
      interval: 5s
      timeout: 5s
      retries: 5
    ports: ['5432:5432']

  cache:
    image: redis:7-alpine
    ports: ['6379:6379']

  mail:
    image: mailhog/mailhog
    ports:
      - '1025:1025'   # SMTP
      - '8025:8025'   # Web UI

volumes:
  postgres_data:
```

### .dockerignore
```
node_modules
.next
.git
.env*
*.log
coverage
```

## Helm Chart Structure

```
my-app/
├── Chart.yaml           # chart metadata + version
├── values.yaml          # default values (override per env)
├── values-staging.yaml
├── values-prod.yaml
└── templates/
    ├── deployment.yaml
    ├── service.yaml
    ├── ingress.yaml
    ├── configmap.yaml
    ├── secret.yaml
    └── hpa.yaml         # horizontal pod autoscaler
```

```yaml
# values.yaml (defaults)
replicaCount: 1
image:
  repository: ghcr.io/org/myapp
  tag: latest
  pullPolicy: IfNotPresent
service:
  type: ClusterIP
  port: 3000
resources:
  requests: { cpu: 100m, memory: 128Mi }
  limits: { cpu: 500m, memory: 512Mi }
autoscaling:
  enabled: false
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
env: []   # override per environment

# values-prod.yaml (overrides)
replicaCount: 3
autoscaling:
  enabled: true
resources:
  requests: { cpu: 250m, memory: 256Mi }
  limits: { cpu: 1000m, memory: 1Gi }
```

```bash
# Validate before apply
helm template my-app ./my-app -f values-prod.yaml

# Deploy
helm upgrade --install my-app ./my-app \
  -f values.yaml -f values-prod.yaml \
  --namespace production \
  --create-namespace
```

## Terraform — Module Structure

```
infra/
├── modules/
│   ├── vpc/              # reusable VPC module
│   ├── rds/              # reusable RDS module
│   ├── ecs-service/      # reusable ECS service module
│   └── redis/
├── environments/
│   ├── staging/
│   │   ├── main.tf       # uses modules
│   │   ├── variables.tf
│   │   └── terraform.tfvars
│   └── prod/
│       ├── main.tf
│       ├── variables.tf
│       └── terraform.tfvars
└── backend.tf            # remote state config
```

```hcl
# backend.tf — remote state (S3 + DynamoDB lock)
terraform {
  backend "s3" {
    bucket         = "my-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "ap-southeast-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"   # prevents concurrent applies
  }
}

# environments/staging/main.tf
module "vpc" {
  source     = "../../modules/vpc"
  cidr_block = "10.0.0.0/16"
  env        = "staging"
}

module "rds" {
  source          = "../../modules/rds"
  vpc_id          = module.vpc.id
  instance_class  = "db.t3.micro"   # smaller for staging
  db_name         = "myapp_staging"
}
```

```bash
# Workflow
cd environments/staging
terraform init
terraform plan -out=tfplan      # always save plan
terraform apply tfplan           # apply the exact plan reviewed

# Never: terraform apply (without plan) or terraform destroy in prod
```

## Secrets Management

```bash
# GitHub Actions: store in repo/org secrets
# Local dev: .env file (gitignored)
# Production: AWS Secrets Manager / GCP Secret Manager / Doppler

# Doppler (recommended for solo projects)
doppler setup                   # link project
doppler run -- npm start        # inject secrets as env vars
doppler run -- docker-compose up
```
