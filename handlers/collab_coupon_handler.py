from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from handlers.common_handlers import logger
from services.company_service import CompanyService
from services.coupon_service import CouponService
from utils.bot_obj import bot
from utils.keyboards import main_menu
from utils.states import CreateCouponTypeStates, CollaborationStates
from datetime import datetime

router = Router()


@router.callback_query(F.data.startswith("send_collab_"), CollaborationStates.collab_location_info)
async def start_coupon_type_creation(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    location_id = int(cb.data.split("_")[-1])
    comp_id = data['company_id']

    await state.update_data(
        company_id=comp_id,
        location_id=location_id,
        agent_owner_user_id=data['agent_owner_user_id'],
        agent_agree=False
    )

    await cb.message.answer("💸 Введите процент скидки (например: 15.5):")
    await state.set_state(CreateCouponTypeStates.discount_percent)


@router.message(CreateCouponTypeStates.discount_percent)
async def get_discount_percent(message: Message, state: FSMContext):
    try:
        value = float(message.text)
        if not (0 < value <= 100):
            raise ValueError
        await state.update_data(discount_percent=value)
        await message.answer("💰 Введите процент комиссии (например: 5.0):")
        await state.set_state(CreateCouponTypeStates.commission_percent)
    except:
        await message.answer("❌ Введите корректное число от 0 до 100.")


@router.message(CreateCouponTypeStates.commission_percent)
async def get_commission_percent(message: Message, state: FSMContext):
    try:
        value = float(message.text)
        if not (0 <= value <= 100):
            raise ValueError
        await state.update_data(commission_percent=value)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да", callback_data="groups_yes"),
             InlineKeyboardButton(text="❌ Нет", callback_data="groups_no")]
        ])
        await message.answer("📚 Требуются все группы?", reply_markup=keyboard)
        await state.set_state(CreateCouponTypeStates.require_all_groups)
    except:
        await message.answer("❌ Введите корректное число.")


@router.callback_query(CreateCouponTypeStates.require_all_groups)
async def get_groups(cb: CallbackQuery, state: FSMContext):
    is_required = cb.data == "groups_yes"
    await state.update_data(require_all_groups=is_required)
    await cb.message.answer("🔢 Введите лимит использования купона:")
    await state.set_state(CreateCouponTypeStates.usage_limit)


@router.message(CreateCouponTypeStates.usage_limit)
async def get_usage_limit(message: Message, state: FSMContext):
    try:
        limit = int(message.text)
        await state.update_data(usage_limit=limit)
        await message.answer("📅 Введите дату начала (ДД.ММ.ГГГГ):")
        await state.set_state(CreateCouponTypeStates.start_date)
    except Exception as e:
        print(e)
        await message.answer("❌ Введите целое число.")


@router.message(CreateCouponTypeStates.start_date)
async def get_start_date(message: Message, state: FSMContext):
    try:
        date = datetime.strptime(message.text, "%d.%m.%Y").date()
        await state.update_data(start_date=date.isoformat())
        await message.answer("📅 Введите дату окончания (ДД.ММ.ГГГГ):")
        await state.set_state(CreateCouponTypeStates.end_date)
    except Exception as e:
        print(e)
        await message.answer("❌ Неверный формат даты.")


@router.message(CreateCouponTypeStates.end_date)
async def get_end_date(message: Message, state: FSMContext):
    try:
        date = datetime.strptime(message.text, "%d.%m.%Y").date()
        await state.update_data(end_date=date.isoformat())
        await message.answer("⏳ Введите количество дней для использования купона:")
        await state.set_state(CreateCouponTypeStates.days_for_used)
    except:
        await message.answer("❌ Неверный формат даты.")


