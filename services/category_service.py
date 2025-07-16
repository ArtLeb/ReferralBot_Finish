from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from utils.database.models import CompanyCategory
import logging

logger = logging.getLogger(__name__)

class CategoryService:
    """Сервис для управления категориями компаний"""
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_category(self, name: str) -> CompanyCategory:
        """
        Создает новую категорию
        Args:
            name: Название категории
        Returns:
            CompanyCategory: Созданная категория
        """
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
        result = await self.session.execute(select(CompanyCategory))
        return result.scalars().all()
    
    async def get_category_by_id(self, category_id: int) -> CompanyCategory:
        """
        Получает категорию по ID
        Args:
            category_id: ID категории
        Returns:
            CompanyCategory: Объект категории
        """
        return await self.session.get(CompanyCategory, category_id)
    
    async def get_category_by_name(self, name: str) -> CompanyCategory:
        """
        Получает категорию по названию
        Args:
            name: Название категории
        Returns:
            CompanyCategory: Объект категории
        """
        stmt = select(CompanyCategory).where(CompanyCategory.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update_category(self, category_id: int, name: str) -> CompanyCategory:
        """
        Обновляет категорию
        Args:
            category_id: ID категории
            name: Новое название
        Returns:
            CompanyCategory: Обновленная категория
        """
        category = await self.get_category_by_id(category_id)
        if category:
            category.name = name
            await self.session.commit()
            return category
        return None
    
    async def delete_category(self, category_id: int) -> bool:
        """
        Удаляет категорию
        Args:
            category_id: ID категории
        Returns:
            bool: True если успешно удалено
        """
        category = await self.get_category_by_id(category_id)
        if category:
            await self.session.delete(category)
            await self.session.commit()
            return True
        return False