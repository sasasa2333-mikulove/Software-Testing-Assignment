ARG PYTHON_VERSION=3.13
FROM python:${PYTHON_VERSION}-slim

ENV UV_CACHE_DIR=/tmp/uv-cache \
    UV_LINK_MODE=copy \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN python -m pip install --no-cache-dir uv

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY tests ./tests
COPY scripts ./scripts
COPY hardware ./hardware
COPY main.py ./

RUN uv sync --locked --dev

CMD ["uv", "run", "pytest", "-q"]
