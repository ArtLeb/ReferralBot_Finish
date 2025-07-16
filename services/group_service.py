from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from utils.database.models import GroupCoupon, CouponType
import logging

logger = logging.getLogger(__name__)

class GroupService:
    """Сервис для работы с группами и подписками"""
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def check_user_subscription(self, bot: Bot, user_id: int, coupon_type_id: int) -> bool:
        """
        Проверяет подписку пользователя на группы для купона
        Args:
            bot: Объект бота
            user_id: ID пользователя
            coupon_type_id: ID типа купона
        Returns:
            bool: True если подписка действительна
        """
        try:
            # Получаем группы, необходимые для этого типа купона
            stmt = select(GroupCoupon).where(
                GroupCoupon.coupon_type_id == coupon_type_id
            )
            result = await self.session.execute(stmt)
            group_coupons = result.scalars().all()
            
            if not group_coupons:
                return True  # Если группы не требуются
            
            # Проверяем подписку на каждую группу
            for group_coupon in group_coupons:
                try:
                    member = await bot.get_chat_member(
                        chat_id=group_coupon.group.group_id,
                        user_id=user_id
                    )
                    if member.status not in ['member', 'administrator', 'creator']:
                        return False
                except Exception as e:
                    logger.error(f"Ошибка проверки подписки: {e}")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Ошибка проверки подписок: {e}")
            return False
    
    async def get_required_groups(self, coupon_type_id: int) -> list:
        """
        Получает группы, необходимые для получения купона
        Args:
            coupon_type_id: ID типа купона
        Returns:
            list: Список групп
        """
        stmt = select(GroupCoupon).where(
            GroupCoupon.coupon_type_id == coupon_type_id
        )
        result = await self.session.execute(stmt)
        return [
            {"id": gc.group.group_id, "name": gc.group.name}
            for gc in result.scalars().all()
        ]