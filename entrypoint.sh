#!/bin/bash
set -e

cd /usr/src/app/src

# Run database migrations
echo "Running database migrations..."
pipenv run flask db upgrade

# Optionally seed demo data
if [ "$SEED_DEMO_DATA" = "true" ]; then
    echo "Seeding demo data..."
    cd /usr/src/app
    pipenv run python -m script.seed.seed_demo
    cd /usr/src/app/src
fi

# Start gunicorn
echo "Starting gunicorn..."
exec pipenv run gunicorn "src:create_app()" \
    --bind "0.0.0.0:${PORT:-5000}" \
    --workers "${GUNICORN_WORKERS:-2}" \
    --timeout 120 \
    --preload \
    --access-logfile - \
    --error-logfile - \
    --chdir /usr/src/app
