# Load .env file if it exists
ifneq (,$(wildcard ./.env))
	include .env
	export
endif

.PHONY: help build up dev down logs clean clean-all shell health test

# Default target
help:
	@echo "<<Available Commands>>"
	@echo "  make build			- Build the docker image"
	@echo "  make up			- Start the application (background)"
	@echo "  make dev			- Start the application (foreground + rebuild)"
	@echo "  make down			- Stop and remove containers"
	@echo "  make logs			- Follow back-end logs"
	@echo "  make clean			- Remove containers, volumes and images associated with this build"
	@echo "  make clean-all		- Remove all containers, volumes, images, and caches (Nuclear option!)"
	@echo "  make shell			- Open a Bash shell inside of the container"
	@echo "  make test			- Mount test/ to the docker image and run all tests"

# Build the image (forcing a rebuild each time code changes)
build:
	docker image prune -f
	docker compose build

# Start services in detached mode
up:
	docker image prune -f
	docker compose up -d

# Builds and runs attached (dev mode)
dev:
	docker image prune -f
	docker compose up --build

# Stop services
down:
	docker compose down

# View live logs
logs:
	docker compose logs -f rag-backend

# Access the container shell
shell:
	docker compose exec rag-backend /bin/bash

# Quick health check (uses Curl command from the config)
health:
	curl -f http://localhost:8000/health || echo "Service is down!"

# Mounts the test/ directory and runs tests on the container build
test:
	docker image prune -f
	docker compose run --rm -v $(PWD)/test:/app/test rag-backend /bin/bash

# Cleans everything including volumes
clean:
	docker compose down -v --rmi local --remove-orphans
	docker image prune -f

# Cleans everything including volumes and caches (Nuclear option!)
clean-all:
	docker system prune -af
	