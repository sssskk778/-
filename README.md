# Redis (через Docker)
docker run -d -p 6379:6379 redis

# Celery воркер
celery -A worker.celery worker --loglevel=info --pool=solo

# Flower (мониторинг)
celery -A worker.celery flower