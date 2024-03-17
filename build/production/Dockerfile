FROM node:20-bookworm-slim as static_build

WORKDIR /src
COPY . ./
RUN yarn install && \
    yarn build-prod


FROM python:3.11-slim-bookworm

ARG BUILD_ENVIRONMENT=production
ARG APP_HOME=/app
ARG POETRY_VERSION="1.8"

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV DJANGO_SETTINGS_MODULE=config.settings_prod
ENV PATH="${PATH}:${POETRY_VENV}/bin"

# Dependencies
RUN apt-get update && \
    apt-get -y install default-libmysqlclient-dev pkg-config build-essential git && \
    pip install poetry==${POETRY_VERSION}

WORKDIR ${APP_HOME}

# Install Python dependencies
COPY poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.create false && \
    poetry install

# Copy application code to WORKDIR
COPY ./bin/ ./bin/
COPY ./config/ ./config/
COPY ./recipe_db/ ./recipe_db/
COPY ./web_app/ ./web_app/
COPY ./manage.py ./

 # Get the generated static assets
COPY --from=static_build /src/bundles/ ./bundles/

COPY --chmod=755 ./build/production/entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
