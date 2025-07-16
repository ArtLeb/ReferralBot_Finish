from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from utils.database.models import ActionLog
from datetime import datetime, timedelta

class ActionLogRepository:
    """Репозиторий для работы с логами действий"""
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_action_log(self, log_data: dict) -> ActionLog:
        """
        Создает запись в логе действий
        Args:
            log_data: Данные лога
        Returns:
            ActionLog: Созданная запись лога
        """
        log = ActionLog(**log_data)
        self.session.add(log)
        await self.session.commit()
        return log
    
    async def get_logs_by_user(self, user_id: int, days: int = 30) -> list[ActionLog]:
        """
        Получает логи действий пользователя
        Args:
            user_id: ID пользователя
            days: Количество дней для фильтрации
        Returns:
            list[ActionLog]: Список логов
        """
        start_date = datetime.now() - timedelta(days=days)
        stmt = select(ActionLog).where(
            (ActionLog.user_id == user_id) &
            (ActionLog.timestamp >= start_date)
        ).order_by(ActionLog.timestamp.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_recent_logs(self, limit: int = 100) -> list[ActionLog]:
        """
        Получает последние записи логов
        Args:
            limit: Количество записей
        Returns:
            list[ActionLog]: Список логов
        """
        stmt = select(ActionLog).order_by(ActionLog.timestamp.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_action_count(self, action_type: str) -> int:
        """
        Получает количество действий определенного типа
        Args:
            action_type: Тип действия
        Returns:
            int: Количество действий
        """
        stmt = select(func.count()).where(ActionLog.action_type == action_type)
        result = await self.session.scalar(stmt)
        return result or 0