import asyncio
from utils.bot_obj import bot, dp
from handlers import (common_handlers, owner_handlers, partner_handlers,
                      admin_handlers, client_handlers, command_handler, edit_company_handler,
                      new_location_handler, collaboration_handler, collab_coupon_handler, tg_group_handlers,
                      my_collabs_handler, collab_req_handler)
from middlewares import DatabaseMiddleware
from utils.logger import setup_logger

async def main():
    """
    Главная функция запуска бота
    """
    # 1. Настройка системы логирования
    logger = setup_logger()
    logger.info("Starting bot")
    
    # 2. Инициализация базы данных
    logger.info("Database initialized")
    
    # 3. Регистрация middleware
    dp.update.middleware(DatabaseMiddleware())  # Обеспечивает сессию БД

    logger.info("Middlewares registered")
    
    # 4. Регистрация роутеров (обработчиков команд)
    dp.include_router(command_handler.router)
    dp.include_router(collab_req_handler.router)
    dp.include_router(common_handlers.router)
    dp.include_router(edit_company_handler.router)
    dp.include_router(collaboration_handler.router)
    dp.include_router(collab_coupon_handler.router)
    dp.include_router(new_location_handler.router)
    dp.include_router(owner_handlers.router)
    dp.include_router(partner_handlers.router)
    dp.include_router(my_collabs_handler.router)
    dp.include_router(admin_handlers.router)
    dp.include_router(client_handlers.router)
    dp.include_router(tg_group_handlers.router)
    
    logger.info("Routers registered")
    
    # 5. Запуск бота
    await bot.delete_webhook(drop_pending_updates=True)  # Очистка очереди обновлений
    logger.info("Bot is ready to start polling")
    await dp.start_polling(bot)  # Основной цикл обработки сообщений

if __name__ == '__main__':
    # Запуск асинхронного event loop
    asyncio.run(main())
