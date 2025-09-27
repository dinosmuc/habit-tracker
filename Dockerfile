# Use Python 3.10 slim image for optimal size/reliability balance
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies needed for SQLite and Python packages
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first (for better Docker layer caching)
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir \
    flask==3.1.2 \
    sqlalchemy==2.0.43 \
    alembic==1.16.5 \
    pandas==2.3.2 \
    python-dotenv==1.1.1

# Copy application code
COPY . .

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Make entrypoint script executable
RUN chmod +x entrypoint.sh

# Expose port 5000 (Flask default)
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=habittracker.app:create_app
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# Use entrypoint script for initialization
ENTRYPOINT ["./entrypoint.sh"]
