from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from utils.database.models import Coupon, CouponType

class CouponRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_coupon(self, coupon_data: dict) -> Coupon:
        coupon = Coupon(**coupon_data)
        self.session.add(coupon)
        await self.session.commit()
        return coupon

    async def get_coupon_by_code(self, code: str) -> Coupon:
        result = await self.session.execute(
            select(Coupon).where(Coupon.code == code)
        )
        return result.scalar_one_or_none()

    async def get_coupon_type_by_prefix(self, prefix: str) -> CouponType:
        result = await self.session.execute(
            select(CouponType).where(CouponType.code_prefix == prefix)
        )
        return result.scalar_one_or_none()