from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from utils.database.models import Company

class CompanyRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_company_by_id(self, company_id: int) -> Company:
        """
        Получает компанию по ID
        
        Args:
            company_id: ID компании
            
        Returns:
            Company: Объект компании или None
        """
        result = await self.session.execute(
            select(Company).where(Company.id_comp == company_id))
        return result.scalar_one_or_none()
    
    async def create_company(self, company: Company) -> Company:
        """
        Создает новую компанию в базе данных
        
        Args:
            company: Объект компании для создания
            
        Returns:
            Company: Созданный объект компании
        """
        self.session.add(company)
        await self.session.commit()
        await self.session.refresh(company)
        return company