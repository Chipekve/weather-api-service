#!/bin/bash

# Скрипт для настройки SSL сертификата на VPS
# Запускать на VPS с правами root

echo "Настройка SSL сертификата для webhook..."

# Устанавливаем certbot
apt update
apt install -y certbot

# Создаем временный nginx конфиг для получения сертификата
cat > /tmp/nginx_temp.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    server {
        listen 80;
        server_name 45.12.109.251;
        
        location /.well-known/acme-challenge/ {
            root /var/www/html;
        }
        
        location / {
            return 200 "Temporary server for SSL certificate";
        }
    }
}
EOF

# Создаем директорию для webroot
mkdir -p /var/www/html/.well-known/acme-challenge

# Запускаем временный nginx
docker run -d --name nginx_temp \
    -p 80:80 \
    -v /tmp/nginx_temp.conf:/etc/nginx/nginx.conf:ro \
    -v /var/www/html:/var/www/html \
    nginx:alpine

# Получаем SSL сертификат
# Замените your-domain.com на ваш домен
certbot certonly --webroot \
    --webroot-path=/var/www/html \
    --email your-email@example.com \
    --agree-tos \
    --no-eff-email \
    -d your-domain.com

# Останавливаем временный nginx
docker stop nginx_temp
docker rm nginx_temp

# Создаем директорию для SSL сертификатов
mkdir -p ssl

# Копируем сертификаты
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/cert.pem
cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/key.pem

# Устанавливаем права доступа
chmod 644 ssl/cert.pem
chmod 600 ssl/key.pem

echo "SSL сертификат настроен!"
echo "Теперь можно запускать docker-compose up -d" 