from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date, timedelta
from utils.database.models import User, UserRole
from utils.config import config
import logging

logger = logging.getLogger(__name__)

class RoleService:
    """Сервис для управления ролями и разрешениями"""
    # Карта разрешений для ролей
    PERMISSION_MAP = {
        'owner': [
            'manage_companies', 'manage_locations', 'add_partners',
            'add_admins', 'view_stats', 'manage_categories', 'view_reports'
        ],
        'partner': [
            'manage_own_companies', 'manage_own_locations', 'gen_coupons',
            'view_own_stats', 'add_agents'
        ],
        'admin': [
            'activate_coupons', 'check_subscriptions', 'view_own_stats',
            'manage_coupons'
        ],
        'client': ['get_coupons', 'view_own_coupons']
    }
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def assign_role_to_user(
        self,
        user_id: int,
        role_name: str,
        company_id: int,
        location_id: int = None
    ) -> UserRole:
        """
        Назначает роль пользователю
        Args:
            user_id: ID пользователя
            role_name: Название роли
            company_id: ID компании
            location_id: ID локации (опционально)
        Returns:
            UserRole: Созданная связь пользователь-роль
        """
        # Проверяем, есть ли уже такая роль
        stmt = select(UserRole).where(
            (UserRole.user_id == user_id) &
            (UserRole.role == role_name) &
            (UserRole.company_id == company_id)
        )
        existing = await self.session.scalar(stmt)
        if existing:
            return existing
        
        # Создаем новую роль
        user_role = UserRole(
            user_id=user_id,
            role=role_name,
            company_id=company_id,
            location_id=location_id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            changed_by=user_id
        )
        
        self.session.add(user_role)
        await self.session.commit()
        return user_role
    
    async def get_user_roles(self, user_id: int) -> list[UserRole]:
        """
        Получает роли пользователя
        Args:
            user_id: ID пользователя
        Returns:
            list[UserRole]: Список ролей
        """
        stmt = select(UserRole).where(UserRole.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def has_permission(self, user_id: int, permission: str) -> bool:
        """
        Проверяет наличие разрешения у пользователя
        Args:
            user_id: ID пользователя
            permission: Требуемое разрешение
        Returns:
            bool: True если разрешение есть
        """
        # Суперпользователь (владелец бота) имеет все права
        user = await self.session.get(User, user_id)
        if user.id_tg == config.OWNER_ID:
            return True
        
        # Получаем роли пользователя
        roles = await self.get_user_roles(user_id)
        
        # Проверяем разрешения для каждой роли
        for role in roles:
            permissions = self.PERMISSION_MAP.get(role.role, [])
            if permission in permissions:
                return True
        
        return False
    
    async def remove_role(self, user_id: int, role_id: int) -> bool:
        """
        Удаляет роль пользователя
        Args:
            user_id: ID пользователя
            role_id: ID роли
        Returns:
            bool: True если успешно удалено
        """
        role = await self.session.get(UserRole, role_id)
        if role and role.user_id == user_id:
            await self.session.delete(role)
            await self.session.commit()
            return True
        return False