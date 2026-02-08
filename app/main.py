from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import redis
import logging
import sys
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import Response
import time

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="DevOps Platform API",
    description="High-performance FastAPI application with Redis backend",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])

# Redis connection with retry logic
def get_redis_client():
    max_retries = 5
    for attempt in range(max_retries):
        try:
            client = redis.Redis(
                host='redis',
                port=6379,
                db=0,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            client.ping()
            logger.info("Successfully connected to Redis")
            return client
        except redis.ConnectionError as e:
            logger.warning(f"Redis connection attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff

redis_client = get_redis_client()

@app.middleware("http")
async def metrics_middleware(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {duration:.4f}s")
    return response

@app.get("/")
def read_root():
    """Root endpoint to read from Redis"""
    try:
        value = redis_client.get("example_key")
        if value is None:
            logger.warning("Key 'example_key' not found in Redis")
            raise HTTPException(status_code=404, detail="Key not found")
        logger.info(f"Successfully retrieved key 'example_key'")
        return {"message": value}
    except redis.RedisError as e:
        logger.error(f"Redis error: {e}")
        raise HTTPException(status_code=500, detail="Database error")

@app.post("/write/{key}")
def write_to_redis(key: str, value: str):
    """Write a key-value pair to Redis"""
    try:
        redis_client.set(key, value)
        logger.info(f"Successfully set key '{key}' to '{value}'")
        return {"message": f"Key '{key}' set to '{value}'"}
    except redis.RedisError as e:
        logger.error(f"Redis error while writing: {e}")
        raise HTTPException(status_code=500, detail="Database error")

@app.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        redis_client.ping()
        return {"status": "healthy", "redis": "connected"}
    except redis.RedisError:
        return {"status": "unhealthy", "redis": "disconnected"}

@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
