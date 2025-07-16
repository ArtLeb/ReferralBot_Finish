from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from utils.database.models import CouponType

class CouponTypeRepository:
    """Репозиторий для работы с типами купонов"""
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_coupon_type(self, coupon_type_data: dict) -> CouponType:
        """
        Создает новый тип купона
        Args:
            coupon_type_data: Данные типа купона
        Returns:
            CouponType: Созданный тип купона
        """
        coupon_type = CouponType(**coupon_type_data)
        self.session.add(coupon_type)
        await self.session.commit()
        await self.session.refresh(coupon_type)
        return coupon_type
    
    async def get_coupon_type_by_id(self, type_id: int) -> CouponType:
        """
        Получает тип купона по ID
        Args:
            type_id: ID типа купона
        Returns:
            CouponType: Объект типа купона
        """
        return await self.session.get(CouponType, type_id)
    
    async def get_coupon_type_by_prefix(self, prefix: str) -> CouponType:
        """
        Получает тип купона по префиксу
        Args:
            prefix: Префикс кода купона
        Returns:
            CouponType: Объект типа купона
        """
        stmt = select(CouponType).where(CouponType.code_prefix == prefix)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_coupon_types_by_company(self, company_id: int) -> list[CouponType]:
        """
        Получает типы купонов компании
        Args:
            company_id: ID компании
        Returns:
            list[CouponType]: Список типов купонов
        """
        stmt = select(CouponType).where(CouponType.company_id == company_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def update_coupon_type(self, type_id: int, update_data: dict) -> CouponType:
        """
        Обновляет данные типа купона
        Args:
            type_id: ID типа купона
            update_data: Данные для обновления
        Returns:
            CouponType: Обновленный тип купона
        """
        stmt = (
            update(CouponType)
            .where(CouponType.id_coupon_type == type_id)
            .values(**update_data)
            .returning(CouponType)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one()
    
    async def delete_coupon_type(self, type_id: int) -> bool:
        """
        Удаляет тип купона
        Args:
            type_id: ID типа купона
        Returns:
            bool: True если успешно удалено
        """
        stmt = delete(CouponType).where(CouponType.id_coupon_type == type_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0