# Use an official Python runtime as a parent image
FROM python:3.10-slim-bullseye

WORKDIR /app

# Install psycopg2 dependencies
RUN apt-get update && apt-get install -y libpq-dev gcc

# Copy requirements first
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy rest of the project including media
COPY . /app/

# Ensure media folder exists in image (development/testing)
RUN mkdir -p /app/media && chown -R root:root /app/media || true

# Default to development; set DJANGO_PRODUCTION=True in Cloud Run for production
ENV DJANGO_PRODUCTION=False
ENV SERVE_MEDIA=False

# Expose port for Cloud Run
EXPOSE 8000

# Start command supports both dev and prod modes
CMD ["sh", "-c", "python manage.py migrate && if [ \"$DJANGO_PRODUCTION\" = \"True\" ]; then gunicorn classifieds.wsgi:application --bind 0.0.0.0:${PORT:-8000}; else python manage.py runserver 0.0.0.0:8000; fi"]
