FROM python:3.11-slim

# 1) Work at repo root inside container
WORKDIR /app

# 2) Copy entire monorepo (because build context is now ../..)
COPY . /app

# 3) Install dependencies for the API
RUN pip install --no-cache-dir -r apps/api/requirements.txt

# 4) Make repo root importable so "packages" works
ENV PYTHONPATH=/app

# 5) Move into API folder
WORKDIR /app/apps/api

# 6) Run the API
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
