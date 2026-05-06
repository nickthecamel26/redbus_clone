FROM python:3.12-slim

WORKDIR /app

# 1. Install system dependencies for Postgres and building packages
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copy the rest of the application code
COPY . .

# 4. Set the PYTHONPATH so 'app' is discoverable
ENV PYTHONPATH=/app

# 5. Default port for the API (ignored by the worker)
EXPOSE 8000

# 6. Default command (this is overridden by docker-compose for the worker)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]