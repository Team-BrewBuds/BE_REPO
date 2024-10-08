FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV POETRY_VERSION=1.8.3
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VENV=/opt/poetry-venv

RUN python3 -m venv $POETRY_VENV \
	&& $POETRY_VENV/bin/pip install -U pip setuptools \
	&& $POETRY_VENV/bin/pip install poetry==${POETRY_VERSION}

ENV PATH="${PATH}:${POETRY_VENV}/bin"

RUN mkdir /app/
WORKDIR /app/

COPY pyproject.toml .

RUN poetry install

COPY . /app

#CMD ["python3", "manage.py", "runserver", "localhost:8000"]
