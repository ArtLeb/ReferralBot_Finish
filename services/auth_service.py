from repositories.user_repository import UserRepository
from utils.database.models import User
from datetime import datetime

class AuthService:
    def __init__(self, session):
        self.user_repo = UserRepository(session)

    async def get_or_create_user(self, tg_id: int, first_name: str, last_name: str) -> User:
        user = await self.user_repo.get_user_by_tg_id(tg_id)
        if not user:
            user = await self.user_repo.create_user({
                'id_tg': tg_id,
                'first_name': first_name,
                'last_name': last_name,
                'tel_num': '',
                'reg_date': datetime.now().date(),
                'role': 'client'
            })
        return user