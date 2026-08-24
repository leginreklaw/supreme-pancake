FROM python:3.11-alpine

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir -p /app/static/icons

COPY . .

EXPOSE 5000

# First initialize database once, then start Gunicorn workers
CMD ["sh", "-c", "python -c 'from app import app, db; app.app_context().push(); db.create_all()' && gunicorn --bind 0.0.0.0:5000 --workers 2 app:app"]