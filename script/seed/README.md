# Demo Seed Script

Populates a fresh AugMed database with synthetic clinical cases, demo users, and configuration so the platform is immediately usable.

## What It Creates

- **3 synthetic patients** with OMOP-formatted clinical data (observations, measurements)
- **3 clinical cases** (visit occurrences), one per patient
- **~20 OMOP concepts** (the minimum vocabulary the app needs to render cases)
- **2 users**:
  - `admin@demo.augmed.org` / `augmed-demo` (admin)
  - `researcher@demo.augmed.org` / `augmed-demo` (participant)
- **Display configs** assigning all 3 cases to the researcher
- **Answer config** (questionnaire) for CRC risk assessment
- **System config** (`page_config`) defining the case display layout

## Usage

### Manual

```bash
export PYTHONPATH=$(pwd)
pipenv run python -m script.seed.seed_demo
```

### Automatic (Docker)

Set `SEED_DEMO_DATA=true` in the environment. The `entrypoint.sh` runs the seed script after migrations on every container start. The script is idempotent — it checks for existing data and skips if already seeded.

## Notes

- Uses synthetic data only — no real patient information
- CRC scores are assigned sequentially (7, 8, 9) across the 3 cases
- The seed script uses the same password hashing as the real auth flow, so login works immediately
