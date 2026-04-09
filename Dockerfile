# Используйте официальный образ Python
FROM python:3.10

# Установите рабочую директорию внутри контейнера
WORKDIR /app

# Скопируйте все файлы проекта в текущую директорию контейнера
COPY . .

# Установите зависимости, указанные в requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Команда для запуска бота
CMD ["python", "union_bot.py"]

