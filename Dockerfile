# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
# We use /app as the root and place EDU_system inside it
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app/EDU_system
COPY . ./EDU_system

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
# Ensure the root /app is in PYTHONPATH so "from EDU_system.app" works
ENV PYTHONPATH /app
ENV FLASK_APP EDU_system/app.py

# Expose the port the app runs on
EXPOSE 5000

# Run the seeding script and then start the application using gunicorn
# We run seed_egypt.py as a module to correctly handle internal package imports
CMD python -m EDU_system.seed_egypt && gunicorn --bind 0.0.0.0:5000 "EDU_system.app:create_app()"
