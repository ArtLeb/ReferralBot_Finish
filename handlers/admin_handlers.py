from aiogram import Bot, Router, F
from aiogram.types import Message
from utils.database.models import User
from services.coupon_service import CouponService
from sqlalchemy.ext.asyncio import AsyncSession

router = Router()

@router.message(F.text == "Активировать купон")
async def activate_coupon(message: Message, session: AsyncSession):
    await message.answer("Введите код купона:")
    # Здесь нужно установить состояние для ожидания кода

@router.message(F.text == "Проверить подписку")
async def check_subscription(message: Message, bot: Bot, user: User):
    # Проверка подписки пользователя на группы
    await message.answer("🔍 Проверяем ваши подписки...")