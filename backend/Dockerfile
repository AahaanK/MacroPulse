FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    pydantic \
    pydantic-settings \
    sqlalchemy \
    alembic \
    psycopg2-binary \
    pandas \
    numpy \
    scipy \
    statsmodels \
    httpx \
    pandas_market_calendars \
    tenacity \
    reportlab \
    matplotlib \
    scikit-learn \
    yfinance \
    pytest \
    pytest-asyncio

# Copy backend source code and data fixtures
COPY macropulse/ macropulse/
COPY alembic/ alembic/
COPY alembic.ini .
COPY data/ data/

EXPOSE 8000

CMD ["uvicorn", "macropulse.main:app", "--host", "0.0.0.0", "--port", "8000"]
