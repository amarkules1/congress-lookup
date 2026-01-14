# Use Python 3.10 slim as base image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy Pipfile and Pipfile.lock to the working directory
COPY Pipfile Pipfile.lock .env ./

# Install pipenv, libpq-dev, and use pipenv to install Python dependencies
RUN apt-get update && apt-get install -y gcc libpq-dev && \
    pip install pipenv && \
    pipenv install --system --deploy && \
    apt-get purge -y --auto-remove gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy main.py to the working directory
COPY main.py .

# Copy congress-lookup-frontend/dist directory to the same in the container
COPY congress-lookup-frontend/dist congress-lookup-frontend/dist

# Expose port 5003
EXPOSE 5003

# Command to run the application
CMD ["waitress-serve", "--port=5003", "main:app"]
