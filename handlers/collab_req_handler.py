from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from services.coupon_service import CouponService
from utils.bot_obj import bot

router = Router()


@router.callback_query(F.data.startswith('req_collab_'))
async def req_collab(cb: CallbackQuery, session: AsyncSession):
    status_txt, owner_id, coupon_id = cb.data.split('_')[2:]
    status = True if status_txt == 'confirm' else False

    coupon_service = CouponService(session=session)
    await coupon_service.set_collab_status(coupon_type_id=int(coupon_id), status=status)
    await coupon_service.set_collab_active_status(coupon_type_id=int(coupon_id), status=status)

    text = '✅ Коллаборация подтверждена' if status else '❌ Коллаборация Отклонена'

    await cb.message.delete()
    await cb.answer(text=text)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👌 OK", callback_data="ok")]
    ])

    await bot.send_message(
        chat_id=owner_id,
        text=text,
        reply_markup=keyboard
    )

@router.callback_query(F.data.startswith('ok'))
async def req_collab(cb: CallbackQuery, session: AsyncSession):
    await cb.message.delete()

