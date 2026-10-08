FROM python:3.10-slim

WORKDIR /app
ENV PYTHONPATH=/app
# Install dependencies first for better caching
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy application code
COPY . .

RUN chmod +x start.sh

# Expose API port
EXPOSE 8000

# Run API
CMD ["./start.sh"]
