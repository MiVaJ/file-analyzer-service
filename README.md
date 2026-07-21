# File Analyzer Service

Приложение загружает удаленный каталог текстовых файлов через API с ограниченной скоростью и вычисляет статистику по частоте встречаемости цифр в их содержимом с использованием веб-интерфейса.

Source API: `http://91.199.149.128:18001` ([Swagger](http://91.199.149.128:18001/docs))

## Статус

🚧 Проект находится в активной разработке 🚧

## Технологии

FastAPI · SQLAlchemy · PostgreSQL · Redis · RabbitMQ · Celery · Nginx · Docker · uv

## Локальная установка (WIP)

```bash
uv sync
cp .env.example .env
docker compose up --build
```

Приложение буде доступно по адресу `http://localhost:8080` (через nginx).
