from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from utils.database.models import CompanyCategory, LocCat
import logging

logger = logging.getLogger(__name__)

class CategoryService:
    """Сервис для управления категориями компаний"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_category(self, name: str) -> CompanyCategory:
        """Создает новую категорию"""
        try:
            category = CompanyCategory(name=name)
            self.session.add(category)
            await self.session.commit()
            await self.session.refresh(category)
            return category
        except Exception as e:
            logger.error(f"Ошибка создания категории: {e}")
            await self.session.rollback()
            raise
    
    async def get_all_categories(self) -> list[CompanyCategory]:
        """Получает все категории"""
        stmt = select(CompanyCategory)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_category_by_id(self, category_id: int) -> CompanyCategory:
        """Получает категорию по ID"""
        return await self.session.get(CompanyCategory, category_id)
    
    async def get_category_by_name(self, name: str) -> CompanyCategory:
        """Получает категорию по названию"""
        stmt = select(CompanyCategory).where(CompanyCategory.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update_category(self, category_id: int, name: str) -> CompanyCategory:
        """Обновляет категорию"""
        category = await self.get_category_by_id(category_id)
        if category:
            category.name = name
            await self.session.commit()
            return category
        return None
    
    async def delete_category(self, category_id: int) -> bool:
        """Удаляет категорию"""
        category = await self.get_category_by_id(category_id)
        if category:
            await self.session.delete(category)
            await self.session.commit()
            return True
        return False
    
    async def get_categories_for_company(self, company_id: int) -> list[CompanyCategory]:
        """
        Получает категории для компании через связь с локациями
        Использует таблицу LOC_CATS для связи
        """
        try:
            stmt = (
                select(CompanyCategory)
                .join(LocCat, LocCat.id_category == CompanyCategory.id)
                .where(LocCat.comp_id == company_id)
            )
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Ошибка получения категорий компании: {e}")
            return []
    
    async def assign_category_to_company(
        self, 
        company_id: int, 
        category_id: int, 
        location_id: int
    ) -> bool:
        """
        Связывает компанию с категорией через локацию
        Использует таблицу LOC_CATS
        """
        try:
            # Проверяем, есть ли уже такая связь
            stmt = select(LocCat).where(
                LocCat.comp_id == company_id,
                LocCat.id_location == location_id,
                LocCat.id_category == category_id
            )
            existing = await self.session.scalar(stmt)
            if existing:
                return True
            
            # Создаем новую связь
            loc_cat = LocCat(
                comp_id=company_id,
                id_location=location_id,
                id_category=category_id
            )
            self.session.add(loc_cat)
            await self.session.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка привязки категории к компании: {e}")
            await self.session.rollback()
            return False