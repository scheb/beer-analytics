FROM python:3.11-slim-bookworm

ARG APP_HOME=/app
ARG POETRY_VERSION="1.8"

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=0 \
    POETRY_VIRTUALENVS_CREATE=0 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=config.settings_dev \
    PATH="${POETRY_VENV}/bin:${PATH}"

# Dependencies
RUN apt-get update && \
    apt-get -y install default-libmysqlclient-dev pkg-config build-essential git && \
    pip install poetry==${POETRY_VERSION}

WORKDIR ${APP_HOME}

# Install Python dependencies
COPY poetry.lock pyproject.toml ./
RUN poetry install


# Copy application code to WORKDIR
COPY . ${APP_HOME}
COPY --chmod=755 ./build/local/entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
