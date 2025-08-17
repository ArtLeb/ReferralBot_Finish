from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder
from redis.asyncio.client import Redis
from utils.config import config

# Создание бота (совместимая версия)
bot = Bot(
    token=config.BOT_TG_TOKEN,
    parse_mode=ParseMode.HTML
)

# Настройка Redis
redis = Redis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,  # Добавьте порт, если используется
    username=config.REDIS_USERNAME,
    password=config.REDIS_PASSWORD,
    db=config.REDIS_DB,  # Добавьте номер базы данных, если используется
    auto_close_connection_pool=True
)

# Создание диспетчера
dp = Dispatcher(
    storage=RedisStorage(
        redis,
        key_builder=DefaultKeyBuilder(prefix=config.REDIS_PREFIX)
    )
)