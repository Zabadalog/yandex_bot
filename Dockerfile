FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY bot.py models.py /app/
COPY src/ /app/src/
CMD ["python", "bot.py"]
