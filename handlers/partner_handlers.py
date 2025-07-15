from aiogram import Router, F
from aiogram.types import Message
from utils.database.models import User
from services.coupon_service import CouponService
from sqlalchemy.ext.asyncio import AsyncSession

router = Router()

@router.message(F.text == "Сгенерировать купон")
async def generate_coupon(message: Message, user: User, session: AsyncSession):
    coupon_service = CouponService(session)
    coupon = await coupon_service.generate_coupon(
        issuer_id=user.id,
        client_id=user.id,
        coupon_type_id=1
    )
    await message.answer(f"🎫 Ваш купон: {coupon.code}")

@router.message(F.text == "Мои администраторы")
async def my_admins(message: Message):
    await message.answer("👥 Список ваших администраторов...")