from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from utils.database.models import Company, CompLocation, UserRole
import logging
from datetime import date
from typing import List

logger = logging.getLogger(__name__)

class CompanyService:
    """Сервис для управления компаниями и локациями"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_company(self, name: str) -> Company:
        """
        Создает новую компанию
        
        Args:
            name: Название компании
            
        Returns:
            Company: Созданная компания
        """
        try:
            company = Company(Name_comp=name)
            self.session.add(company)
            await self.session.commit()
            await self.session.refresh(company)
            return company
        except Exception as e:
            logger.error(f"Ошибка создания компании: {e}")
            await self.session.rollback()
            raise
    
    
    async def create_location(
        self,
        company_id: int,
        city: str,
        address: str,
        name_loc: str = "Главный офис" 
    ) -> CompLocation:
        """
        Создает новую локацию компании
        
        Args:
            company_id: ID компании
            city: Город локации
            address: Адрес локации
            name_loc: Название локации
            
        Returns:
            CompLocation: Созданная локация
        """
        try:
            location = CompLocation(
                id_comp=company_id,
                city=city,
                address=address,
                name_loc=name_loc 
            )
            self.session.add(location)
            await self.session.commit()
            await self.session.refresh(location)
            return location
        except Exception as e:
            logger.error(f"Ошибка создания локации: {e}")
            await self.session.rollback()
            raise
    
    async def get_user_companies(self, tg_id: int) -> List[Company]:
        """Получает компании пользователя по его ролям"""
        stmt = select(UserRole.company_id).where(
            UserRole.user_id == tg_id,
            UserRole.role == 'partner'
        )
        result = await self.session.execute(stmt)
        company_ids = [row[0] for row in result.all()]
        
        if not company_ids:
            return []
        
        stmt = select(Company).where(Company.id_comp.in_(company_ids))
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_company_by_id(self, company_id: int) -> Company:
        """Получает компанию по ID"""
        return await self.session.get(Company, company_id)
    
    async def update_company(self, company_id: int, update_data: dict) -> Company:
        """Обновляет данные компании"""
        company = await self.get_company_by_id(company_id)
        if company:
            for key, value in update_data.items():
                setattr(company, key, value)
            await self.session.commit()
            return company
        return None
    
    async def get_locations_by_company(self, company_id: int) -> List[CompLocation]:
        """Получает локации компании"""
        stmt = select(CompLocation).where(CompLocation.id_comp == company_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_location_by_id(self, location_id: int) -> CompLocation:
        """Получает локацию по ID"""
        return await self.session.get(CompLocation, location_id)
    
    async def update_location(self, location_id: int, update_data: dict) -> CompLocation:
        """Обновляет данные локации"""
        location = await self.get_location_by_id(location_id)
        if location:
            for key, value in update_data.items():
                setattr(location, key, value)
            await self.session.commit()
            return location
        return None