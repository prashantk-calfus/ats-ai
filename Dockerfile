FROM python:3.13-slim

# System deps
RUN apt-get update && apt-get install -y curl build-essential && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_VERSION=1.8.2
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# Set workdir
WORKDIR /app

# Copy only dependency files first
COPY pyproject.toml poetry.lock ./

# Install deps
RUN poetry install --no-root

# Copy rest of the code
COPY . .

# Ensure script is executable
RUN chmod +x start.sh

# Create log directory (in case it isn't mounted)
RUN mkdir -p ..logs

# Start both apps
# CMD ["./start.sh"]
