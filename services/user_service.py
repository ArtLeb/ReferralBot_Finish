from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from utils.database.models import User

class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_user_by_tg_id(self, tg_id: int) -> User:
        """Возвращает пользователя по Telegram ID"""
        result = await self.session.execute(
            select(User).where(User.id_tg == tg_id)
        )
        return result.scalar_one_or_none()