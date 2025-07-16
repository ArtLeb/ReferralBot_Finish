from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_
from utils.database.models import Company, Subscription
from datetime import date

class SubscriptionRepository:
    """Репозиторий для работы с подписками"""
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_subscription(self, subscription_data: dict) -> Subscription:
        """
        Создает новую подписку
        Args:
            subscription_data: Данные подписки
        Returns:
            Subscription: Созданная подписка
        """
        subscription = Subscription(**subscription_data)
        self.session.add(subscription)
        await self.session.commit()
        await self.session.refresh(subscription)
        return subscription
    
    async def get_subscription_by_id(self, subscription_id: int) -> Subscription:
        """
        Получает подписку по ID
        Args:
            subscription_id: ID подписки
        Returns:
            Subscription: Объект подписки
        """
        return await self.session.get(Subscription, subscription_id)
    
    async def get_active_subscriptions(self, company_id: int) -> list[Subscription]:
        """
        Получает активные подписки компании
        Args:
            company_id: ID компании
        Returns:
            list[Subscription]: Список активных подписок
        """
        today = date.today()
        stmt = select(Subscription).where(
            (Subscription.company_id == company_id) &
            (Subscription.is_active == True) &
            (Subscription.start_date <= today) &
            (Subscription.end_date >= today)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_user_subscriptions(self, user_id: int) -> list[Subscription]:
        """
        Получает подписки пользователя
        Args:
            user_id: ID пользователя
        Returns:
            list[Subscription]: Список подписок
        """
        # Предполагаем, что пользователь связан с компаниями
        stmt = select(Subscription).join(Company).where(
            Company.owner_id == user_id
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def update_subscription(self, subscription_id: int, update_data: dict) -> Subscription:
        """
        Обновляет данные подписки
        Args:
            subscription_id: ID подписки
            update_data: Данные для обновления
        Returns:
            Subscription: Обновленная подписка
        """
        stmt = (
            update(Subscription)
            .where(Subscription.id_subscription == subscription_id)
            .values(**update_data)
            .returning(Subscription)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one()
    
    async def delete_subscription(self, subscription_id: int) -> bool:
        """
        Удаляет подписку
        Args:
            subscription_id: ID подписки
        Returns:
            bool: True если успешно удалено
        """
        stmt = delete(Subscription).where(Subscription.id_subscription == subscription_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0