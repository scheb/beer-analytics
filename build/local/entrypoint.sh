#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

#python3 manage.py migrate

exec opentelemetry-instrument python3 manage.py runserver 0.0.0.0:8000
