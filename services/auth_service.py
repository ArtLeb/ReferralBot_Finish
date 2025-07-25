from repositories.user_repository import UserRepository
from utils.database.models import User
from datetime import datetime

class AuthService:
    """Сервис для аутентификации и регистрации пользователей"""
    def __init__(self, session):
        self.user_repo = UserRepository(session)
    
    async def get_or_create_user(self, tg_id: int, first_name: str, last_name: str) -> User:
        """
        Получает или создает пользователя в системе
        Args:
            tg_id: Telegram ID пользователя
            first_name: Имя пользователя
            last_name: Фамилия пользователя
        Returns:
            User: Объект пользователя
        """
        user = await self.user_repo.get_user_by_tg_id(tg_id)
        if not user:
            user = await self.user_repo.create_user({
                'id_tg': tg_id,  
                'first_name': first_name,
                'last_name': last_name,
                'tel_num': '',
                'reg_date': datetime.now().date(),
                
            })
        return user
    
    async def update_user_profile(self, user_id: int, update_data: dict) -> User:
        """
        Обновляет профиль пользователя
        Args:
            user_id: ID пользователя
            update_data: Данные для обновления
        Returns:
            User: Обновленный объект пользователя
        """
        return await self.user_repo.update_user(user_id, update_data)