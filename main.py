import asyncio
import logging
from aiogram import Dispatcher
from utils.bot_obj import bot
from handlers import (
    common_handlers,
    coupon_handlers,
    admin_handlers,
    partner_handlers,
    subscription_handlers
)
from middlewares.role_middleware import RoleMiddleware

async def main():
    logging.basicConfig(level=logging.INFO)
    
    dp = Dispatcher()
    
    # Регистрация middleware
    dp.message.middleware(RoleMiddleware())
    dp.callback_query.middleware(RoleMiddleware())
    
    # Регистрация роутеров
    dp.include_router(common_handlers.router)
    dp.include_router(coupon_handlers.router)
    dp.include_router(admin_handlers.router)
    dp.include_router(partner_handlers.router)
    dp.include_router(subscription_handlers.router)
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())