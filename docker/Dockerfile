FROM python:3.10 as base

WORKDIR /app
ADD pyproject.toml .
RUN pip install . && rm pyproject.toml
ENV PYTHONPATH=/app
ADD pr_agent pr_agent

FROM base as github_app
CMD ["python", "pr_agent/servers/github_app.py"]

FROM base as github_polling
CMD ["python", "pr_agent/servers/github_polling.py"]

FROM base as test
ADD requirements-dev.txt .
RUN pip install -r requirements-dev.txt && rm requirements-dev.txt

FROM base as cli
ENTRYPOINT ["python", "pr_agent/cli.py"]
