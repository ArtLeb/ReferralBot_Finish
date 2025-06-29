from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Callable, Dict, Awaitable, Any
from utils.database.db_session import get_db_session
from services.role_service import get_user_roles

class RoleMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)
        
        async with get_db_session() as session:
            roles = await get_user_roles(session, user.id)
            data["user_roles"] = roles
        
        return await handler(event, data)