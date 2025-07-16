from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_
from utils.database.models import UserRole
from datetime import date

class UserRoleRepository:
    """Репозиторий для работы с ролями пользователей"""
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_user_role(self, role_data: dict) -> UserRole:
        """
        Создает новую роль пользователя
        Args:
            role_data: Данные роли
        Returns:
            UserRole: Созданная роль
        """
        role = UserRole(**role_data)
        self.session.add(role)
        await self.session.commit()
        await self.session.refresh(role)
        return role
    
    async def get_user_role_by_id(self, role_id: int) -> UserRole:
        """
        Получает роль по ID
        Args:
            role_id: ID роли
        Returns:
            UserRole: Объект роли
        """
        return await self.session.get(UserRole, role_id)
    
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
    
    async def get_users_by_role(self, role_name: str) -> list[UserRole]:
        """
        Получает пользователей с определенной ролью
        Args:
            role_name: Название роли
        Returns:
            list[UserRole]: Список ролей
        """
        stmt = select(UserRole).where(UserRole.role == role_name)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def update_user_role(self, role_id: int, update_data: dict) -> UserRole:
        """
        Обновляет данные роли
        Args:
            role_id: ID роли
            update_data: Данные для обновления
        Returns:
            UserRole: Обновленная роль
        """
        stmt = (
            update(UserRole)
            .where(UserRole.id == role_id)
            .values(**update_data)
            .returning(UserRole)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one()
    
    async def delete_user_role(self, role_id: int) -> bool:
        """
        Удаляет роль пользователя
        Args:
            role_id: ID роли
        Returns:
            bool: True если успешно удалено
        """
        stmt = delete(UserRole).where(UserRole.id == role_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0
    
    async def deactivate_expired_roles(self) -> int:
        """
        Деактивирует просроченные роли
        Returns:
            int: Количество деактивированных ролей
        """
        today = date.today()
        stmt = (
            update(UserRole)
            .where(UserRole.end_date < today)
            .values(is_active=False)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount