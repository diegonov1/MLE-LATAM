# syntax=docker/dockerfile:1.2
FROM python:3.13.2-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set the working directory in the container
WORKDIR /app

# Install required system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    libpq-dev \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copying the requirements files into the container
COPY requirements.txt requirements.txt
COPY requirements-test.txt requirements-test.txt

# Install the required Python libraries
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt -r requirements-test.txt

# Copy all files from the current directory to the working directory in the container
COPY . .

# Expose port 8080 of the container to external network
EXPOSE 8080

# Command to run the FastAPI application with Uvicorn
CMD ["uvicorn", "challenge.api:app", "--host", "0.0.0.0", "--port", "8080"]