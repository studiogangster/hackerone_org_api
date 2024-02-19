# Use the official Python image as a base image
FROM python:3.10

# Set the working directory to /app
WORKDIR /app

# Copy the poetry files to the working directory
COPY pyproject.toml poetry.lock /app/
COPY .env /app/.env

# Install Poetry and project dependencies
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev

# Copy the rest of the application code to the working directory
COPY . /app/

# Specify the command to run on container start
CMD ["poetry", "run", "python", "main.py"]
