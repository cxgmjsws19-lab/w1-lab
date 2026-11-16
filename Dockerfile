# -----------构建阶段--------------
FROM python:3.12-slim AS builder

ENV UK_LINK_MOOD=copy

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src
RUN uv sync --frozen --no-dev

#-------------运行阶段---------
FROM python:3.12-slim


ENV PYTHONDONTWRITEBYTECODE=1 \    
    PYTHONUNBUFFERED=1    

WORKDIR /app      

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src
COPY alembic.ini ./
COPY migrations ./migrations

ENV PATH="/app/.venv/bin:$PATH"    

EXPOSE 8000       
CMD ["uvicorn", "w1_lab.api:app", "--host", "0.0.0.0", "--port", "8000"]    
