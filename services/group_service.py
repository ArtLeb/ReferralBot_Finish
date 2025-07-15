from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from utils.database.models import CouponType, GroupCoupon
from utils.group_check import check_group_subscription
import logging

logger = logging.getLogger(__name__)

class GroupService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def check_user_subscription(self, bot: Bot, user_id: int, coupon_type_id: int) -> bool:
        """
        Проверяет подписку пользователя на группы для заданного типа купона
        с учетом логики AND/OR
        """
        try:
            # Получаем тип купона
            coupon_type = await self.session.get(CouponType, coupon_type_id)
            if not coupon_type:
                logger.error(f"Тип купона {coupon_type_id} не найден")
                return False
            
            # Получаем группы для этого типа купона
            result = await self.session.execute(
                select(GroupCoupon).where(
                    GroupCoupon.coupon_type_id == coupon_type_id
                )
            )
            group_coupons = result.scalars().all()
            
            if not group_coupons:
                logger.info(f"Для типа купона {coupon_type_id} не заданы группы")
                return True
                
            group_ids = [gc.group.group_id for gc in group_coupons]
            
            # Проверяем подписки в зависимости от логики
            if coupon_type.require_all_groups:  # AND-логика
                for group_id in group_ids:
                    if not await check_group_subscription(bot, user_id, group_id):
                        logger.info(f"Пользователь {user_id} не подписан на группу {group_id} (AND логика)")
                        return False
                return True
            else:  # OR-логика
                for group_id in group_ids:
                    if await check_group_subscription(bot, user_id, group_id):
                        logger.info(f"Пользователь {user_id} подписан на группу {group_id} (OR логика)")
                        return True
                return False
                
        except Exception as e:
            logger.error(f"Ошибка проверки подписки: {str(e)}")
            return False

    async def get_required_groups(self, coupon_type_id: int) -> list:
        """
        Возвращает список групп, необходимых для получения купона
        """
        try:
            result = await self.session.execute(
                select(GroupCoupon).where(
                    GroupCoupon.coupon_type_id == coupon_type_id
                )
            )
            return [
                {"id": gc.group.group_id, "name": gc.group.name} 
                for gc in result.scalars().all()
            ]
        except Exception as e:
            logger.error(f"Ошибка получения групп: {str(e)}")
            return []