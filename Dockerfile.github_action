FROM python:3.10 as base

WORKDIR /app
ADD pyproject.toml .
ADD requirements.txt .
RUN pip install . && rm pyproject.toml requirements.txt
ENV PYTHONPATH=/app
ADD pr_agent pr_agent
ADD github_action/entrypoint.sh /
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
