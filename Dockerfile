FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

# Копирование файлов проекта
COPY requirements.txt .
COPY bot/ bot/
COPY main.py .
COPY weather_image.py .
COPY cache.py .
COPY fonts/ fonts/

# Установка зависимостей Python
RUN pip install --no-cache-dir -r requirements.txt

# Создание директории для логов
RUN mkdir -p logs

# Запуск приложения
CMD ["python", "main.py"] 