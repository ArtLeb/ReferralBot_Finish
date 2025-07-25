from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update
from typing import Callable, Dict, Any, Awaitable
from services.role_service import RoleService
from services.user_service import UserService
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)

class RoleMiddleware(BaseMiddleware):
    """
    Middleware для управления ролями и разрешениями пользователей.
    
    Основные функции:
    1. Определяет пользователя из входящего события
    2. Загружает полную информацию о пользователе из БД
    3. Проверяет наличие необходимых разрешений для обработчика
    4. Блокирует выполнение при отсутствии прав
    
    Принцип работы:
    - Для каждого входящего обновления (сообщение, callback и т.д.)
    - Получает Telegram ID пользователя
    - Загружает соответствующую запись из таблицы USERS
    - Проверяет атрибут __required_permission__ обработчика
    - Если разрешение требуется, проверяет его через RoleService
    
    Особенности:
    - Для системного владельца (OWNER_ID) всегда разрешает все действия
    - Сохраняет объект пользователя в контексте (data['user'])
    """
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # 1. Проверяем тип события - работаем только с Update
        if not isinstance(event, Update):
            return await handler(event, data)
        
        # 2. Определяем пользователя в зависимости от типа обновления
        user = None
        if event.message:
            user = event.message.from_user
        elif event.callback_query:
            user = event.callback_query.from_user
        elif event.inline_query:
            user = event.inline_query.from_user
        
        if not user:
            return await handler(event, data)
        
        # 3. Получаем сессию БД из контекста
        session: AsyncSession = data.get('session')
        if not session:
            logger.error("Сессия БД не найдена в middleware")
            return await handler(event, data)
        
        # 4. Инициализируем сервисы
        role_service = RoleService(session)
        user_service = UserService(session)
        
        # 5. Загружаем пользователя из БД по Telegram ID
        db_user = await user_service.get_user_by_tg_id(user.id)
        if not db_user:
            logger.warning(f"Пользователь TG ID {user.id} не найден в БД")
            return await handler(event, data)
        
        # 6. Сохраняем пользователя в контексте для использования в хэндлерах
        data['user'] = db_user
        data['db_user'] = db_user
        
        # 7. Проверяем разрешения обработчика
        required_permission = getattr(handler, '__required_permission__', None)
        
        # Если разрешение не требуется - пропускаем проверку
        if not required_permission:
            return await handler(event, data)
        
        # 8. Проверяем наличие разрешения у пользователя
        has_permission = await role_service.has_permission(db_user.id, required_permission)
        
        if not has_permission:
            logger.warning(
                f"У пользователя {db_user.id} нет прав {required_permission} "
                f"для обработчика {handler.__name__}"
            )
            
            # 9. Отправляем сообщение только для Message событий
            if event.message:
                await event.message.answer("⛔ У вас недостаточно прав для выполнения этой операции")
            return
        
        # 10. Если все проверки пройдены - выполняем обработчик
        return await handler(event, data)