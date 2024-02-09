FROM python:3.10-slim-bullseye

ARG BUILD_ENVIRONMENT=local
ARG APP_HOME=/app

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ARG POETRY_VERSION="1.4"
ENV DJANGO_SETTINGS_MODULE=beer_analytics.settings_dev
ENV PATH="${PATH}:${POETRY_VENV}/bin"

# Dependencies
RUN apt-get update && \
    apt-get -y install default-libmysqlclient-dev pkg-config build-essential && \
    pip install poetry==${POETRY_VERSION}

WORKDIR ${APP_HOME}

# Install Python dependencies
COPY poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.create false && \
    poetry install

# Copy application code to WORKDIR
COPY . ${APP_HOME}
COPY --chmod=755 ./build/local/entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
