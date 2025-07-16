from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from utils.database.models import Company

class CompanyRepository:
    """Репозиторий для работы с компаниями"""
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_company(self, company_data: dict) -> Company:
        """
        Создает новую компанию
        Args:
            company_data: Данные компании
        Returns:
            Company: Созданная компания
        """
        company = Company(**company_data)
        self.session.add(company)
        await self.session.commit()
        await self.session.refresh(company)
        return company
    
    async def get_company_by_id(self, company_id: int) -> Company:
        """
        Получает компанию по ID
        Args:
            company_id: ID компании
        Returns:
            Company: Объект компании
        """
        return await self.session.get(Company, company_id)
    
    async def get_company_by_name(self, name: str) -> Company:
        """
        Получает компанию по названию
        Args:
            name: Название компании
        Returns:
            Company: Объект компании
        """
        stmt = select(Company).where(Company.Name_comp == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_companies_by_owner(self, owner_id: int) -> list[Company]:
        """
        Получает компании владельца
        Args:
            owner_id: ID владельца
        Returns:
            list[Company]: Список компаний
        """
        stmt = select(Company).where(Company.owner_id == owner_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def update_company(self, company_id: int, update_data: dict) -> Company:
        """
        Обновляет данные компании
        Args:
            company_id: ID компании
            update_data: Данные для обновления
        Returns:
            Company: Обновленная компания
        """
        stmt = (
            update(Company)
            .where(Company.id_comp == company_id)
            .values(**update_data)
            .returning(Company)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one()
    
    async def delete_company(self, company_id: int) -> bool:
        """
        Удаляет компанию
        Args:
            company_id: ID компании
        Returns:
            bool: True если успешно удалено
        """
        stmt = delete(Company).where(Company.id_comp == company_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0