FROM python:3.8-slim-bullseye

ARG BUILD_ENVIRONMENT=local
ARG APP_HOME=/app

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ARG POETRY_VERSION="1.4"
ENV DJANGO_SETTINGS_MODULE=beer_analytics.settings_dev

# Install apt packages
RUN apt-get update && apt-get install --no-install-recommends -y \
  # dependencies for building Python packages
  build-essential \
  curl \
  # cleaning up unused files
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install poetry==${POETRY_VERSION}

# Add `poetry` to PATH
ENV PATH="${PATH}:${POETRY_VENV}/bin"

COPY ./build/local/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY poetry.lock pyproject.toml ./

WORKDIR ${APP_HOME}

# Install Python dependencies
RUN poetry config virtualenvs.create false \
  && poetry install

# Copy application code to WORKDIR
COPY . ${APP_HOME}

ENTRYPOINT ["/entrypoint.sh"]
