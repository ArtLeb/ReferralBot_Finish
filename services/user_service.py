from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from utils.database.models import User

class UserService:
    """Сервис для работы с пользователями"""
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
            (User.user_name.ilike(f"%{query}%")) |
            (User.id_tg.cast(str).ilike(f"%{query}%"))
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def update_user(self, user_id: int, update_data: dict) -> User:
        """
        Обновляет данные пользователя
        Args:
            user_id: ID пользователя
            update_data: Данные для обновления
        Returns:
            User: Обновленный пользователь
        """
        user = await self.get_user_by_id(user_id)
        if user:
            for key, value in update_data.items():
                setattr(user, key, value)
            await self.session.commit()
            return user
        return None