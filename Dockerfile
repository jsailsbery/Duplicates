# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory inside the container to /app
WORKDIR /app

# Install any needed packages specified in requirements.txt
COPY requirements.txt /app
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app

# Define environment variable for Python to run in unbuffered mode
ENV PYTHONUNBUFFERED 1

# Add the project directory to the Python path
ENV PYTHONPATH "${PYTHONPATH}:/app"

# Run your program or tests here
# For example, to run pytest:
CMD ["python", "duplicates/file_index.py"]

