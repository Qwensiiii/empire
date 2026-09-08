import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base
from database.crud import DatabaseCRUD
from game.economy import EconomyManager
from bot.handlers import router, setup_handlers

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///empire.db')

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация базы данных
engine = create_engine(DATABASE_URL, echo=True)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Инициализация CRUD и экономики
db = DatabaseCRUD(session)
economy = EconomyManager(db)

# Инициализация бизнесов при первом запуске
economy.init_businesses()

# Настройка бота
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# Настройка обработчиков
setup_handlers(db, economy)
dp.include_router(router)

async def main():
    logger.info("🚀 Бот Business Empire запущен!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен")