# BUILDER #
###########

# pull official base image
FROM python:3.12-slim as builder

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies for building (including mariadb-dev for mysqlclient)
RUN apt update && apt install -y \
    python3 python3-dev default-libmysqlclient-dev build-essential curl \
    pkg-config

# install Poetry
ENV POETRY_VERSION=1.8.3
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

# copy pyproject.toml and poetry.lock
COPY ./pyproject.toml ./poetry.lock* ./

# install dependencies and build wheels
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi \
    && poetry export -f requirements.txt --output requirements.txt --without-hashes \
    && pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r requirements.txt


# FINAL #
########

# pull official base image
FROM python:3.12-slim

# create directory for the app user
RUN mkdir -p /home/app

# create the app user
RUN addgroup --system app && adduser --system --group app

# create the appropriate directories
ENV HOME=/home/app
ENV APP_HOME=/home/app/web
RUN mkdir -p $APP_HOME/static $APP_HOME/media
WORKDIR $APP_HOME

# install runtime dependencies
RUN apt update && apt install -y libpq-dev default-libmysqlclient-dev

# copy wheels and install dependencies
COPY --from=builder /usr/src/app/wheels /wheels
COPY --from=builder /usr/src/app/pyproject.toml ./pyproject.toml
COPY --from=builder /usr/src/app/poetry.lock ./poetry.lock
RUN pip install --no-cache /wheels/*

# copy entrypoint-prod.sh
COPY ./scripts/entrypoint.prod.sh $APP_HOME

# copy project files
COPY . $APP_HOME

# chown all the files to the app user
RUN chown -R app:app $APP_HOME

# change to the app user
USER app
