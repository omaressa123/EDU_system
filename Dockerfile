# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONPATH /app
ENV FLASK_APP app.py

# Expose the port the app runs on
EXPOSE 5000

# Run the seeding script and then start the application using gunicorn
# We use a shell command to ensure both seeding and starting happen
CMD python seed_egypt.py && gunicorn --bind 0.0.0.0:5000 "app:create_app()"
