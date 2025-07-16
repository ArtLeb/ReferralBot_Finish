from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from services.role_service import RoleService
from utils.database.models import Subscription, UserRole
from datetime import date, timedelta

class SubscriptionService:
    """Сервис для управления подписками"""
    def __init__(self, session: AsyncSession, role_service: RoleService):
        self.session = session
        self.role_service = role_service
    
    async def check_subscription(self, user_id: int) -> bool:
        """
        Проверяет наличие активной подписки у пользователя
        Args:
            user_id: ID пользователя
        Returns:
            bool: True если есть активная подписка
        """
        # Получаем компании пользователя
        stmt = select(UserRole.company_id).where(
            (UserRole.user_id == user_id) &
            (UserRole.role.in_(['partner', 'admin']))
        )
        result = await self.session.execute(stmt)
        company_ids = [row[0] for row in result.all()]
        
        if not company_ids:
            return False
        
        # Проверяем активные подписки для компаний
        today = date.today()
        stmt = select(Subscription).where(
            Subscription.company_id.in_(company_ids),
            Subscription.is_active == True,
            Subscription.start_date <= today,
            Subscription.end_date >= today
        )
        result = await self.session.execute(stmt)
        return bool(result.scalars().first())
    
    async def create_subscription(
        self,
        company_id: int,
        months: int = 1
    ) -> Subscription:
        """
        Создает новую подписку
        Args:
            company_id: ID компании
            months: Количество месяцев подписки
        Returns:
            Subscription: Созданная подписка
        """
        today = date.today()
        end_date = today + timedelta(days=months * 30)
        
        subscription = Subscription(
            company_id=company_id,
            start_date=today,
            end_date=end_date,
            is_active=True
        )
        
        self.session.add(subscription)
        await self.session.commit()
        return subscription
    
    async def extend_subscription(self, subscription_id: int, months: int) -> Subscription:
        """
        Продлевает подписку
        Args:
            subscription_id: ID подписки
            months: Количество месяцев продления
        Returns:
            Subscription: Обновленная подписка
        """
        subscription = await self.session.get(Subscription, subscription_id)
        if subscription:
            # Если подписка еще активна, продлеваем от текущей даты окончания
            if subscription.end_date > date.today():
                new_end_date = subscription.end_date + timedelta(days=months * 30)
            else:
                new_end_date = date.today() + timedelta(days=months * 30)
            
            subscription.end_date = new_end_date
            subscription.is_active = True
            await self.session.commit()
            return subscription
        return None