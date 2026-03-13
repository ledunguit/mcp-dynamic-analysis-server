FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        valgrind \
        build-essential \
        make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md .
COPY src ./src
COPY scripts ./scripts
COPY examples ./examples

RUN python -m pip install --no-cache-dir -e .

ENV WORKSPACE_ROOT=/app \
    RUNS_DIR=/app/runs \
    VALGRIND_BIN=valgrind \
    LOG_LEVEL=INFO

EXPOSE 8080

CMD ["mcp-da-server", "--transport", "http", "--host", "0.0.0.0", "--port", "8080"]
