FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

COPY alembic.ini .
COPY migrations ./migrations
COPY radar ./radar

RUN addgroup --system radar \
    && adduser --system --ingroup radar --home /app radar \
    && chown -R radar:radar /app

USER radar

CMD ["python", "-m", "radar.cli", "scheduler"]
