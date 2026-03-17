# Используем официальный легкий образ Python
FROM python:3.11-slim

# Рабочая директория внутри контейнера
WORKDIR /app

# Копируем зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код бота
COPY bot.py .

# Отключаем буферизацию вывода, чтобы логи сразу появлялись в панели Bothost
ENV PYTHONUNBUFFERED=1

# Команда запуска
CMD ["python", "bot.py"]
