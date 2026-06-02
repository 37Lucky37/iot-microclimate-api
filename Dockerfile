FROM python:3.12-slim

WORKDIR /app

# Встановлюємо системні залежності (включно з curl для healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Встановлюємо Python-залежності
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Копіюємо вихідний код додатку
COPY app /app/app

EXPOSE 8000

# Запускаємо FastAPI-додаток
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]