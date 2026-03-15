FROM astral/uv:python3.14-trixie-slim AS builder

# SET ENV
ENV LIBRARY_PATH=/lib:/usr/lib
# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_NO_DEV=1
ENV UV_PYTHON_DOWNLOADS=0
ENV UV_PYTHON=/usr/local/bin/python

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
  --mount=type=bind,source=uv.lock,target=uv.lock \
  --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

COPY . .

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

FROM python:3.14-slim-trixie AS runner
SHELL [ "/bin/bash", "-c" ]

ENV SHELL=/bin/bash
ENV PYTHONBUFFERED=1
ENV LIBRARY_PATH=/lib:/usr/lib
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt-get update && \
    apt-get install -y libmagic1 libmagic-dev


# Creates non-root user
RUN groupadd --system --gid 1000 appuser \ 
  && useradd --system -ms /bin/bash --gid 1000 --uid 1000 --create-home appuser \
  && usermod -aG sudo appuser \
  && mkdir -p /app && mkdir -p /app/logs \
  && chown -R appuser:appuser /app \
  && chown -R appuser:appuser /app/logs

WORKDIR /app

# Copy files from builder
COPY --from=builder --chown=appuser:appuser /app /app

EXPOSE 8000

USER appuser
ENTRYPOINT ["/app/boot.sh"]