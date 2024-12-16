FROM python:3.12-slim

# Устанавливаем переменные окружения
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Обновляем и устанавливаем системные зависимости
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY django_cor/requirements.txt /app/

# Устанавливаем зависимости
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Копируем оставшиеся файлы проекта
COPY .. /app/


# Пробрасываем порт 8000 (опционально)
EXPOSE 8001

# Команда по умолчанию для запуска приложения
CMD ["python", "manage.py", "runserver", "0.0.0.0:8001"]