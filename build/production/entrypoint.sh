#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

# Collect all static images
python manage.py collectstatic --no-input

exec gunicorn config.asgi --bind 0.0.0.0:5000 --chdir=/app -k uvicorn.workers.UvicornWorker
