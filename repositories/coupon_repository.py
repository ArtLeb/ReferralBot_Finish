from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from utils.database.models import Coupon
from datetime import date

class CouponRepository:
    """Репозиторий для работы с купонами"""
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_coupon(self, coupon_data: dict) -> Coupon:
        """
        Создает новый купон
        Args:
            coupon_data: Данные купона
        Returns:
            Coupon: Созданный купон
        """
        coupon = Coupon(**coupon_data)
        self.session.add(coupon)
        await self.session.commit()
        await self.session.refresh(coupon)
        return coupon
    
    async def get_coupon_by_id(self, coupon_id: int) -> Coupon:
        """
        Получает купон по ID
        Args:
            coupon_id: ID купона
        Returns:
            Coupon: Объект купона
        """
        return await self.session.get(Coupon, coupon_id)
    
    async def get_coupon_by_code(self, code: str) -> Coupon:
        """
        Получает купон по коду
        Args:
            code: Код купона
        Returns:
            Coupon: Объект купона
        """
        stmt = select(Coupon).where(Coupon.code == code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_coupons(self, user_id: int) -> list[Coupon]:
        """
        Получает купоны пользователя
        Args:
            user_id: ID пользователя
        Returns:
            list[Coupon]: Список купонов
        """
        stmt = select(Coupon).where(Coupon.client_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_active_coupons(self) -> list[Coupon]:
        """
        Получает активные купоны
        Returns:
            list[Coupon]: Список активных купонов
        """
        today = date.today()
        stmt = select(Coupon).where(
            (Coupon.start_date <= today) &
            (Coupon.end_date >= today) &
            (Coupon.status_id == 1)  # Статус "Активен"
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def update_coupon(self, coupon_id: int, update_data: dict) -> Coupon:
        """
        Обновляет данные купона
        Args:
            coupon_id: ID купона
            update_data: Данные для обновления
        Returns:
            Coupon: Обновленный купон
        """
        stmt = (
            update(Coupon)
            .where(Coupon.id_coupon == coupon_id)
            .values(**update_data)
            .returning(Coupon)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one()
    
    async def delete_coupon(self, coupon_id: int) -> bool:
        """
        Удаляет купон
        Args:
            coupon_id: ID купона
        Returns:
            bool: True если успешно удалено
        """
        stmt = delete(Coupon).where(Coupon.id_coupon == coupon_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0