from sqlalchemy.ext.asyncio import AsyncSession
from utils.database.models import CompLocation

class LocationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_location(self, location: CompLocation) -> CompLocation:
        """
        Создает новую локацию компании в базе данных
        
        Args:
            location: Объект локации для создания
            
        Returns:
            CompLocation: Созданный объект локации
        """
        self.session.add(location)
        await self.session.commit()
        await self.session.refresh(location)
        return location