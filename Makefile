# Makefile for Nice-2-Meet-U-Match

.PHONY: help setup-cloud-sql install run test clean auth-gcloud proxy

help:
	@echo "Available commands:"
	@echo "  make install           - Install dependencies"
	@echo "  make setup-cloud-sql   - Setup Cloud SQL connection"
	@echo "  make auth-gcloud       - Authenticate with gcloud"
	@echo "  make proxy             - Start Cloud SQL Proxy (run in separate terminal)"
	@echo "  make run               - Run the FastAPI application"
	@echo "  make test              - Run tests"
	@echo "  make clean             - Clean up __pycache__ and .pyc files"
	@echo ""
	@echo "Example workflow:"
	@echo "  1. make auth-gcloud"
	@echo "  2. make setup-cloud-sql"
	@echo "  3. make proxy           (in another terminal, optional)"
	@echo "  4. make run"

install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt

setup-cloud-sql:
	@echo "Starting Cloud SQL setup..."
	chmod +x setup_cloud_sql.sh
	./setup_cloud_sql.sh

auth-gcloud:
	@echo "Authenticating with gcloud..."
	gcloud auth login
	@echo ""
	@echo "Setting up application default credentials for Python..."
	gcloud auth application-default login

proxy:
	@if [ -z "$$INSTANCE_CONNECTION_NAME" ]; then \
		echo "Error: INSTANCE_CONNECTION_NAME environment variable not set"; \
		echo "Please run 'make setup-cloud-sql' first to set up your .env"; \
		exit 1; \
	fi
	@echo "Starting Cloud SQL Proxy for $$INSTANCE_CONNECTION_NAME..."
	cloud-sql-proxy $$INSTANCE_CONNECTION_NAME --port 3306

run:
	@if [ ! -f .env ]; then \
		echo "Error: .env file not found. Please run 'make setup-cloud-sql' first"; \
		exit 1; \
	fi
	@echo "Starting FastAPI application..."
	python main.py

test:
	@echo "Running tests..."
	pytest -v

clean:
	@echo "Cleaning up..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "Clean complete"

.env:
	@echo "Creating .env from .env.example..."
	@if [ ! -f .env.example ]; then \
		echo "Error: .env.example not found"; \
		exit 1; \
	fi
	cp .env.example .env
	@echo ".env created. Please edit it with your settings."
