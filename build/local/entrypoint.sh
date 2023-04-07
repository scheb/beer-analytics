#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

python3 manage.py migrate

exec python3 manage.py runserver 0.0.0.0:8000
