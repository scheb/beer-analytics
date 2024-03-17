FROM node:20-bookworm-slim as static-builder

WORKDIR /src
COPY . ./
RUN yarn install && \
    yarn build-prod

# define an alias for the specific python version used in this file.
FROM python:3.11-slim-bookworm as python

FROM python as python-build-stage

ARG APP_HOME=/app
ARG POETRY_VERSION="1.8"

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    PATH="/opt/venv/bin:${POETRY_VENV}/bin:${PATH}"

# Dependencies
RUN apt-get update && \
    apt-get -y install default-libmysqlclient-dev pkg-config build-essential && \
    pip install poetry==${POETRY_VERSION}

WORKDIR ${APP_HOME}

# Install Python dependencies
COPY poetry.lock pyproject.toml ./
RUN poetry install --without dev && \
    rm -rf $POETRY_CACHE_DIR

FROM python as python-run-stage

ARG APP_HOME=/app

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=config.settings_prod

# Dependencies
RUN apt-get update && \
    apt-get -y install default-libmysqlclient-dev git && \
    # cleaning up unused files
    apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false && \
    rm -rf /var/lib/apt/lists/*

# Copy python dependency wheels from python-build-stage
COPY --from=python-build-stage ${VIRTUAL_ENV} ${VIRTUAL_ENV}

WORKDIR ${APP_HOME}

# Copy application code to WORKDIR
COPY ./bin/ ./bin/
COPY ./config/ ./config/
COPY ./recipe_db/ ./recipe_db/
COPY ./web_app/ ./web_app/
COPY ./manage.py ./

 # Get the generated static assets
COPY --from=static-builder /src/bundles/ ./bundles/

COPY --chmod=755 ./build/production/entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
