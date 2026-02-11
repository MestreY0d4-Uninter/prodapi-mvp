FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml .
COPY prodapi ./prodapi
COPY alembic ./alembic
COPY alembic.ini .

RUN uv sync --frozen

ENV DATABASE_URL=postgresql+asyncpg://prodapi:prodapi@db:5432/prodapi
ENV ENVIRONMENT=production
ENV LOG_LEVEL=INFO

EXPOSE 8000

COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

CMD ["./entrypoint.sh"]
