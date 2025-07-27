from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from utils.database.models import TgGroup
from typing import List, Optional

class TgGroupService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_groups_by_company(self, company_id: int) -> List[TgGroup]:
        """Получает все группы для указанной компании"""
        stmt = select(TgGroup).where(TgGroup.company_id == company_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_group_by_id(self, group_id: int) -> Optional[TgGroup]:
        """Получает группу по ID"""
        return await self.session.get(TgGroup, group_id)

    async def create_group(
        self,
        group_id: int,
        name: str,
        company_id: int,
        is_active: bool = True
    ) -> TgGroup:
        """Создает новую группу и привязывает к компании"""
        group = TgGroup(
            group_id=group_id,
            name=name,
            company_id=company_id,
            is_active=is_active
        )
        self.session.add(group)
        await self.session.commit()
        return group

    async def delete_group(self, group_id: int, company_id: int) -> bool:
        """Удаляет группу с проверкой принадлежности компании"""
        # Проверяем существование группы и принадлежность компании
        group = await self.session.get(TgGroup, group_id)
        if not group or group.company_id != company_id:
            return False
        
        await self.session.delete(group)
        await self.session.commit()
        return True