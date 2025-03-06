# syntax=docker/dockerfile:1.2
FROM python:3.13.2-slim

# Set the working directory in the container
WORKDIR /app

# Copying the requirements files into the container
COPY requirements.txt requirements.txt
COPY requirements-test.txt requirements-test.txt

# Install the required Python libraries
RUN pip install -r requirements.txt
RUN pip install -r requirements-test.txt

# Copy all files from the current directory to the working directory in the container
COPY . .

# Expose port 8080 of the container to external network
EXPOSE 8080

# Command to run the FastAPI application with Uvicorn
CMD ["uvicorn", "challenge.api:app", "--host", "0.0.0.0", "--port", "8080"]