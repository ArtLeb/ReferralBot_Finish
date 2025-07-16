from sqlalchemy.ext.asyncio import AsyncSession
from utils.database.models import ActionLog
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ActionLogger:
    """Сервис для логирования действий пользователей"""
    ACTION_TYPES = {
        'coupon_issued': "Выдача купона",
        'coupon_used': "Использование купона",
        'role_assigned': "Назначение роли",
        'user_created': "Создание пользователя",
        'subscription_checked': "Проверка подписки",
        'qr_generated': "Генерация QR-кода"
    }
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def log_action(
        self,
        user_id: int,
        action_type: str,
        entity_id: int = None,
        details: str = None
    ) -> ActionLog:
        """
        Логирует действие пользователя
        Args:
            user_id: ID пользователя
            action_type: Тип действия
            entity_id: ID связанной сущности
            details: Дополнительные детали
        Returns:
            ActionLog: Созданная запись лога
        """
        try:
            action_name = self.ACTION_TYPES.get(action_type, action_type)
            
            log = ActionLog(
                user_id=user_id,
                action_type=action_name,
                entity_id=entity_id,
                timestamp=datetime.now(),
                details=details
            )
            
            self.session.add(log)
            await self.session.commit()
            return log
        except Exception as e:
            logger.error(f"Ошибка записи действия: {e}")
            await self.session.rollback()
            return None