FROM python:3.11-slim
LABEL version="8.0.0"

WORKDIR /app

# Copy requirements first (leverage cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir structlog>=23.0.0

# Copy source
COPY src/ ./src/
COPY tests/ ./tests/

# Back to app
WORKDIR /app

# Environment
ENV JWT_SECRET=${JWT_SECRET}
ENV ENV="production"
ENV API_PORT=8000
ENV API_HOST="0.0.0.0"

# Expose ports
EXPOSE 8000


# Run
CMD ["uvicorn", "src.api.server:app", "--host", "0.0.0.0", "--port", "8000"]