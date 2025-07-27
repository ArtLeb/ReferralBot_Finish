from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update
from typing import Callable, Dict, Any, Awaitable
from services.role_service import RoleService
from services.user_service import UserService
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)

class RoleMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Проверяем тип события
        if not isinstance(event, Update):
            return await handler(event, data)
        
        # Определяем пользователя в зависимости от типа обновления
        user = None
        if event.message:
            user = event.message.from_user
        elif event.callback_query:
            user = event.callback_query.from_user
        elif event.inline_query:
            user = event.inline_query.from_user
        
        if not user:
            return await handler(event, data)
        
        # Получаем сессию из данных
        session: AsyncSession = data.get('session')
        if not session:
            logger.error("Сессия БД не найдена в middleware")
            return await handler(event, data)
        
        # Инициализируем сервисы
        role_service = RoleService(session)
        user_service = UserService(session)
        
        # Получаем полную информацию о пользователе из БД
        db_user = await user_service.get_user_by_tg_id(user.id)
        if not db_user:
            logger.warning(f"Пользователь TG ID {user.id} не найден в БД")
            return await handler(event, data)
        
        # Сохраняем пользователя в контексте
        data['user'] = db_user
        data['db_user'] = db_user
        
        # Проверяем разрешения обработчика
        required_permission = getattr(handler, '__required_permission__', None)
        if required_permission:
            # Проверяем наличие разрешения
            has_permission = await role_service.has_permission(db_user, required_permission)
            
            if not has_permission:
                logger.warning(
                    f"У пользователя {db_user.id} нет прав {required_permission} "
                    f"для обработчика {handler.__name__}"
                )
                
                # Отправляем сообщение только если это Message
                if event.message:
                    await event.message.answer("⛔ У вас недостаточно прав для выполнения этой операции")
                return
        
        return await handler(event, data)