from repositories.subscription_repository import SubscriptionRepository
from services.role_service import RoleService
from sqlalchemy import select, and_, func
from utils.database.models import Subscription  # Исправленный импорт
from datetime import date, timedelta
import logging

logger = logging.getLogger(__name__)

class SubscriptionService:
    def __init__(self, session, role_service: RoleService):
        self.session = session
        self.subscription_repo = SubscriptionRepository(session)
        self.role_service = role_service

    async def check_subscription(self, user_id: int) -> bool:
        """
        Проверяет наличие активной подписки для компаний пользователя
        Возвращает True если есть хотя бы одна активная подписка
        """
        try:
            # Получаем роли пользователя
            user_roles = await self.role_service.get_user_roles(user_id)
            
            # Фильтруем только бизнес-роли
            business_roles = ['partner', 'admin', 'owner']
            company_ids = {role.company_id for role in user_roles 
                          if role.role.lower() in business_roles}
            
            # Если пользователь не имеет бизнес-ролей
            if not company_ids:
                logger.info(f"User {user_id} has no business roles")
                return False
            
            # Проверяем наличие активных подписок для компаний
            today = date.today()
            stmt = select(func.count()).where(
                and_(
                    Subscription.company_id.in_(company_ids),
                    Subscription.is_active == True,
                    Subscription.start_date <= today,
                    Subscription.end_date >= today
                )
            )
            
            active_count = await self.session.scalar(stmt)
            return active_count > 0 if active_count else False
            
        except Exception as e:
            logger.error(f"Error checking subscription: {str(e)}")
            return False