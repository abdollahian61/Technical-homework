.PHONY: help build up down logs test clean deploy-staging deploy-prod

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build Docker images
	docker-compose build

up: ## Start all services
	docker-compose up -d
	@echo "Services started. Access:"
	@echo "  - FastAPI: http://localhost:8000"
	@echo "  - Prometheus: http://localhost:9090"
	@echo "  - Grafana: http://localhost:3000 (admin/admin)"

down: ## Stop all services
	docker-compose down

logs: ## View logs
	docker-compose logs -f

logs-app: ## View application logs only
	docker-compose logs -f app

test: ## Run tests
	docker-compose exec app pytest -v

test-coverage: ## Run tests with coverage
	docker-compose exec app pytest --cov=app --cov-report=html

lint: ## Run linting
	docker-compose exec app pylint app/*.py

security-scan: ## Run security scans
	docker-compose exec app bandit -r .
	docker-compose exec app safety check

performance-test: ## Run performance tests
	k6 run performance-tests/load-test.js

load-test: ## Run load tests with Locust
	locust -f performance-tests/locustfile.py --host http://localhost:8000 --headless -u 100 -r 10 -t 5m

clean: ## Clean up containers and volumes
	docker-compose down -v
	docker system prune -f

restart: down up ## Restart all services

health: ## Check service health
	@echo "Checking FastAPI health..."
	@curl -f http://localhost:8000/health || echo "FastAPI is not healthy"
	@echo "\nChecking Prometheus..."
	@curl -f http://localhost:9090/-/healthy || echo "Prometheus is not healthy"

metrics: ## View application metrics
	curl http://localhost:8000/metrics

# Kubernetes commands
k8s-deploy-staging: ## Deploy to Kubernetes staging
	kubectl apply -k infrastructure/kubernetes/overlays/staging

k8s-deploy-prod: ## Deploy to Kubernetes production
	kubectl apply -k infrastructure/kubernetes/overlays/production

k8s-status: ## Check Kubernetes deployment status
	kubectl get pods,svc,deploy,hpa

k8s-logs: ## View Kubernetes logs
	kubectl logs -l app=fastapi-app --tail=100 -f

# Terraform commands
tf-init: ## Initialize Terraform
	cd infrastructure/terraform && terraform init

tf-plan: ## Run Terraform plan
	cd infrastructure/terraform && terraform plan

tf-apply: ## Apply Terraform changes
	cd infrastructure/terraform && terraform apply

tf-destroy: ## Destroy Terraform infrastructure
	cd infrastructure/terraform && terraform destroy

# Development helpers
dev-setup: ## Set up development environment
	pip install -r app/requirements.txt
	pip install pytest pylint bandit safety

watch-logs: ## Watch logs in real-time with highlighting
	docker-compose logs -f | grep --color=auto -E "ERROR|WARNING|$$"

monitor: ## Open monitoring dashboards
	@echo "Opening monitoring tools..."
	@open http://localhost:9090 || xdg-open http://localhost:9090 || echo "Visit http://localhost:9090"
	@open http://localhost:3000 || xdg-open http://localhost:3000 || echo "Visit http://localhost:3000"

api-docs: ## Open API documentation
	@open http://localhost:8000/docs || xdg-open http://localhost:8000/docs || echo "Visit http://localhost:8000/docs"
