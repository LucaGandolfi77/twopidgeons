# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for C extensions and other tools
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the current directory contents into the container at /app
COPY . /app

# Install the package in editable mode (or standard mode)
# This installs dependencies listed in pyproject.toml
RUN pip install --no-cache-dir .

# Expose the port the app runs on
EXPOSE 5000

# Define environment variable
ENV FLASK_APP=twopidgeons.server

# Run the application
# We use the CLI entry point to start the server
CMD ["twopidgeons", "serve", "--port", "5000", "--node-dir", "/data", "--node-id", "docker_node"]
