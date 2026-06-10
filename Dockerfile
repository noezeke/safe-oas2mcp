FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml README.md ./
COPY safe_oas2mcp ./safe_oas2mcp
COPY examples ./examples

RUN python -m pip install --no-cache-dir .

ENTRYPOINT ["safe-oas2mcp"]
CMD ["--help"]

