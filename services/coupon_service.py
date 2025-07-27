import uuid
from datetime import datetime, timedelta, date
from decimal import Decimal

from sqlalchemy import select
from repositories.coupon_repository import CouponRepository
from utils.database.models import Coupon, CouponType, CouponStatus
from services.group_service import GroupService


class CouponService:
    """Сервис для работы с купонами"""

    def __init__(self, session):
        self.session = session
        self.coupon_repo = CouponRepository(session)
        self.group_service = GroupService(session)

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

        # Проверка подписки на группы (если требуется)
        if coupon_type.require_all_groups:
            if not await self.group_service.check_user_subscription(client_id, coupon_type_id):
                raise ValueError("Пользователь не подписан на все требуемые группы")

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
            location_id: int,
            discount_percent: Decimal,
            commission_percent: Decimal,
            require_all_groups: bool,
            usage_limit: int,
            start_date: date,
            end_date: date,
            company_agent_id: int,
            location_agent_id: int,
            days_for_used: int,
    ) -> CouponType:
        """
        Асинхронно создает новый тип купона в базе данных.

        Args:
            company_id (int): ID компании, к которой относится купон.
            location_id (int): ID локации, на которую действует купон.
            discount_percent (Decimal): Процент скидки.
            commission_percent (Decimal): Процент комиссии.
            require_all_groups (bool): Требуются ли все группы для использования купона.
            usage_limit (int): Максимальное количество использований.
            start_date (date): Дата начала действия купона.
            end_date (date): Дата окончания действия купона.
            company_agent_id (int): ID агента компании, создавшего купон.
            location_agent_id (int): ID агента локации, создавшего купон.
            days_for_used (int): Количество дней, в течение которых можно использовать купон.

        Returns:
            CouponType: Объект созданного купона.
        """
        coupon_type = CouponType(
            code_prefix=f"CPN-{company_id}-{int(discount_percent)}",
            company_id=company_id,
            location_id=location_id,
            discount_percent=discount_percent,
            commission_percent=commission_percent,
            require_all_groups=require_all_groups,
            usage_limit=usage_limit,
            start_date=start_date,
            end_date=end_date,
            company_agent_id=company_agent_id,
            location_agent_id=location_agent_id,
            days_for_used=days_for_used,
            agent_agree=False,
        )

        self.session.add(coupon_type)
        await self.session.commit()
        return coupon_type

