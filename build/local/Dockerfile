FROM python:3.10-slim-bullseye

ARG BUILD_ENVIRONMENT=local
ARG APP_HOME=/app

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ARG POETRY_VERSION="1.4"
ENV DJANGO_SETTINGS_MODULE=beer_analytics.settings_dev

# Install poetry
RUN pip install poetry==${POETRY_VERSION}

# Add `poetry` to PATH
ENV PATH="${PATH}:${POETRY_VENV}/bin"

WORKDIR ${APP_HOME}

COPY poetry.lock pyproject.toml ./
COPY ./build/local/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

# Install Python dependencies
RUN poetry config virtualenvs.create false \
  && poetry install

# Copy application code to WORKDIR
COPY . ${APP_HOME}

ENTRYPOINT ["/entrypoint.sh"]
