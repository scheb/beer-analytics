#!/bin/bash

set -e
set -o pipefail

APP_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../" && pwd )"

python ${APP_DIR}/manage.py warmup_cache
