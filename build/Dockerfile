# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Install pipenv and create venv inside project dir (survives USER switch)
ENV PIPENV_VENV_IN_PROJECT=1
RUN pip install pipenv

# Copy the Pipfile and Pipfile.lock into the container
COPY Pipfile Pipfile.lock ./

# Install project dependencies
RUN pipenv install --deploy --ignore-pipfile

# Copy the rest of your application's code
COPY ../ .

# Copy and set entrypoint
COPY build/entrypoint.sh /usr/src/app/entrypoint.sh
RUN chmod +x /usr/src/app/entrypoint.sh

# Run as non-root user for security
RUN useradd --create-home appuser && chown -R appuser:appuser /usr/src/app
USER appuser

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Run migrations and start gunicorn via entrypoint
CMD ["/usr/src/app/entrypoint.sh"]
