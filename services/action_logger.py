from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from utils.database.models import City
import logging

logger = logging.getLogger(__name__)


class CityLogger:
    """Сервис для сторонних таблиц"""
    def __init__(self, session: AsyncSession):
        self.session = session

    async def insert_city(self, name: str) -> City:
        """
        Логирует действие пользователя
        Args:
            name: ID пользователя
        Returns:
            City: Созданная запись лога
        """
        try:
            log = City(name=name)

            self.session.add(log)
            await self.session.commit()
            return log
        except Exception as e:
            logger.error(f"Ошибка записи действия: {e}")
            await self.session.rollback()
            return None

    async def get_all_cities(self) -> List[City] | None:
        """
        Логирует действие пользователя
        Returns:
            City: Созданная запись лога
        """
        try:
            stmt = select(City)
            result = await self.session.execute(stmt)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Ошибка записи действия: {e}")
            return None

    async def get_cities_name_by_id(self, city_ids: List[int]) -> List[str]:
        """
        Получает список названий городов по их ID.

        Args:
            city_ids (List[int]): Список ID городов

        Returns:
            List[str]: Список названий городов
        """
        try:
            stmt = select(City).where(City.id.in_(city_ids))
            result = await self.session.execute(stmt)
            return [city.name for city in result.scalars().all()]
        except Exception as e:
            logger.error(f"Ошибка получения названий городов: {e}")
            return []

