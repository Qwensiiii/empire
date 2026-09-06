import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Если нет .env, используем токен напрямую
if not BOT_TOKEN:
    BOT_TOKEN = "8800841098:AAHIR4nwW_QAJR2BGqyaLJmWibaKL8dGdzg"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message()
async def echo(message):
    await message.answer(f"Вы написали: {message.text}")

async def main():
    print("🤖 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())