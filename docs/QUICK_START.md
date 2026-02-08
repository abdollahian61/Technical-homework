# Quick Start Guide

This guide will get you up and running in **less than 5 minutes**.

## Prerequisites

- Docker 24.0+
- Docker Compose 2.0+

That's it! Everything else runs in containers.

## Step 1: Extract Files

```bash
# Extract the ZIP file
unzip devops-platform-task.zip
cd devops-platform-task
```

## Step 2: Start the Platform

```bash
# Start all services (app, Redis, monitoring)
docker-compose up -d

# Wait 30 seconds for services to initialize
```

## Step 3: Verify Everything Works

### Check Application Health
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","redis":"connected"}
```

### Test Write Operation
```bash
curl -X POST "http://localhost:8000/write/test?value=hello"
# Expected: {"message":"Key 'test' set to 'hello'"}
```

### Test Read Operation
```bash
curl http://localhost:8000/
# Expected: {"message":"hello"} or {"detail":"Key not found"}
```

## Step 4: Access Monitoring Tools

### Grafana (Visualization)
- URL: http://localhost:3000
- Username: `admin`
- Password: `admin`

### Prometheus (Metrics)
- URL: http://localhost:9090

### API Documentation
- URL: http://localhost:8000/docs

## Common Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Just the application
docker-compose logs -f app
```

### Run Tests
```bash
docker-compose exec app pytest
```

### Stop Services
```bash
docker-compose down
```

### Restart Everything
```bash
docker-compose restart
```

## Troubleshooting

### Services Won't Start

1. Check if ports are available:
```bash
lsof -i :8000  # FastAPI
lsof -i :6379  # Redis
lsof -i :9090  # Prometheus
lsof -i :3000  # Grafana
```

2. View service status:
```bash
docker-compose ps
```

3. View detailed logs:
```bash
docker-compose logs
```

### Application Returns Errors

1. Check Redis is running:
```bash
docker-compose ps redis
```

2. Check application logs:
```bash
docker-compose logs app
```

3. Restart services:
```bash
docker-compose restart
```

## Next Steps

Once everything is working:

1. Read the [README.md](../README.md) for detailed information
2. Check [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md) for architecture details
3. Review [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md) for key decisions

## Production Deployment

For production deployment:

1. Review `infrastructure/terraform/` for AWS infrastructure
2. Check `infrastructure/kubernetes/` for Kubernetes manifests
3. See `.github/workflows/ci-cd.yml` for CI/CD pipeline

## Getting Help

- Check the [README.md](../README.md)
- Review documentation in `docs/`
- Look at example commands in `Makefile`

---

**Time to working system:** ~3 minutes  
**Services included:** FastAPI, Redis, Prometheus, Grafana, Loki, Promtail  
**Total components:** 6 microservices
