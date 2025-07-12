#!/bin/bash

# Скрипт для генерации самоподписанного SSL сертификата
# Для быстрого тестирования webhook

echo "Генерация самоподписанного SSL сертификата..."

# Создаем директорию для SSL сертификатов
mkdir -p ssl

# Генерируем самоподписанный сертификат
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ssl/key.pem \
    -out ssl/cert.pem \
    -subj "/C=RU/ST=Moscow/L=Moscow/O=WeatherBot/OU=IT/CN=45.12.109.251"

# Устанавливаем права доступа
chmod 644 ssl/cert.pem
chmod 600 ssl/key.pem

echo "Самоподписанный SSL сертификат создан!"
echo "Теперь можно запускать docker-compose up -d"
echo "ВНИМАНИЕ: Telegram может не принять самоподписанный сертификат!"
echo "Для продакшена используйте setup_ssl.sh с Let's Encrypt" 