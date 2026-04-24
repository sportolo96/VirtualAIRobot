FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY pyproject.toml ./
COPY src ./src
COPY tests ./tests
COPY docs ./docs
COPY PLAN.md ./PLAN.md
COPY AGENTS.md ./AGENTS.md

RUN mkdir -p /app/artifacts

ENV PYTHONPATH=/app

CMD ["python", "-m", "src.interfaces.http.server"]
