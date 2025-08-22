FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
EXPOSE 8000
ENV DATA_DIR=/app/app/data
ENV SCHEMAS_DIR=/app/app/schemas
ENV SEEDS_DIR=/app/app/seeds
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
