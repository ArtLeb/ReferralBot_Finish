from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from utils.database.models import CompLocation

class LocationRepository:
    """Репозиторий для работы с локациями компаний"""
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_location(self, location_data: dict) -> CompLocation:
        """
        Создает новую локацию
        Args:
            location_data: Данные локации
        Returns:
            CompLocation: Созданная локация
        """
        location = CompLocation(**location_data)
        self.session.add(location)
        await self.session.commit()
        await self.session.refresh(location)
        return location
    
    async def get_location_by_id(self, location_id: int) -> CompLocation:
        """
        Получает локацию по ID
        Args:
            location_id: ID локации
        Returns:
            CompLocation: Объект локации
        """
        return await self.session.get(CompLocation, location_id)
    
    async def get_locations_by_company(self, company_id: int) -> list[CompLocation]:
        """
        Получает локации компании
        Args:
            company_id: ID компании
        Returns:
            list[CompLocation]: Список локаций
        """
        stmt = select(CompLocation).where(CompLocation.id_comp == company_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def update_location(self, location_id: int, update_data: dict) -> CompLocation:
        """
        Обновляет данные локации
        Args:
            location_id: ID локации
            update_data: Данные для обновления
        Returns:
            CompLocation: Обновленная локация
        """
        stmt = (
            update(CompLocation)
            .where(CompLocation.id_location == location_id)
            .values(**update_data)
            .returning(CompLocation)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one()
    
    async def delete_location(self, location_id: int) -> bool:
        """
        Удаляет локацию
        Args:
            location_id: ID локации
        Returns:
            bool: True если успешно удалено
        """
        stmt = delete(CompLocation).where(CompLocation.id_location == location_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0