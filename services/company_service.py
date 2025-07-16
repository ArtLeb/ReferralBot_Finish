from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from utils.database.models import Company, CompLocation
import logging
from datetime import date
from typing import List

logger = logging.getLogger(__name__)

class CompanyService:
    """Сервис для управления компаниями и локациями"""
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_company(self, name: str, category_id: int, owner_id: int) -> Company:
        """
        Создает новую компанию
        Args:
            name: Название компании
            category_id: ID категории компании
            owner_id: ID владельца
        Returns:
            Company: Созданная компания
        """
        try:
            # Проверка лимита компаний (не более 5 на пользователя)
            stmt = select(func.count()).where(Company.owner_id == owner_id)
            count = await self.session.scalar(stmt)
            if count >= 5:
                raise ValueError("Превышен лимит компаний (5 на пользователя)")
            
            company = Company(
                Name_comp=name,
                category_id=category_id,
                owner_id=owner_id
            )
            self.session.add(company)
            await self.session.commit()
            await self.session.refresh(company)
            return company
        except Exception as e:
            logger.error(f"Ошибка создания компании: {e}")
            await self.session.rollback()
            raise
    
    async def get_user_companies(self, owner_id: int) -> List[Company]:
        """
        Получает компании пользователя
        Args:
            owner_id: ID владельца
        Returns:
            List[Company]: Список компаний
        """
        stmt = select(Company).where(Company.owner_id == owner_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_company_by_id(self, company_id: int) -> Company:
        """
        Получает компанию по ID
        Args:
            company_id: ID компании
        Returns:
            Company: Объект компании
        """
        return await self.session.get(Company, company_id)
    
    async def update_company(self, company_id: int, update_data: dict) -> Company:
        """
        Обновляет данные компании
        Args:
            company_id: ID компании
            update_data: Данные для обновления
        Returns:
            Company: Обновленная компания
        """
        company = await self.get_company_by_id(company_id)
        if company:
            for key, value in update_data.items():
                setattr(company, key, value)
            await self.session.commit()
            return company
        return None
    
    async def create_location(self, company_id: int, city: str, address: str) -> CompLocation:
        """
        Создает новую локацию компании
        Args:
            company_id: ID компании
            city: Город локации
            address: Адрес локации
        Returns:
            CompLocation: Созданная локация
        """
        try:
            location = CompLocation(
                id_comp=company_id,
                city=city,
                address=address
            )
            self.session.add(location)
            await self.session.commit()
            await self.session.refresh(location)
            return location
        except Exception as e:
            logger.error(f"Ошибка создания локации: {e}")
            await self.session.rollback()
            raise
    
    async def get_locations_by_company(self, company_id: int) -> List[CompLocation]:
        """
        Получает локации компании
        Args:
            company_id: ID компании
        Returns:
            List[CompLocation]: Список локаций
        """
        stmt = select(CompLocation).where(CompLocation.id_comp == company_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_location_by_id(self, location_id: int) -> CompLocation:
        """
        Получает локацию по ID
        Args:
            location_id: ID локации
        Returns:
            CompLocation: Объект локации
        """
        return await self.session.get(CompLocation, location_id)
    
    async def update_location(self, location_id: int, update_data: dict) -> CompLocation:
        """
        Обновляет данные локации
        Args:
            location_id: ID локации
            update_data: Данные для обновления
        Returns:
            CompLocation: Обновленная локация
        """
        location = await self.get_location_by_id(location_id)
        if location:
            for key, value in update_data.items():
                setattr(location, key, value)
            await self.session.commit()
            return location
        return None