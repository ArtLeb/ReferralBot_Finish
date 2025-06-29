from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder
from redis.asyncio.client import Redis

from utils.config import config as cfg

# Создание бота
bot = Bot(
    token=cfg.BOT_TG_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

# Настройка Redis
redis = Redis(
    host=cfg.REDIS_HOST,
    username=cfg.REDIS_USERNAME,
    password=cfg.REDIS_PASSWORD,
    auto_close_connection_pool=True
)

# Создание диспетчера
dp = Dispatcher(
    storage=RedisStorage(
        redis,
        key_builder=DefaultKeyBuilder(prefix=cfg.REDIS_PREFIX)
    )
)
