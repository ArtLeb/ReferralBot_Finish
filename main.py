import asyncio
import logging
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage  
from utils.bot_obj import bot, dp
from handlers import common_handlers, owner_handlers, partner_handlers, admin_handlers, client_handlers
from middlewares import RoleMiddleware,  DatabaseMiddleware
from utils.logger import setup_logger
from utils.database import init_db

async def main():
    """
    Главная функция запуска бота
    """
    # 1. Настройка системы логирования
    logger = setup_logger()
    logger.info("Starting bot")
    
    # 2. Инициализация базы данных
    await init_db()
    #logger.info("Database initialized")
    
    # 3. Регистрация middleware
    dp.update.middleware(DatabaseMiddleware())  # Обеспечивает сессию БД
    dp.update.middleware(RoleMiddleware())      # Определяет роли пользователя
    #dp.update.middleware(SubscriptionMiddleware())  # Проверяет подписки
    
    logger.info("Middlewares registered")
    
    # 4. Регистрация роутеров (обработчиков команд)
    dp.include_router(common_handlers.router)      # Общие команды (/start, помощь)
    dp.include_router(owner_handlers.router)       # Команды для владельцев
    dp.include_router(partner_handlers.router)     # Команды для партнеров
    dp.include_router(admin_handlers.router)       # Команды для администраторов
    dp.include_router(client_handlers.router)      # Команды для клиентов
    
    logger.info("Routers registered")
    
    # 5. Запуск бота
    await bot.delete_webhook(drop_pending_updates=True)  # Очистка очереди обновлений
    logger.info("Bot is ready to start polling")
    await dp.start_polling(bot)  # Основной цикл обработки сообщений

if __name__ == '__main__':
    # Запуск асинхронного event loop
    asyncio.run(main())