# Deployment

AugMed supports multiple deployment options, from one-click cloud platforms to full AWS infrastructure.

## Deployment Options

| Option | Monthly Cost | Technical Skill | Best For |
|--------|-------------|----------------|----------|
| [Railway](#railway-one-click) | ~$5-8 | None | Quick demos, small studies |
| [Render](#render-blueprint) | ~$21 | Low | Small-medium studies |
| [Docker Compose](#docker-compose-self-hosted) | ~$6-12 (VPS) | Medium | Institutional servers, privacy requirements |
| [AWS (Terraform)](#aws-advanced) | ~$30-50 | High | Large-scale production, existing AWS infrastructure |

---

## Railway (One-Click)

The fastest way to deploy. See the full guide: [One-Click Deploy](../getting-started/one-click-deploy.md).

<!-- TODO: Replace with actual Railway template URL -->
[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/template/TEMPLATE_ID)

Railway deploys all four services (API, Frontend, RL, PostgreSQL) from a template. Environment variables auto-configure. Demo data seeds on first boot.

---

## Render (Blueprint)

This repository includes a `render.yaml` Blueprint that defines all services.

1. Log in to [Render](https://render.com)
2. Click "New" → "Blueprint"
3. Connect the `augmed-api-v2` repository
4. Render will detect `render.yaml` and configure all services automatically

The Blueprint creates: API (web service), Frontend (web service), RL service (web service), and PostgreSQL database. Secrets are auto-generated.

---

## Docker Compose (Self-Hosted)

See the full guide: [Self-Hosted Deploy](../getting-started/self-hosted-deploy.md).

```bash
git clone https://github.com/DHEPLab/augmed-api-v2.git
git clone https://github.com/DHEPLab/augmed-app-v2.git
git clone https://github.com/DHEPLab/augmed-rl.git
cd augmed-api-v2
docker compose -f docker-compose.full.yml up --build
```

Access at `http://localhost:8080`. For production VPS deployment, add a reverse proxy (Caddy/nginx) for HTTPS.

---

## AWS (Advanced)

For teams with existing AWS infrastructure or large-scale production needs. This is the original deployment method and remains fully supported.

### Infrastructure Overview

Production infrastructure is managed via Terraform and lives in the [augmed-infra](https://github.com/DHEPLab/augmed-infra) repository. The main components are:

```
Internet
    │
    ▼
Route 53 (DNS)
    │
    ▼
Application Load Balancer (ALB)
    │
    ├── /api/* ──► ECS Fargate Service (Flask API)
    │                      │
    │                      ▼
    │               RDS PostgreSQL
    │
    └── /* ──────► [Frontend hosting - separate]
```

### AWS Services Used

| Service | Purpose |
|---------|---------|
| ECS Fargate | Runs the containerized Flask API — no servers to manage |
| ECR | Container registry — Docker images are pushed here and pulled by ECS |
| RDS PostgreSQL | Managed PostgreSQL database |
| ALB | Application Load Balancer — routes traffic, handles SSL termination |
| Route 53 | DNS — maps `augmed1.dhep.org` to the ALB |
| S3 | Static assets and deployment artifacts |
| CloudWatch | Logs and monitoring |

## CI/CD Pipeline

GitHub Actions handles building and deploying. The workflow file is at `.github/workflows/` in the repository.

**On push to main:**
1. Run tests (`pytest`)
2. Build Docker image
3. Push image to ECR with the git commit SHA as the tag
4. Update the ECS service to use the new image (rolling deployment)

**Manual deployment:**

```bash
# Build and push image manually (requires AWS CLI configured)
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com

docker build -t augmed-api .
docker tag augmed-api:latest <account>.dkr.ecr.us-east-1.amazonaws.com/augmed-api:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/augmed-api:latest

# Force ECS to pick up the new image
aws ecs update-service \
  --cluster augmed-cluster \
  --service augmed-api-service \
  --force-new-deployment
```

## Terraform Setup

See the [augmed-infra](https://github.com/DHEPLab/augmed-infra) repository for full Terraform configuration.

Quick reference for applying infrastructure changes:

```bash
cd augmed-infra
terraform init
terraform plan    # Preview changes
terraform apply   # Apply changes
```

!!! warning
    Terraform changes to RDS (database) can cause downtime or data loss. Always review the plan carefully before applying, especially for database-related resources.

## Environment Variables

The Flask API reads configuration from environment variables. In production, these are set in the ECS task definition.

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string: `postgresql://user:pass@host:5432/dbname` |
| `JWT_SECRET_KEY` | Yes | Secret key for signing JWT tokens — must be strong and kept private |
| `JWT_ACCESS_TOKEN_EXPIRES` | No | Access token lifetime in seconds (default: 259200 = 3 days) |
| `JWT_REFRESH_TOKEN_EXPIRES` | No | Refresh token lifetime in seconds (default: 259200 = 3 days) |
| `POSTGRES_USER` | Yes | Database username (used by export scripts) |
| `POSTGRES_PASSWORD` | Yes | Database password (used by export scripts) |
| `POSTGRES_DB` | Yes | Database name |
| `POSTGRES_HOST` | Yes | Database host (used by export scripts) |
| `POSTGRES_PORT` | No | Database port (default: 5432) |
| `EXPORT_API_KEY` | Yes | API key for the export endpoint (used by RL service for service-to-service auth) |
| `CORS_ORIGINS` | No | Comma-separated allowed origins, or `*` for all (default: `*`) |
| `SEED_DEMO_DATA` | No | Set to `true` to seed demo data on first boot (default: `false`) |
| `GUNICORN_WORKERS` | No | Number of gunicorn worker processes (default: 2) |

### Updating Secrets

In production, update secrets through the AWS console (ECS task definition) or via the AWS CLI:

```bash
aws ssm put-parameter \
  --name "/augmed/production/jwt-secret" \
  --value "new-secret-value" \
  --type SecureString \
  --overwrite
```

Then update the ECS task definition to reference the new parameter version and redeploy.

## Docker Configuration

The `Dockerfile` at the project root builds the API image. The container uses `entrypoint.sh` which runs database migrations, optionally seeds demo data, and starts gunicorn (production WSGI server).

```dockerfile
# Key build steps (abbreviated — see actual Dockerfile for full content)
FROM python:3.11-slim
WORKDIR /usr/src/app
COPY Pipfile Pipfile.lock ./
RUN pip install pipenv && pipenv install --deploy --ignore-pipfile
COPY . .
CMD ["/usr/src/app/entrypoint.sh"]
```

Build locally:

```bash
docker build -t augmed-api:local .
docker run -p 5000:5000 --env-file .env augmed-api:local
```

## Database Migrations

Alembic (via Flask-Migrate) manages database schema changes. Migrations run automatically when the API starts (`upgrade()` is called in `create_app()`).

**Creating a new migration:**

```bash
cd src
flask db migrate -m "Add new column to user table"
# Review the generated script in src/migrations/versions/
flask db upgrade
```

!!! important
    Always review generated migration scripts before running `upgrade`. Auto-generated scripts sometimes include `drop_table` or other destructive operations that are not intended.

**Rolling back:**

```bash
flask db downgrade
```

## Health Check

The ALB uses the health check endpoint to determine if instances are healthy:

```
GET /api/healthcheck
```

Expected response:

```json
{"status": "OK", "message": "Service is up and running."}
```

HTTP 200 = healthy. The ALB will route traffic away from unhealthy instances automatically.

## Monitoring

**CloudWatch Logs** — Container logs (stdout/stderr from Flask) stream to CloudWatch. Access through the AWS console: CloudWatch → Log Groups → `/ecs/augmed-api`.

**ECS Service Events** — Deployment events and instance health changes appear in: ECS → Clusters → augmed-cluster → Services → augmed-api-service → Events tab.

## Related Documentation

- [Troubleshooting](troubleshooting.md) — Common issues and solutions
- [Database](database.md) — Schema and migration details
- [Configuration](configuration.md) — System and answer config setup
