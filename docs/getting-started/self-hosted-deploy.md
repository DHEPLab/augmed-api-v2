# Self-Hosted Deploy (Docker Compose)

Run the full AugMed platform on your own machine or server using Docker Compose.

## Prerequisites

- **Docker Desktop** (version 4.x or later) — [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/)
- **Git**
- **~2 GB disk space** for Docker images

## Step 1: Clone the Repositories

All three repositories must be cloned into the same parent directory:

```bash
mkdir augmed && cd augmed
git clone https://github.com/DHEPLab/augmed-api-v2.git
git clone https://github.com/DHEPLab/augmed-app-v2.git
git clone https://github.com/DHEPLab/augmed-rl.git
```

Your directory should look like:

```
augmed/
├── augmed-api-v2/
├── augmed-app-v2/
└── augmed-rl/
```

## Step 2: Start the Platform

```bash
cd augmed-api-v2
docker compose -f docker-compose.full.yml up --build
```

The first build takes 5-10 minutes. Subsequent starts are much faster.

You'll see logs from all four services. When you see `Starting gunicorn...` from the API and the nginx startup message from the app, the platform is ready.

## Step 3: Access AugMed

Open your browser to **http://localhost:8080**.

Log in with the demo credentials:

| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@demo.augmed.org` | `augmed-demo` |
| Researcher | `researcher@demo.augmed.org` | `augmed-demo` |

## Step 4: Review a Case

Log in as the researcher. You'll see assigned cases. Click one to review clinical data and answer the questionnaire.

## Configuration

### Environment Variables

Create a `.env` file in `augmed-api-v2/` to override defaults:

```env
POSTGRES_PASSWORD=your-secure-password
JWT_SECRET_KEY=your-secret-key
EXPORT_API_KEY=your-api-key
```

If no `.env` file is present, development defaults are used (fine for local testing, not for production).

### Disable Demo Data

To start with an empty database (for loading your own data):

```env
SEED_DEMO_DATA=false
```

## Deploying to a Server

To deploy on a VPS (e.g., DigitalOcean, Linode, Hetzner):

1. Install Docker on the server
2. Clone the repositories as above
3. Create a `.env` file with production secrets
4. Set `SEED_DEMO_DATA=false` if loading real data
5. Run `docker compose -f docker-compose.full.yml up -d` (the `-d` flag runs in the background)

Estimated cost: **$6-12/month** for a small VPS.

### HTTPS

For production use, put a reverse proxy (nginx, Caddy, or Traefik) in front of the platform to handle SSL. The simplest option is Caddy with automatic HTTPS:

```
your-domain.com {
    reverse_proxy localhost:8080
}
```

## Stopping and Restarting

```bash
# Stop
docker compose -f docker-compose.full.yml down

# Stop and delete data
docker compose -f docker-compose.full.yml down -v

# Restart
docker compose -f docker-compose.full.yml up -d
```

## Troubleshooting

**Port conflict:** If port 8080 or 5000 is already in use, edit `docker-compose.full.yml` to change the host port (e.g., `"3000:8080"`).

**Database connection error:** Make sure the `db` service is healthy before the API starts. The compose file has a health check, but if the database is slow to initialize, try `docker compose -f docker-compose.full.yml up -d db` first, wait a few seconds, then bring up the rest.

**Out of memory:** The full stack uses ~1 GB of RAM. If your machine is constrained, reduce gunicorn workers: set `GUNICORN_WORKERS=1` in the environment.
