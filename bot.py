import os
import asyncio
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from dotenv import load_dotenv

# Загружаем .env
load_dotenv()

# Достаем ключ и СРАЗУ чистим его от пробелов и кавычек
RAW_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_API_KEY = RAW_KEY.strip().replace('"', '').replace("'", "")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Простейшая проверка в консоли при запуске
if not OPENROUTER_API_KEY.startswith("sk-or-v1-"):
    print("❌ ОШИБКА: Ключ OpenRouter выглядит неправильно. Он должен начинаться с 'sk-or-v1-'")

API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemma-4-26b-a4b-it:free"

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

def ask_gemini(prompt: str) -> str:
    try:
        # Прямая сборка заголовков
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        response = requests.post(
            API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 401:
            return "❌ Ошибка 401: Твой API-ключ неверный или не прописан в .env"

        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()

    except Exception as e:
        return f"⚠️ Ошибка: {str(e)}"

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer("Бот запущен. Жду вопросов!")

@dp.message()
async def handle_text(message: types.Message):
    msg = await message.answer("⏳ Думаю...")
    # Используем нить, чтобы не вешать бота
    answer = await asyncio.to_thread(ask_gemini, message.text)
    await msg.edit_text(answer)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())