from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from utils.database.models import CompanyCategory

class CategoryRepository:
    """Репозиторий для работы с категориями компаний"""
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
        category = CompanyCategory(name=name)
        self.session.add(category)
        await self.session.commit()
        await self.session.refresh(category)
        return category
    
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
    
    async def get_all_categories(self) -> list[CompanyCategory]:
        """
        Получает все категории
        Returns:
            list[CompanyCategory]: Список категорий
        """
        stmt = select(CompanyCategory)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def update_category(self, category_id: int, name: str) -> CompanyCategory:
        """
        Обновляет название категории
        Args:
            category_id: ID категории
            name: Новое название
        Returns:
            CompanyCategory: Обновленная категория
        """
        stmt = (
            update(CompanyCategory)
            .where(CompanyCategory.id == category_id)
            .values(name=name)
            .returning(CompanyCategory)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one()
    
    async def delete_category(self, category_id: int) -> bool:
        """
        Удаляет категорию
        Args:
            category_id: ID категории
        Returns:
            bool: True если успешно удалено
        """
        stmt = delete(CompanyCategory).where(CompanyCategory.id == category_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0