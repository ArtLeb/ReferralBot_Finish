from aiogram import Router, F
from aiogram.types import Message
from utils.database.models import User
from services.coupon_service import CouponService
from sqlalchemy.ext.asyncio import AsyncSession
import qrcode
from io import BytesIO

router = Router()

@router.message(F.text == "Получить купон")
async def get_coupon(message: Message, user: User, session: AsyncSession):
    """Генерация нового купона для клиента"""
    coupon_service = CouponService(session)
    
    try:
        coupon = await coupon_service.generate_coupon(
            issuer_id=1,  # Системный пользователь
            client_id=user.id,
            coupon_type_id=1  # Базовый тип купона
        )
        
        # Генерация QR-кода
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(coupon.code)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Отправка изображения
        bio = BytesIO()
        bio.name = f'coupon_{coupon.code}.png'
        img.save(bio, 'PNG')
        bio.seek(0)
        
        await message.answer_photo(
            photo=bio,
            caption=f"🎫 Ваш купон: {coupon.code}\n"
                    f"🔢 Код: {coupon.code}\n"
                    f"📅 Срок действия: до {coupon.end_date}"
        )
    except Exception as e:
        await message.answer("❌ Не удалось создать купон. Попробуйте позже.")

@router.message(F.text == "Мои купоны")
async def my_coupons(message: Message, user: User, session: AsyncSession):
    """Просмотр активных купонов пользователя"""
    coupon_service = CouponService(session)
    coupons = await coupon_service.get_user_coupons(user.id)
    
    if not coupons:
        await message.answer("📭 У вас пока нет активных купонов")
        return
    
    response = "📋 Ваши активные купоны:\n\n"
    for coupon in coupons:
        response += (
            f"🎫 Купон: {coupon.code}\n"
            f"📅 Срок действия: до {coupon.end_date}\n"
            f"🏷️ Статус: {coupon.status.name}\n\n"
        )
    
    await message.answer(response)