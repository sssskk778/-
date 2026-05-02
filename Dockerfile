FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y libpq-dev && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
ENV FLASK_APP=run.py
RUN python -m pytest tests/ --tb=short
CMD ["python", "run.py"]