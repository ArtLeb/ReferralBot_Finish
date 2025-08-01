from typing import List, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func, and_, or_
from datetime import date, timedelta
from services.user_service import UserService
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

    async def get_comp_owner(self, company_id: int, loc_id: int) -> Optional[User]:
        stmt = select(User).join(UserRole, User.id_tg == UserRole.user_id).where(
            and_(
                UserRole.company_id == company_id,
                UserRole.location_id == loc_id,
                UserRole.role == 'owner'
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def assign_role_to_user(
            self,
            tg_id: int,  # Принимаем Telegram ID вместо внутреннего ID
            company_id: int,
            role_name: str,
            location_id: int = None
    ) -> UserRole:
        """
        Назначает роль пользователю
        Args:
            tg_id: Telegram ID пользователя
            role_name: Название роли
            company_id: ID компании
            location_id: ID локации (опционально)
        Returns:
            UserRole: Созданная связь пользователь-роль
        """
        # Проверяем, есть ли уже такая роль
        stmt = select(UserRole).where(
            and_(
                UserRole.user_id == tg_id,
                UserRole.role == role_name,
                UserRole.company_id == company_id
            )
        )
        existing = await self.session.scalar(stmt)
        if existing:
            return existing

        # Создаем новую роль
        user_role = UserRole(
            user_id=tg_id,
            role=role_name,
            company_id=company_id,
            location_id=location_id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            changed_by=tg_id
        )

        self.session.add(user_role)
        await self.session.commit()
        return user_role

    async def get_user_roles(self, tg_id: int) -> List[UserRole]:
        """
        Получает роли пользователя
        Args:
            tg_id: Telegram ID пользователя
        Returns:
            list[UserRole]: Список ролей
        """
        stmt = select(UserRole).where(UserRole.user_id == tg_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def has_permission(self, tg_id: int, permission: str) -> bool:
        """
        Проверяет наличие разрешения у пользователя
        Args:
            tg_id: Telegram ID пользователя
            permission: Требуемое разрешение
        Returns:
            bool: True если разрешение есть
        """
        # Получаем пользователя по Telegram ID
        user = await UserService(self.session).get_user_by_tg_id(tg_id)
        if not user:
            return False

        # Если OWNER_ID задан и совпадает с Telegram ID, разрешаем всё
        if config.OWNER_ID and tg_id == config.OWNER_ID:
            return True

        # Получаем роли пользователя
        roles = await self.get_user_roles(tg_id)

        # Проверяем разрешения для каждой роли
        for role in roles:
            permissions = self.PERMISSION_MAP.get(role.role, [])
            if permission in permissions:
                return True

        return False

    async def remove_role(
            self,
            tg_id: int,
            company_id: int,
            role_name: str = None,
            location_id: int = None
    ) -> bool:
        """
        Удаляет роль пользователя
        Args:
            tg_id: Telegram ID пользователя
            company_id: ID компании
            role_name: Название роли
            location_id: ID локации
        Returns:
            bool: True если удалено
        """
        conditions = [
            UserRole.user_id == tg_id,
            UserRole.company_id == company_id
        ]
        
        if role_name:
            conditions.append(UserRole.role == role_name)
        if location_id:
            conditions.append(UserRole.location_id == location_id)
            
        stmt = delete(UserRole).where(and_(*conditions))
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def get_location_admins(self, company_id: int, location_id: int) -> List[UserRole]:
        """
        Получает список администраторов для локации
        Args:
            company_id: ID компании
            location_id: ID локации
        Returns:
            list[UserRole]: Список ролей администраторов
        """
        stmt = select(UserRole).where(
            and_(
                UserRole.company_id == company_id,
                UserRole.location_id == location_id,
                UserRole.role == 'admin'
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_user_role_in_location(
        self, 
        tg_id: int, 
        company_id: int, 
        location_id: int, 
        role: str
    ) -> Optional[UserRole]:
        """
        Проверяет наличие роли у пользователя в локации
        Args:
            tg_id: Telegram ID пользователя
            company_id: ID компании
            location_id: ID локации
            role: Название роли
        Returns:
            UserRole или None
        """
        stmt = select(UserRole).where(
            and_(
                UserRole.user_id == tg_id,
                UserRole.company_id == company_id,
                UserRole.location_id == location_id,
                UserRole.role == role
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_admin_role(
        self,
        tg_id: int,
        company_id: int,
        location_id: int,
        end_date: date,
        changed_by: int
    ) -> UserRole:
        """
        Добавляет роль администратора
        Args:
            tg_id: Telegram ID пользователя
            company_id: ID компании
            location_id: ID локации
            end_date: Дата окончания
            changed_by: Telegram ID кто добавил
        Returns:
            UserRole: Созданная роль
        """
        new_role = UserRole(
            user_id=tg_id,
            role='admin',
            company_id=company_id,
            location_id=location_id,
            start_date=date.today(),
            end_date=end_date,
            changed_by=changed_by,
            changed_date=func.now()
        )
        self.session.add(new_role)
        await self.session.commit()
        return new_role

    async def remove_admin_role(self, role_id: int) -> bool:
        """
        Удаляет роль администратора по ID записи
        Args:
            role_id: ID записи в USERS_ROLES
        Returns:
            bool: True если удалено
        """
        stmt = delete(UserRole).where(
            and_(
                UserRole.id == role_id,
                UserRole.role == 'admin'
            )
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0