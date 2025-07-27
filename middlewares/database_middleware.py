# middlewares/database_middleware.py
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Callable, Dict, Any, Awaitable
from utils.database.db_session import async_session  

class DatabaseMiddleware(BaseMiddleware):
    """
    Middleware для управления сессиями базы данных.
    Создает новую асинхронную сессию для каждого входящего запроса.
    """
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Создаем новую сессию БД для обработки запроса
        async with async_session() as session:
            # Передаем сессию в данные для использования в хэндлерах
            data['session'] = session
            
            # Вызываем следующий обработчик в цепочке middleware
            result = await handler(event, data)
            
            
            return result
