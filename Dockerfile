FROM python:3.11-slim

WORKDIR /app

RUN pip install poetry==1.8.0 && \
    poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-dev --no-interaction

COPY api/ ./api/
COPY migrations/ ./migrations/
COPY alembic.ini ./

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
