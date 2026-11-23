# syntax=docker/dockerfile:1.7
# One image, two entrypoints: the consumer (default) and the producer.

FROM python:3.12-slim AS build
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install -r requirements.txt \
 && pip uninstall -y pip setuptools wheel || true

FROM python:3.12-slim AS runtime
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

# OS security fixes since the base image was built; drop unused installers.
RUN apt-get update \
 && apt-get upgrade -y --no-install-recommends \
 && rm -rf /var/lib/apt/lists/* \
 && { python -m pip uninstall -y pip setuptools wheel || true; } \
 && groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --no-create-home app

WORKDIR /app
COPY --from=build /opt/venv /opt/venv
COPY --chown=app:app src ./src

USER 10001
CMD ["python", "-m", "worker.consumer"]
