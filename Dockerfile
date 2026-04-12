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
ENV FLASK_APP EDU_system/app.py

# Expose the port the app runs on
EXPOSE 5000

# Run the seeding script and then start the application
# We use a shell script or a combined command to ensure data is present
CMD python EDU_system/seed_egypt.py && gunicorn --bind 0.0.0.0:5000 "EDU_system.app:create_app()"