@router.message(CreateCouponTypeStates.days_for_used)
async def get_days_for_used(message: Message, state: FSMContext):
    try:
        days = int(message.text)
        await state.update_data(days_for_used=days)

        data = await state.get_data()

        summary = (
            f"<b>Проверьте данные купона:</b>\n"
            f"💸 Скидка: {data['discount_percent']}%\n"
            f"💰 Комиссия: {data['commission_percent']}%\n"
            f"📚 Все группы: {'Да' if data['require_all_groups'] else 'Нет'}\n"
            f"🔢 Лимит: {data['usage_limit']}\n"
            f"📅 Даты: {data['start_date']} — {data['end_date']}\n"
            f"⏳ Дней на использование: {data['days_for_used']}\n\n"
            f"✅ Подтвердите создание купона."
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_coupon_type")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_coupon_type")]
        ])

        await message.answer(summary, reply_markup=keyboard, parse_mode="HTML")
        await state.set_state(CreateCouponTypeStates.confirm)
    except Exception as e:
        await message.answer("❌ Введите целое число.")


@router.callback_query(CreateCouponTypeStates.confirm, F.data == "confirm_coupon_type")
async def confirm_coupon_type(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    coupon_service = CouponService(session)
    start_date = datetime.fromisoformat(data["start_date"]).date()
    end_date = datetime.fromisoformat(data["end_date"]).date()

    coupon = await coupon_service.create_coupon_type(
        company_id=data["my_company_id"],
        location_id=data["my_location_id"],
        discount_percent=data["discount_percent"],
        commission_percent=data["commission_percent"],
        require_all_groups=data["require_all_groups"],
        usage_limit=data["usage_limit"],
        start_date=start_date,
        end_date=end_date,
        company_agent_id=data["agent_company_id"],
        location_agent_id=data["agent_location_id"],
        days_for_used=data["days_for_used"],
    )

    await cb.message.answer("🎉 Купон успешно создан!")
    await cb.message.delete()
    await cb.message.answer(
        "👋 Добро пожаловать в ReferralBot!",
        reply_markup=await main_menu(session, cb.message.from_user.id)
    )
    await state.clear()

    agent_user_id = data.get("agent_owner_user_id")
    if not agent_user_id:
        return
    comp_service = CompanyService(session)

    my_location = await comp_service.get_location_by_id(data["location_id"])
    my_company = await comp_service.get_company_by_id(data["company_id"])

    agent_location = await comp_service.get_location_by_id(data["agent_location_id"])
    agent_company = await comp_service.get_company_by_id(data["agent_company_id"])

    notify_text = (
        f"📣 <b>Новая заявка на коллаборацию!</b>\n\n"

        f"👤 <b>Компания-заявитель</b>\n"
        f"🏢 <b>Название:</b> {my_company.Name_comp}\n"
        # f"📍 <b>Локация:</b> {my_location.name_loc}\n"
        f"💸 <b>Скидка:</b> {coupon.discount_percent}%\n"
        f"💼 <b>Комиссия:</b> {coupon.commission_percent}%\n"
        f"📅 <b>Период действия:</b> {coupon.start_date.strftime('%d.%m.%Y')} – {coupon.end_date.strftime('%d.%m.%Y')}\n"
        f"🔢 <b>Лимит использований:</b> {coupon.usage_limit}\n"
        f"⏱️ <b>Дней на использование:</b> {coupon.days_for_used}\n"
        f"🆔 <b>Код купона:</b> <code>{coupon.code_prefix}</code>\n\n"

        f"🛡 <b>Ваша компания</b>\n"
        f"🏢 <b>Название:</b> {agent_company.Name_comp}\n"

        f"<i>Пожалуйста, подтвердите или отклоните предложение.</i>"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Подтвердить",
                callback_data=f"req_collab_confirm_{cb.from_user.id}_{coupon.id_coupon_type}"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Отклонить",
                callback_data=f"req_collab_reject_{cb.from_user.id}_{coupon.id_coupon_type}"
            )
        ]
    ])

    try:
        await bot.send_message(
            chat_id=agent_user_id,
            text=notify_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления агенту: {e}")


@router.callback_query(CreateCouponTypeStates.confirm, F.data == "cancel_coupon_type")
async def cancel_coupon_type(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text("❌ Создание купона отменено.")
