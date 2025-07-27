from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from services.action_logger import CityLogger
from services.category_service import CategoryService
from services.company_service import CompanyService
from utils.database.models import Company, CompLocation, User
from utils.keyboards import loc_comp_keyboard, loc_categories_keyboard, loc_city_keyboard, comp_location_keyboard
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
        await cb.answer(f"Ошибка: {str(e)}", show_alert=True)


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
    city_service = CityLogger(session)
    cities = await city_service.get_all_cities()
    keyboard = loc_city_keyboard(cities, selected_cities=[])

    await cb.message.edit_text(
        text="✍️ Введите Город",
        reply_markup=keyboard
    )
    await state.update_data(filter_selected_city=[], current_page=0)
    await state.set_state(CreateLocationStates.get_loc_city)


async def comp_locations(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    try:
        company_id = int(cb.data.split('_')[1])
        comp_service = CompanyService(session)
        locations = await comp_service.get_locations_by_company(company_id=company_id)
        keyboard = comp_location_keyboard(locations=locations)

        await cb.message.edit_text(text="Выберите локацию", reply_markup=keyboard)

        await state.update_data(company_id=company_id)
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
