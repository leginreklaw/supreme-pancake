# Use lightweight Python on Alpine Linux
FROM python:3.11-alpine

# Set working directory
WORKDIR /app

# Install dependencies first (leverages Docker cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose Flask default port
EXPOSE 5000

# Run with Gunicorn WSGI server for production performance
# Note: Add gunicorn to requirements.txt if using production server
CMD ["python", "app.py"]