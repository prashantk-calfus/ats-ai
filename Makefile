.PHONY: all make_env install_poetry

PYTHON_VERSION := $(shell awk -F '"' '/^python =/ { print $$2 }' pyproject.toml)
POETRY_HOME := $(shell echo $$HOME/.local/bin)
VENV_DIR := .venv

all: make_env
	poetry install --no-root
	poetry run pre-commit install
	chmod +x start.sh

make_env:
	# Checks if venv is created or not
	@if [ ! -d $(VENV_DIR) ]; then \
		echo "Creating virtual environment with Python $(PYTHON_VERSION)..."; \
		pyenv install -s $(PYTHON_VERSION); \
		pyenv local $(PYTHON_VERSION); \
		python$(PYTHON_VERSION) -m venv $(VENV_DIR); \
	else \
		echo "Virtual environment already exists."; \
	fi
	@echo "Activating venv and installing Poetry if missing..."
	. $(VENV_DIR)/bin/activate && make install_poetry

install_poetry:
	# Install poetry to manage deps
	@if ! command -v poetry >/dev/null 2>&1; then \
		echo "Installing Poetry..."; \
		curl -sSL https://install.python-poetry.org | python3 -; \
	else \
		echo "Poetry already installed."; \
	fi
