ARG PYTHON_VERSION=3.13
FROM ghcr.io/astral-sh/uv:python${PYTHON_VERSION}-bookworm-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --dev --no-install-project

COPY . .
RUN uv sync --locked --dev

CMD ["uv", "run", "pytest", "-q"]
