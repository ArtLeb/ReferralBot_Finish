# role_service.py
from typing import Any, Coroutine, List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import date, timedelta

from sqlalchemy.testing.suite.test_reflection import users

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

    async def get_comp_owner(self, company_id: int, loc_id: int|None) -> User | None:
        smtp = select(User).join(UserRole, User.id_tg==UserRole.user_id).where(
            UserRole.company_id == company_id and
            UserRole.role == 'owner'
        )
        smtp = smtp.where(UserRole.location_id == loc_id) if loc_id else smtp
        result = await self.session.execute(smtp)
        return result.scalar_one_or_none()

    async def assign_role_to_user(
            self,
            user_id: int,
            company_id: int,
            role_name: str,
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
        # Получаем пользователя по ID
        user = await self.session.get(User, user_id)
        if not user:
            return False

        # Если OWNER_ID задан и Telegram ID пользователя совпадает с OWNER_ID, то разрешаем всё
        if config.OWNER_ID and user.id_tg == config.OWNER_ID:
            return True

        # Получаем роли пользователя
        roles = await self.get_user_roles(user_id)

        # Проверяем разрешения для каждой роли
        for role in roles:
            permissions = self.PERMISSION_MAP.get(role.role, [])
            if permission in permissions:
                return True

        return False

    async def remove_role(
            self,
            user_id: int,
            company_id: int,
            role_name: str = None,
            location_id: int = None
    ) -> bool:
        """
        Удаляет роль пользователя

        Args:
            user_id: ID пользователя в Telegram
            company_id: ID компании
            role_name: Название роли (если None - удаляет все роли пользователя в компании/локации)
            location_id: ID локации (если None - удаляет роли в рамках всей компании)

        Returns:
            bool: True если была удалена хотя бы одна роль, False если ничего не удалено
        """
        stmt = delete(UserRole).where(
            (UserRole.user_id == user_id) &
            (UserRole.company_id == company_id)
        )

        if role_name is not None:
            stmt = stmt.where(UserRole.role == role_name)

        if location_id is not None:
            stmt = stmt.where(UserRole.location_id == location_id)

        result = await self.session.execute(stmt)
        await self.session.commit()

        return result.rowcount > 0

    async def get_roles_in_loc(
            self,
            company_id: int,
            role_name: str = None,
            location_id: int = None
    ) -> List[Tuple[UserRole, User]]:
        """
        Получает список пар (UserRole, User) для заданных условий

        Args:
            company_id: ID компании
            role_name: Название роли (опционально)
            location_id: ID локации (опционально)

        Returns:
            List[Tuple[UserRole, User]]: Список пар объектов UserRole и User
        """
        stmt = select(UserRole, User).join(
            User, UserRole.user_id == User.id_tg
        ).where(
            UserRole.company_id == company_id
        )

        if role_name:
            stmt = stmt.where(UserRole.role == role_name)

        if location_id:
            stmt = stmt.where(UserRole.location_id == location_id)

        result = await self.session.execute(stmt)
        return result.all()
