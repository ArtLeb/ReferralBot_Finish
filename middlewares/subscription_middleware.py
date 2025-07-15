from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, Update
from typing import Callable, Dict, Any, Awaitable, Union
import logging

logger = logging.getLogger(__name__)

class SubscriptionMiddleware(BaseMiddleware):
    def __init__(self):
        self.business_commands = {
            '/add_partner', '/add_admin', '/gen_coupons', 
            '/set_discount', '/set_commission', '/add_group',
            'Создать купон', 'Добавить партнера', 'Назначить админа',
            'Изменить скидку', 'Установить комиссию', 'Сгенерировать купон'
        }

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        # Определяем текст и команду в зависимости от типа события
        event_text = None
        event_command = None
        
        if isinstance(event, Message):
            event_text = event.text
            event_command = event.command
        elif isinstance(event, CallbackQuery) and event.message:
            event_text = event.message.text
        
        # Проверяем, требует ли событие проверки подписки
        if not self.requires_subscription(event_text, event_command):
            return await handler(event, data)
        
        logger.info(f"Checking subscription for event: {event_text or event_command}")
        
        # Получаем сервисы из контекста
        user_service = data.get("user_service")
        subscription_service = data.get("subscription_service")
        
        if not user_service or not subscription_service:
            logger.error("UserService or SubscriptionService not found in context")
            return await handler(event, data)
        
        # Получаем ID пользователя
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
        
        if not user_id:
            logger.warning("User ID not found in event")
            return await handler(event, data)
        
        # Получаем пользователя
        user = await user_service.get_user_by_tg_id(user_id)
        if not user:
            logger.warning(f"User not found for ID: {user_id}")
            # Для сообщений можно ответить, для callback - пропускаем
            if isinstance(event, Message):
                await event.answer("❌ Пользователь не найден!")
            return
        
        # Проверяем подписку
        has_subscription = await subscription_service.check_subscription(user.id)
        
        if has_subscription:
            return await handler(event, data)
        else:
            # Отправляем сообщение об ошибке
            message = "🚫 Для выполнения этого действия нужна активная подписка!\nОбратитесь к администратору для продления подписки."
            
            if isinstance(event, Message):
                await event.answer(message)
            elif isinstance(event, CallbackQuery):
                await event.message.answer(message)
                await event.answer()  # Закрываем callback
            
            return
    
    def requires_subscription(self, text: str, command: str) -> bool:
        """Определяет, требует ли команда проверки подписки"""
        if command and command in self.business_commands:
            return True
        
        if text and any(keyword in text for keyword in self.business_commands):
            return True
            
        return False