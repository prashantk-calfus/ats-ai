FROM python:3.13-slim

# System deps
RUN apt-get update && apt-get install -y curl build-essential && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_VERSION=1.8.2
RUN pip install --no-cache-dir poetry
ENV PATH="/root/.local/bin:$PATH"

# Set workdir
WORKDIR /app

# Copy only dependency files first
COPY pyproject.toml poetry.lock .env ./

# Install deps
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi

# Copy just the core-package of the code
COPY ats_ai ./ats_ai
COPY .streamlit ./.streamlit
COPY jd_json ./jd_json
COPY jd_folder ./jd_folder

# Create log directory (in case it isn't mounted)
RUN mkdir -p ..logs

EXPOSE 8000 8501
