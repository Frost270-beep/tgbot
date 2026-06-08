import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.client.session.aiohttp import AiohttpSession
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dp = Dispatcher()

_default_headers = {}
if site_url := os.getenv("OPENROUTER_SITE_URL"):
    _default_headers["HTTP-Referer"] = site_url
if app_name := os.getenv("OPENROUTER_APP_NAME", "Telegram LLM Bot"):
    _default_headers["X-Title"] = app_name

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY", ""),
    default_headers=_default_headers or None,
)

user_context = {}


def get_user_history(user_id: int) -> list:
    if user_id not in user_context:
        user_context[user_id] = [
            {"role": "system", "content": "Продолжай диалог."}
        ]
    return user_context[user_id]


@dp.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    user_context[user_id] = [{"role": "system", "content": "Продолжай диалог."}]
    await message.answer("Привет! Я бот на базе ИИ. Просто напиши мне что-нибудь, и я отвечу.")


@dp.message(Command("help"))
async def help_handler(message: types.Message):
    await message.answer("Команды:\n/start - сбросить контекст\n/help - помощь\nПросто текст - общение с ИИ.")


@dp.message()
async def chat_handler(message: types.Message):
    if not message.text:
        return

    user_id = message.from_user.id
    history = get_user_history(user_id)
    history.append({"role": "user", "content": message.text})

    if len(history) > 11:
        history = [history[0]] + history[-10:]

    try:
        response = await client.chat.completions.create(
            model=os.getenv("MODEL_NAME", "meta-llama/llama-3.3-70b-instruct:free"),
            messages=history,
        )
        answer = response.choices[0].message.content
        history.append({"role": "assistant", "content": answer})
        user_context[user_id] = history

        try:
            await message.answer(answer, parse_mode="Markdown")
        except Exception as e:
            logger.warning(f"Markdown parsing failed: {e}")
            await message.answer(answer)

    except Exception as e:
        logger.error(f"Ошибка в API: {e}")
        await message.answer(f"капут: {e}")


async def main():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_TOKEN не задан")

    proxy = os.getenv("PROXY_URL")
    if proxy:
        bot = Bot(token=token, session=AiohttpSession(proxy=proxy))
        logger.info("готов (подключено через прокси)")
    else:
        bot = Bot(token=token)
        logger.info("готов")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
