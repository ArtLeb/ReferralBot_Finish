from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from utils.states import CouponGen
from services.coupon_service import generate_coupon

router = Router()

@router.message(Command("generate_coupon"))
async def generate_coupon_cmd(message: Message, state: FSMContext, user_roles: list):
    # Проверка прав
    if not any(role.gen_coups for role in user_roles):
        await message.answer("❌ У вас нет прав для создания купонов!")
        return
    
    await state.set_state(CouponGen.enter_discount)
    await message.answer(
        "🎫 Создание нового купона:\n\n"
        "💯 Введите размер скидки (в процентах):"
    )

@router.message(CouponGen.enter_discount, F.text.regexp(r'^\d{1,3}$'))
async def process_discount(message: Message, state: FSMContext):
    discount = int(message.text)
    await state.update_data(discount=discount)
    await state.set_state(CouponGen.enter_commission)
    await message.answer(
        f"✅ Скидка установлена: {discount}%\n\n"
        "🏦 Введите размер комиссии (в процентах):"
    )

@router.callback_query(F.data.startswith("coupon_confirm"))
async def confirm_coupon(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    coupon = await generate_coupon(
        discount=data['discount'],
        commission=data['commission'],
        creator_id=callback.from_user.id
    )
    
    await callback.message.answer(
        f"🎉 Купон успешно создан!\n\n"
        f"🔖 Код: {coupon.coup_code}\n"
        f"💯 Скидка: {coupon.discount}%\n"
        f"🏦 Комиссия: {coupon.commission}%\n"
        f"📅 Действует до: {coupon.endda}"
    )
    await state.clear()