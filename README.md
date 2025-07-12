# Weather API Service 🌤️

```mermaid
graph TD
    User("Пользователь в Telegram") --> Bot("Telegram-бот (UI)")
    Bot -->|"API-запрос"| WebService("Веб-сервис (бизнес-логика + БД)")
    WebService -->|"API-ответ"| Bot
```

## Структура проекта

```
weather-api-service/
├── bot/                    # Модуль Telegram-бота
│   ├── api.py             # Интеграция с API сервиса
│   ├── bot.py             # Основной файл бота
│   ├── handlers.py        # Обработчики сообщений
│   ├── keyboards.py       # Клавиатуры и кнопки
│   ├── middlewares.py     # Промежуточные обработчики
│   └── states.py          # Состояния FSM
├── tests/                  # Модульные и интеграционные тесты
│   ├── conftest.py        # Фикстуры для тестов
│   ├── test_api.py        # Тесты API endpoints
│   └── test_weather_image.py  # Тесты генерации изображений
├── fonts/                  # Шрифты для генерации изображений
│   └── DejaVuSans.ttf     # Основной шрифт
├── logs/                   # Логи приложения
├── main.py                # Основной файл FastAPI приложения
├── weather_image.py       # Генерация изображений с погодой
├── requirements.txt       # Зависимости Python
├── requirements-test.txt  # Зависимости для тестирования
├── Dockerfile            # Конфигурация Docker
├── docker-compose.yml    # Конфигурация Docker Compose
└── env.example           # Пример переменных окружения
```

## О проекте

**Weather API Service** — это универсальный погодный backend, который:
- Предоставляет REST API для получения текущей погоды, прогноза и поиска городов
- Легко интегрируется с любыми клиентами: Telegram-бот, мобильное приложение, веб-интерфейс
- Реализует все бизнес-правила и хранение данных на сервере
- Генерирует красивые изображения с погодой для Telegram

## Основные возможности

- **Асинхронный FastAPI** — высокая производительность и масштабируемость
- **Pydantic** — строгая типизация и валидация данных
- **Swagger/OpenAPI** — автогенерация документации
- **Docker-ready** — легко разворачивается в контейнере
- **Redis-кэширование** — ускоряет ответы и экономит лимиты внешнего API
- **Тесты** — модульные и интеграционные тесты с pytest
- **Логирование** — подробные логи работы приложения

---

## Кэширование с помощью Redis

Сервис поддерживает автоматическое кэширование данных о погоде, прогнозах и поиске городов с помощью Redis. Это позволяет:
- Ускорить ответы для популярных городов
- Снизить количество обращений к внешнему WeatherAPI
- Гибко настраивать время жизни кэша (TTL)

### Как это работает
- При запросе погоды или прогноза сервис сначала ищет данные в Redis.
- Если данные есть и не устарели — возвращает их мгновенно.
- Если данных нет или TTL истёк — делает запрос к WeatherAPI, сохраняет результат в кэш и возвращает пользователю.

### Настройка
- Redis поднимается автоматически через docker-compose (сервис `redis`).
- Все параметры кэширования настраиваются через переменные окружения:

```
REDIS_URL=redis://localhost:6379         # URL подключения к Redis
CACHE_TTL_WEATHER=600                    # TTL для текущей погоды (секунды, по умолчанию 10 минут)
CACHE_TTL_FORECAST=1800                  # TTL для прогноза (секунды, по умолчанию 30 минут)
CACHE_TTL_CITIES=3600                    # TTL для поиска городов (секунды, по умолчанию 1 час)
```

### Эндпоинты для мониторинга и управления кэшем

- `GET /cache/stats` — статистика кэша (количество ключей, использование памяти и т.д.)
- `GET /cache/health` — проверка состояния кэша
- `DELETE /cache/clear` — очистка всего кэша или по типу/ключу (например, `/cache/clear?cache_type=weather&identifier=Moscow`)

---

## Установка и запуск

### Предварительные требования
- Python 3.8 или выше
- Git
- Редактор кода (VS Code, PyCharm и т.д.)
- Терминал (Terminal для macOS, Command Prompt или PowerShell для Windows)

### Установка для macOS/Linux

1. **Клонирование репозитория:**
```bash
# Создайте папку для проекта
mkdir ~/Projects
cd ~/Projects

# Клонируйте репозиторий
git clone https://github.com/your-username/weather-api-service.git
cd weather-api-service
```

2. **Создание и активация виртуального окружения:**
```bash
# Создание виртуального окружения
python3 -m venv venv

# Активация виртуального окружения
source venv/bin/activate
```

3. **Установка зависимостей:**
```bash
# Обновление pip
pip install --upgrade pip

# Установка зависимостей
pip install -r requirements.txt

# Установка зависимостей для тестов (опционально)
pip install -r requirements-test.txt
```

4. **Настройка переменных окружения:**
```bash
# Копирование примера конфигурации
cp env.example .env

# Откройте файл .env в редакторе и добавьте:
# - WEATHER_API_KEY (получить на weatherapi.com)
# - TELEGRAM_BOT_TOKEN (получить у @BotFather)
```

### Установка для Windows

1. **Клонирование репозитория:**
```powershell
# Создайте папку для проекта
mkdir C:\Projects
cd C:\Projects

# Клонируйте репозиторий
git clone https://github.com/your-username/weather-api-service.git
cd weather-api-service
```

2. **Создание и активация виртуального окружения:**
```powershell
# Создание виртуального окружения
python -m venv venv

# Активация виртуального окружения
.\venv\Scripts\activate
```

3. **Установка зависимостей:**
```powershell
# Обновление pip
python -m pip install --upgrade pip

# Установка зависимостей
pip install -r requirements.txt

# Установка зависимостей для тестов (опционально)
pip install -r requirements-test.txt
```

4. **Настройка переменных окружения:**
```powershell
# Копирование примера конфигурации
copy env.example .env

# Откройте файл .env в редакторе и добавьте:
# - WEATHER_API_KEY (получить на weatherapi.com)
# - TELEGRAM_BOT_TOKEN (получить у @BotFather)
```

### Запуск приложения

1. **Запуск API сервиса:**
```bash
# Стандартный запуск
python main.py

# Или через uvicorn с автоперезагрузкой (для разработки)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

2. **Запуск Telegram бота:**
```bash
# В отдельном терминале
python -m bot.bot
```

3. **Запуск через Docker:**
```bash
# Сборка и запуск всех сервисов
docker-compose up --build

# Запуск в фоновом режиме
docker-compose up -d
```

### Запуск тестов

```bash
# Запуск всех тестов
pytest tests/

# Запуск с отчетом о покрытии
pytest tests/ --cov=.
```

## API документация

После запуска API сервиса документация доступна по адресам:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Примеры запросов

1. **Получение погоды:**
```bash
curl -X POST "http://localhost:8000/weather" \
     -H "Content-Type: application/json" \
     -d '{"city": "Moscow"}'
```

2. **Поиск города:**
```bash
curl -X POST "http://localhost:8000/cities/search" \
     -H "Content-Type: application/json" \
     -d '{"query": "Mosc"}'
```

