FROM python:3.13-slim

WORKDIR /app

RUN pip install aiogram openai python-dotenv aiohttp-socks --no-cache-dir

COPY bot.py .

CMD ["python", "bot.py"]
