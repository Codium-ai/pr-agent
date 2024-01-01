ARG PYTHON_VERSION=3.10
FROM python:$PYTHON_VERSION as builder

# Configure Poetry
ARG POETRY_VERSION=1.7.1
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VENV=/opt/poetry-venv
ENV POETRY_CACHE_DIR=/opt/.cache
ENV POETRY_VIRTUALENVS_IN_PROJECT=1
ENV POETRY_NO_INTERACTION=1
ENV PYTHONUNBUFFERED=1

# Install poetry separated from system interpreter
RUN python3 -m venv $POETRY_VENV \
    && $POETRY_VENV/bin/pip install -U pip setuptools \
    && $POETRY_VENV/bin/pip install poetry==$POETRY_VERSION

# Add `poetry` to PATH
ENV PATH="${PATH}:${POETRY_VENV}/bin"

WORKDIR /usr/app
COPY poetry.lock pyproject.toml ./
RUN poetry install --without dev --no-root && rm -rf $POETRY_CACHE_DIR
RUN poetry export -f requirements.txt -o requirements-dev.txt --only=dev

FROM python:$PYTHON_VERSION as base

ARG UID=1000
ARG GID=1000

ENV PYTHONPATH=/usr/app/
ENV VIRTUAL_ENV=/usr/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Create and use non-root user
RUN groupadd -g $GID -r pr_agent && useradd -m -g $GID -u $UID pr_agent

WORKDIR /usr/app
COPY --chown=pr_agent:pr_agent --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY --chown=pr_agent:pr_agent pr_agent/ $PYTHONPATH/pr_agent/
USER pr_agent

FROM base as github_app
CMD ["python", "pr_agent/servers/github_app.py"]

FROM base as bitbucket_app
CMD ["python", "pr_agent/servers/bitbucket_app.py"]

FROM base as bitbucket_server_webhook
CMD ["python", "pr_agent/servers/bitbucket_server_webhook.py"]

FROM base as github_polling
CMD ["python", "pr_agent/servers/github_polling.py"]

FROM base as gitlab_webhook
CMD ["python", "pr_agent/servers/gitlab_webhook.py"]

FROM base as test
COPY --chown=pr_agent:pr_agent --from=builder /usr/app/requirements-dev.txt /usr/app/requirements-dev.txt
RUN python -m pip install -r requirements-dev.txt
COPY tests/ ./tests/

FROM base as cli
ENTRYPOINT ["python", "pr_agent/cli.py"]
