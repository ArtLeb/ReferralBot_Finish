import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import select
from repositories.coupon_repository import CouponRepository
from utils.database.models import Coupon, CouponType, CouponStatus

class CouponService:
    """Сервис для работы с купонами"""
    
    def __init__(self, session):
        self.session = session
        self.coupon_repo = CouponRepository(session)
    
    async def generate_coupon(self, issuer_id: int, client_id: int, coupon_type_id: int) -> Coupon:
        """
        Генерирует новый купон
        
        Args:
            issuer_id: ID пользователя, выдающего купон
            client_id: ID клиента, получающего купон
            coupon_type_id: ID типа купона
        
        Returns:
            Coupon: Созданный купон
        """
        # Получение типа купона
        coupon_type = await self.session.get(CouponType, coupon_type_id)
        if not coupon_type:
            raise ValueError("Тип купона не найден")
        
        # Убрана проверка подписки на группы (временно)
        
        # Генерация уникального кода
        code = f"{coupon_type.code_prefix}-{uuid.uuid4().hex[:8].upper()}"
        
        # Создание купона
        coupon = Coupon(
            code=code,
            coupon_type_id=coupon_type_id,
            client_id=client_id,
            start_date=datetime.now().date(),
            end_date=datetime.now().date() + timedelta(days=coupon_type.days_for_used),
            issued_by=issuer_id,
            status_id=CouponStatus.get_status_id("active")
        )
        
        self.session.add(coupon)
        await self.session.commit()
        return coupon
    
    async def redeem_coupon(self, coupon_code: str, redeemed_by: int, amount: Decimal) -> Coupon:
        """
        Активирует (погашает) купон
        
        Args:
            coupon_code: Код купона
            redeemed_by: ID пользователя, активировавшего купон
            amount: Сумма покупки
        
        Returns:
            Coupon: Обновленный купон
        """
        coupon = await self.coupon_repo.get_coupon_by_code(coupon_code)
        if not coupon:
            raise ValueError("Купон не найден")
        
        # Проверка статуса
        if coupon.status_id != CouponStatus.get_status_id("active"):
            raise ValueError("Купон не активен")
        
        # Проверка срока действия
        if coupon.end_date < datetime.now().date():
            coupon.status_id = CouponStatus.get_status_id("expired")
            await self.session.commit()
            raise ValueError("Срок действия купона истек")
        
        # Обновление данных купона
        coupon.used_by = redeemed_by
        coupon.used_at = datetime.now()
        coupon.order_amount = amount
        coupon.status_id = CouponStatus.get_status_id("used")
        
        await self.session.commit()
        return coupon
    
    async def get_user_coupons(self, user_id: int) -> list[Coupon]:
        """
        Получает купоны пользователя
        
        Args:
            user_id: ID пользователя
        
        Returns:
            list[Coupon]: Список купонов
        """
        stmt = select(Coupon).where(
            (Coupon.client_id == user_id) &
            (Coupon.status_id == CouponStatus.get_status_id("active"))
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def create_coupon_type(
        self,
        company_id: int,
        discount_percent: Decimal,
        days_valid: int = 30
    ) -> CouponType:
        """
        Создает новый тип купона
        
        Args:
            company_id: ID компании
            discount_percent: Процент скидки
            days_valid: Срок действия в днях
        
        Returns:
            CouponType: Созданный тип купона
        """
        code_prefix = f"CPN-{company_id}-{str(int(discount_percent))}"
        coupon_type = CouponType(
            code_prefix=code_prefix,
            company_id=company_id,
            discount_percent=discount_percent,
            commission_percent=Decimal('5.0'),  # Стандартная комиссия
            require_all_groups=False,
            usage_limit=0,
            start_date=datetime.now().date(),
            end_date=datetime.now().date() + timedelta(days=365),
            days_for_used=days_valid,
            agent_agree=True
        )
        
        self.session.add(coupon_type)
        await self.session.commit()
        return coupon_type