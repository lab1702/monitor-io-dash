FROM python:3.13-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files
COPY app.py data_fetcher.py config.py constants.py exceptions.py ui_components.py ./
COPY static/ ./static/
COPY scripts/ ./scripts/

# Create non-root user for security
RUN useradd -m -u 1001 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Use environment variables for configuration
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO

CMD ["python", "app.py"]
