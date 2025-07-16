from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from utils.database.models import User, UserRole
from datetime import date

class UserRepository:
    """Репозиторий для работы с пользователями"""
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_user_by_tg_id(self, tg_id: int) -> User:
        """
        Получает пользователя по Telegram ID
        Args:
            tg_id: Telegram ID пользователя
        Returns:
            User: Объект пользователя
        """
        stmt = select(User).where(User.id_tg == tg_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, user_id: int) -> User:
        """
        Получает пользователя по ID
        Args:
            user_id: ID пользователя
        Returns:
            User: Объект пользователя
        """
        return await self.session.get(User, user_id)
    
    async def create_user(self, user_data: dict) -> User:
        """
        Создает нового пользователя
        Args:
            user_data: Данные пользователя
        Returns:
            User: Созданный пользователь
        """
        user = User(**user_data)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    async def update_user(self, user_id: int, update_data: dict) -> User:
        """
        Обновляет данные пользователя
        Args:
            user_id: ID пользователя
            update_data: Данные для обновления
        Returns:
            User: Обновленный пользователь
        """
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(**update_data)
            .returning(User)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one()
    
    async def delete_user(self, user_id: int) -> bool:
        """
        Удаляет пользователя
        Args:
            user_id: ID пользователя
        Returns:
            bool: True если успешно удалено
        """
        stmt = delete(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0
    
    async def search_users(self, query: str) -> list[User]:
        """
        Поиск пользователей по имени, username или ID
        Args:
            query: Строка для поиска
        Returns:
            list[User]: Список найденных пользователей
        """
        stmt = select(User).where(
            (User.first_name.ilike(f"%{query}%")) |
            (User.last_name.ilike(f"%{query}%")) |
            (User.user_name.ilike(f"%{query}%")) |
            (User.id_tg.cast(str).ilike(f"%{query}%"))
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_users_by_role(self, role_name: str) -> list[User]:
        """
        Получает пользователей по роли
        Args:
            role_name: Название роли
        Returns:
            list[User]: Список пользователей
        """
        stmt = select(User).join(User.roles).where(
            UserRole.role == role_name
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()