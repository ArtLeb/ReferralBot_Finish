from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from utils.database.models import Company, CompLocation
from repositories.company_repository import CompanyRepository
from repositories.location_repository import LocationRepository
import logging

logger = logging.getLogger(__name__)

class CompanyService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.company_repo = CompanyRepository(session)
        self.location_repo = LocationRepository(session)

    async def create_company(
        self,
        name: str,
        category: str,
        owner_id: int
    ) -> Company:
        """
        Создает новую компанию в базе данных с проверкой лимита
        
        Args:
            name: Название компании
            category: Категория компании
            owner_id: ID владельца компании
            
        Returns:
            Company: Созданный объект компании
            
        Raises:
            ValueError: Если превышен лимит компаний
        """
        try:
            # Проверяем количество компаний у пользователя
            companies_count = await self.session.scalar(
                select(func.count(Company.id_comp)).where(Company.owner_id == owner_id))
            
            if companies_count and companies_count >= 5:
                raise ValueError("❌ Вы можете создать не более 5 компаний")
            
            company = Company(
                Name_comp=name,
                category=category,
                owner_id=owner_id
            )
            return await self.company_repo.create_company(company)
        except Exception as e:
            logger.error(f"Ошибка создания компании: {e}")
            raise

    async def create_location(
        self,
        company_id: int,
        city: str,
        address: str,
        name: str
    ) -> CompLocation:
        """
        Создает новую локацию для компании
        
        Args:
            company_id: ID компании
            city: Город расположения
            address: Адрес локации
            name: Название локации
            
        Returns:
            CompLocation: Созданный объект локации
        """
        try:
            location = CompLocation(
                id_comp=company_id,
                name_loc=name,
                city=city,
                address=address
            )
            return await self.location_repo.create_location(location)
        except Exception as e:
            logger.error(f"Ошибка создания локации: {e}")
            raise