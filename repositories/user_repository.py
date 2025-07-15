from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from utils.database.models import User, UserRole
from datetime import date

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_tg_id(self, tg_id: int) -> User:
        result = await self.session.execute(
            select(User).where(User.id_tg == tg_id)
        )
        return result.scalar_one_or_none()

    async def create_user(self, user_data: dict) -> User:
        user = User(**user_data)
        self.session.add(user)
        await self.session.commit()
        return user

    async def get_user_roles(self, user_id: int):
        result = await self.session.execute(
            select(UserRole).where(UserRole.user_id == user_id)
        )
        return result.scalars().all()