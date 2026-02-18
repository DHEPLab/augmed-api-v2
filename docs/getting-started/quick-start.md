# Quick Start Guide

This guide walks you through setting up a local AugMed instance for development or testing. You will have a running API server, a connected database, and a test user able to review cases.

## Prerequisites

Before you begin, install the following:

- **Docker Desktop** (version 4.x or later) — [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/)
- **Python 3.11** — via `brew install python@3.11` (macOS) or your system package manager
- **Pipenv** — `pip install pipenv`
- **Node.js 18+** and **npm** — for the frontend (if running the full stack)
- **Git**

Verify your installations:

```bash
python3 --version    # Should show 3.11.x
docker --version     # Should show 4.x or later
pipenv --version
```

## Step 1: Clone the Repositories

Clone the backend API:

```bash
git clone https://github.com/DHEPLab/augmed-api-v2.git
cd augmed-api-v2
```

If you also want the frontend:

```bash
git clone https://github.com/DHEPLab/augmed-app.git
```

## Step 2: Configure Environment Variables

In the `augmed-api-v2` directory, create a `.env` file. Use the provided `.env_example` as a template:

```bash
cp .env_example .env
```

Edit `.env` with your local settings:

```env
# Database connection
DATABASE_URL=postgresql://augmed:augmed@localhost:5432/augmed
POSTGRES_USER=augmed
POSTGRES_PASSWORD=augmed
POSTGRES_DB=augmed

# JWT security — change this to a random secret in any non-local environment
JWT_SECRET_KEY=your-local-secret-key-change-me

# Token expiry (in seconds); defaults to 3 days if not set
JWT_ACCESS_TOKEN_EXPIRES=259200
JWT_REFRESH_TOKEN_EXPIRES=259200
```

> **Note:** Never commit `.env` files to version control. The `.gitignore` should already exclude them.

## Step 3: Start the Database

Docker Compose starts a local PostgreSQL instance:

```bash
docker-compose up -d
```

Verify the container is running:

```bash
docker ps
# Should show postgres_container with status "Up"
```

## Step 4: Install Python Dependencies

```bash
pipenv install
```

Activate the virtual environment:

```bash
pipenv shell
```

## Step 5: Set the Python Path

From the project root directory:

```bash
export PYTHONPATH=$(pwd)
```

> **Note:** You need to run this command each time you open a new terminal session, or add it to your shell profile.

## Step 6: Start the API Server

```bash
flask run
```

The API will start at `http://localhost:5000`. Database migrations run automatically on startup.

If port 5000 is in use, run on a different port:

```bash
flask run --host=127.0.0.1 --port=5001
```

Verify the server is running:

```bash
curl http://localhost:5000/api/healthcheck
# Expected: {"message": "Service is up and running.", "status": "OK"}
```

## Step 7: Start the Frontend (Optional)

If you cloned the frontend repository:

```bash
cd augmed-app
npm install
npm start
```

The frontend will start at `http://localhost:3000`. It expects the API at `http://localhost:5000`.

> **Note:** If you see CORS errors in the browser console, you may need to enable CORS in the API. See the comment in `src/__init__.py` — uncomment the CORS lines and reinstall `flask-cors` with `pipenv install flask-cors`.

## Step 8: Load Sample Data

Before participants can review cases, you need OMOP clinical data in the database. The `script/sample_data/` directory contains sample CSV files:

```
script/sample_data/
├── person.csv
├── visit_occurrence.csv
├── observation.csv
├── measurement.csv
├── drug_exposure.csv
└── procedure_occurrence.csv
```

Load the sample data using the load script:

```bash
bash src/load_omop.sh
```

> **Note:** The sample data script may require adjustments to match your local database credentials. Check the script for the connection details and update them to match your `.env`.

## Step 9: Create Test Users

Use the admin API to create participant accounts. Newly created users are **inactive** by default and cannot log in until activated.

Create a test user:

```bash
curl -X POST http://localhost:5000/admin/users \
  -H "Content-Type: application/json" \
  -d '{
    "users": [
      {
        "name": "Test Participant",
        "email": "testparticipant@example.com",
        "position": "Physician",
        "employer": "Test Hospital",
        "area_of_clinical_ex": "Internal Medicine"
      }
    ]
  }'
```

Expected response:

```json
{
  "data": {"testparticipant@example.com": "added"},
  "status": "success"
}
```

## Step 10: Upload a Display Config

The display config assigns cases to participants and specifies which clinical features they see. Create a minimal CSV file named `test_config.csv`:

```csv
User,Case No.,Path,Collapse,Highlight,Top
testparticipant@example.com,1,BACKGROUND.Medical History.Fatigue: Yes,FALSE,TRUE,
testparticipant@example.com,1,BACKGROUND.Family History.Cancer: No,FALSE,TRUE,
testparticipant@example.com,1,RISK ASSESSMENT.CRC risk assessments,FALSE,TRUE,
```

Upload it:

```bash
curl -X POST http://localhost:5000/admin/config/upload \
  -F "file=@test_config.csv"
```

Expected response:

```json
{
  "data": [{"user_case_key": "testparticipant@example.com-1", "status": "added"}],
  "status": "success"
}
```

> **Note:** Uploading a new config **replaces all existing display configs**. See [Config CSV Format](../reference/config-csv-format.md) for details.

## Step 11: Activate a User and Review a Case

Users must be activated before they can log in. Currently, activation is done by directly updating the database. In a future release, this will be available through the admin API.

Activate the test user directly in the database:

```bash
docker exec -it postgres_container psql -U augmed -d augmed \
  -c "UPDATE \"user\" SET active = true, password = 'temp' WHERE email = 'testparticipant@example.com';"
```

> **Note:** Setting a real password requires going through the `POST /api/auth/reset-password-request` flow. For local testing, you can also set a hashed password directly. See [Managing Participants](../researcher-guide/managing-participants.md) for the full activation workflow.

Log in:

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "testparticipant@example.com", "password": "temp"}'
```

The JWT token is returned in the `Authorization` response header.

## What's Next

- [Terminology Glossary](terminology.md) — Understand key concepts
- [Creating Experiments](../researcher-guide/creating-experiments.md) — Design your experimental arms
- [Managing Participants](../researcher-guide/managing-participants.md) — Set up your participant roster
- [API Reference](../reference/api-reference.md) — Full endpoint documentation
