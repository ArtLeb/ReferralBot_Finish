import logging
from typing import Tuple

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from services.action_logger import CityLogger
from services.category_service import CategoryService
from services.company_service import CompanyService
from services.coupon_service import CouponService
from utils.database.models import Company, CompLocation, User
from utils.keyboards import loc_comp_keyboard, loc_categories_keyboard, loc_city_keyboard, comp_location_keyboard, \
    collab_comp_keyboard, collab_request_keyboard
from utils.states import CreateLocationStates, CollaborationStates


async def handle_pagination(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    try:
        data = await state.get_data()
        new_page = int(cb.data.split('_')[1])

        comp_service = CompanyService(session)
        comp_list = await comp_service.get_companies_filtered_by_loc(
            city=data.get('filter_selected_city', []),
            category=data.get('filter_selected_category', [])
        )

        keyboard = loc_comp_keyboard(
            companies=comp_list, page=new_page,
            selected_companies=data.get('selected_companies', [])
        )

        await state.update_data(current_page=new_page)
        await cb.message.edit_reply_markup(reply_markup=keyboard)
    except Exception as e:
        logging.error(f"Ошибка: {str(e)}", show_alert=True)


async def filter_categories(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    category_service = CategoryService(session)
    categories = await category_service.get_all_categories()
    keyboard = loc_categories_keyboard(categories, selected_category=[])

    await cb.message.edit_text(
        text="✍️ Введите Категории",
        reply_markup=keyboard
    )
    await state.update_data(filter_selected_category=[], current_page=0)
    await state.set_state(CreateLocationStates.get_loc_category)


async def filter_cities(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    city_service = CityLogger(session)
    cities = await city_service.get_all_cities()
    keyboard = loc_city_keyboard(cities, selected_cities=data.get('filter_selected_city', []))

    await cb.message.edit_text(
        text="✍️ Введите Город",
        reply_markup=keyboard
    )
    await state.update_data(filter_selected_city=[], current_page=0)
    await state.set_state(CreateLocationStates.get_filter_loc_city)


async def comp_locations(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    try:
        company_id = int(cb.data.split('_')[1])
        comp_service = CompanyService(session)
        locations = await comp_service.get_locations_by_company(company_id=company_id)
        keyboard = comp_location_keyboard(locations=locations)

        await cb.message.edit_text(text="Выберите локацию", reply_markup=keyboard)

        await state.update_data(agent_company_id=company_id)
        await state.set_state(CollaborationStates.choose_location)
    except Exception as e:
        await cb.answer(f"Ошибка: {str(e)}", show_alert=True)


def loc_info_text(comp: Company, loc: CompLocation, owner: User) -> str:
    return (
        f"🏢 <b>Компания:</b> {comp.Name_comp}\n"
        f"📍 <b>Локация:</b> {loc.name_loc}\n"
        f"🌆 <b>Город:</b> {loc.city}\n"
        f"🗺️ <b>Адрес:</b> {loc.address}\n"
        f"🔗 <b>Карта:</b> <a href='{loc.map_url}'>Открыть в картах</a>\n\n"
        f"👤 <b>Владелец:</b> {owner.first_name} {owner.last_name}\n"
        f"🧑‍💼 <b>Username:</b> @{owner.user_name if owner.user_name else '—'}\n"
        f"🆔 <b>Telegram ID:</b> {owner.id_tg}\n"
        f"📞 <b>Телефон:</b> {owner.tel_num}\n"
        f"📅 <b>Регистрация:</b> {owner.reg_date.strftime('%d.%m.%Y')}\n"
        f"🏷️ <b>Роль:</b> {owner.role}"
    )


def collab_action_keyboard(comp_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📩 Отправить предложение",
                callback_data=f"send_collab_{comp_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="collab_back"
            )
        ]
    ])


async def show_collaborations(
        cb: CallbackQuery,
        state: FSMContext,
        session: AsyncSession,
        collab_type: str | list[str],
        current_page: int | None = 0
):
    """Общий метод для отображения коллабораций"""
    data = await state.get_data()

    coupon_service = CouponService(session)
    collaborations = await coupon_service.get_collaborations(
        role=collab_type,
        comp_id=data['company_id']
    )

    # Сохраняем в контекст
    await state.update_data(
        current_page=current_page,
        collab_type=collab_type
    )

    return collab_comp_keyboard(collabs=collaborations)


async def collaborations_requests(
        state: FSMContext,
        session: AsyncSession,
        current_page: int | None = 0
):
    """Общий метод для отображения коллабораций"""
    data = await state.get_data()
    coupon_service = CouponService(session)
    collaborations = await coupon_service.get_collaboration_requests(
        company_id=data['company_id'],
        location_id=data['location_id']
    )
    # Сохраняем в контекст
    await state.update_data(current_page=current_page)

    return collab_request_keyboard(collabs=collaborations)


async def collab_info(coupon_id: int, company_id: int, session: AsyncSession) -> Tuple[str, InlineKeyboardMarkup]:
    coupon_service = CouponService(session)
    coupon_info, agent_loc_info = await coupon_service.get_collaboration_info(coupon_id=coupon_id)
    builder = InlineKeyboardBuilder()
    builder.row(*[InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"collab_confirm_{coupon_id}")])
    builder.row(*[InlineKeyboardButton(text="❌ Отклонить", callback_data=f"collab_stop_{coupon_id}")])
    builder.row(*[InlineKeyboardButton(text="⬅️ Назад", callback_data="back_my_collab")])

    if coupon_info.location_agent_id == company_id:
        company_name = coupon_info.company.Name_comp
    else:
        company_name = agent_loc_info.company.Name_comp



    if coupon_info is None:
        text = "❌ Коллаборация не найдена."
    else:
        text = f"""
    🎟 <b>Информация о коллаборации</b>

    🔑 <b>Код:</b> <code>{coupon_info.code_prefix}</code>
    📅 <b>Период действия:</b> {coupon_info.start_date.strftime("%d.%m.%Y")} — {coupon_info.end_date.strftime("%d.%m.%Y")}

    🏢 <b>Компания:</b> {company_name}

    💸 <b>Скидка клиенту:</b> {coupon_info.discount_percent:.2f}%
    🤝 <b>Комиссия агенту:</b> {coupon_info.commission_percent:.2f}%

    🔁 <b>Лимит использований:</b> {'Без ограничений' if coupon_info.usage_limit == 0 else coupon_info.usage_limit}
    📦 <b>Нужно все группы тг:</b> {'Да' if coupon_info.require_all_groups else 'Нет'}
    ⏱ <b>Дней на использование:</b> {coupon_info.days_for_used}

    📬 <b>Согласие агента:</b> {'✅ Да' if coupon_info.agent_agree else '❌ Нет'}
    📌 <b>Активна:</b> {'🟢 Да' if coupon_info.is_active else '🔴 Нет'}
        """.strip()
    return text, builder.as_markup()


async def collab_stop(coupon_id: int, session: AsyncSession) -> bool:
    coupon_service = CouponService(session)
    coupon_info = await coupon_service.terminate_collaboration(coupon_type_id=coupon_id)
    return coupon_info is not None
