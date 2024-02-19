# Use the official Python image as a base image
FROM python:3.9

RUN apt-get update \
    && apt-get install curl -y \
    && curl -sSL https://install.python-poetry.org | python - 

ENV PATH="/root/.local/bin:$PATH"

# Copy the poetry files to the working directory
WORKDIR /app
COPY poetry.lock pyproject.toml /app/

# RUN poetry config virtualenvs.create false
# Copy the rest of the application code to the working directory
COPY . /app/

ENV PYTHONUNBUFFERED=1
# RUN poetry env use 3.9
# RUN [ "poetry",  "shell" ]
RUN poetry install 

# Specify the command to run on container start
# CMD [ "poetry", "run" "python", "-u", "main.py"]
CMD ["poetry", "run", "python", "-u", "main.py"]

