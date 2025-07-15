# subscription_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from utils.database.models import Subscription
from datetime import date

class SubscriptionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_subscription(self, subscription_data: dict) -> Subscription:
        """Создает новую подписку"""
        subscription = Subscription(**subscription_data)
        self.session.add(subscription)
        await self.session.commit()
        await self.session.refresh(subscription)
        return subscription
    
    async def get_active_subscriptions(self, company_id: int) -> list[Subscription]:
        """Возвращает активные подписки компании"""
        today = date.today()
        stmt = select(Subscription).where(
            Subscription.company_id == company_id,
            Subscription.is_active == True,
            Subscription.start_date <= today,
            Subscription.end_date >= today
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()