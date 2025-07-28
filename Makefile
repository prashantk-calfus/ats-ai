.PHONY: local prod make_env install_poetry ui install backend

VERSION := $(shell awk -F '"' '/^version =/ { print $$2 }' pyproject.toml)
PYTHON_VERSION := $(shell awk -F '"' '/^python =/ { print $$2 }' pyproject.toml)
POETRY_HOME := $(shell echo $$HOME/.local/bin)
VENV_DIR := .venv
PROD_IMAGE := ramdorak571/ats_ai_base:$(VERSION)
LOCAL_IMAGE := ats_ai_base:$(VERSION)

prod: build
	PROD_IMAGE=$(LOCAL_IMAGE) docker compose up

local: install
	chmod +x start.sh
	./start.sh

backend: install
	poetry run uvicorn ats_ai.app_server:app --host 0.0.0.0 --port 8000

ui:
	poetry run streamlit run ats_ai/streamlit_app.py --server.port 8501

install: make_env
	poetry install --no-root
	poetry run pre-commit install

build:
	docker build --platform linux/amd64 -t $(LOCAL_IMAGE) .

push:
	docker push $(PROD_IMAGE)

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
