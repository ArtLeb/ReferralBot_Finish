from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from services.action_logger import CityLogger
from services.category_service import CategoryService
from services.company_service import CompanyService
from services.role_service import RoleService
from utils.collab_helper import handle_pagination, filter_categories, filter_cities, comp_locations, loc_info_text, \
    collab_action_keyboard
from utils.keyboards import coupon_menu_keyboard, loc_comp_keyboard, loc_categories_keyboard, loc_city_keyboard, \
    comp_location_keyboard
from utils.states import PartnerStates, CollaborationStates, CreateLocationStates

router = Router()


@router.message(PartnerStates.select_location_action, F.text == "Коллаборации")
async def start_collab_menu(message: Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Я выдаю купоны", callback_data='iam_coupon'))
    builder.row(InlineKeyboardButton(text="Я агент", callback_data='iam_agent'))
    builder.row(InlineKeyboardButton(text="Мои Коллаборации", callback_data='my_collabs'))
    builder.adjust(2)

    await message.answer(
        text='Выберите свою роль в коллаборации',
        reply_markup=builder.as_markup()
    )
    await state.set_state(CollaborationStates.collab_menu)


@router.callback_query(CollaborationStates.collab_menu)
async def select_collab_menu(cb: CallbackQuery, state: FSMContext):
    if cb.data == 'my_collabs':
        pass

    keyboard = coupon_menu_keyboard(cb_data=cb.data)
    await cb.message.edit_text(
        text='🕓 Выберите действие',
        reply_markup=keyboard
    )
    await state.set_state(CollaborationStates.filter_comp_start_menu)
    await state.update_data(filter_selected_city=[], filter_selected_category=[])


@router.callback_query(CollaborationStates.filter_comp_start_menu, F.data == 'iam_coupon_search')
async def search_collab(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    comp_service = CompanyService(session)

    selected_cities = data.get('filter_selected_city', [])
    selected_categories = data.get('filter_selected_category', [])

    current_page = data.get('current_page', 0)

    comp_list = await comp_service.get_companies_filtered_by_loc(
        city=selected_cities,
        category=selected_categories
    )

    keyboard = loc_comp_keyboard(
        companies=comp_list,
        page=current_page,
        selected_companies=data.get('selected_companies', [])
    )

    await cb.message.edit_text(
        text='Выберите компанию для коллаборации',
        reply_markup=keyboard
    )
    await state.set_state(CollaborationStates.filter_comp_menu)


@router.callback_query(CollaborationStates.filter_comp_menu)
async def handle_company_pagination(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    if cb.data.startswith('page_'):
        await handle_pagination(cb, state, session)
    elif cb.data.startswith('company_'):
        await comp_locations(cb, state, session)
    elif cb.data == 'filter_clear':
        await state.update_data(filter_selected_city=[], filter_selected_category=[], current_page=0)
        comp_service = CompanyService(session)
        comp_list = await comp_service.get_companies_filtered_by_loc(city=[], category=[])

        keyboard = loc_comp_keyboard(companies=comp_list, page=0, selected_companies=[])

        await cb.message.edit_reply_markup(reply_markup=keyboard)
        await handle_pagination(cb, state, session)
    elif cb.data == 'filter_category':
        await filter_categories(cb, state, session)
    elif cb.data == 'filter_city':
        await filter_cities(cb, state, session)
    elif cb.data == 'filter_back':
        await cb.message.delete()
        await start_collab_menu(message=cb.message, state=state)


@router.callback_query(CollaborationStates.choose_location)
async def paginate_location(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    company_id = data['company_id']
    comp_service = CompanyService(session)
    role_service = RoleService(session)
    if cb.data.startswith('page_'):
        new_page = int(cb.data.split('_')[1])
        locations = await comp_service.get_locations_by_company(company_id=company_id)
        keyboard = comp_location_keyboard(locations=locations, page=new_page)

        await cb.message.edit_text(text="Выберите локацию", reply_markup=keyboard)

        await state.update_data(company_id=company_id)

    elif cb.data == 'location_back':
        await search_collab(cb=cb, state=state, session=session)

    if cb.data.startswith('location_'):
        location_id = int(cb.data.split('_')[1])
        loc_info = await comp_service.get_location_by_id(location_id=location_id)
        comp_info = await comp_service.get_company_by_id(company_id=company_id)
        owner_info = await role_service.get_comp_owner(company_id=company_id, loc_id=location_id)

        await cb.message.edit_text(
            text=loc_info_text(comp=comp_info, loc=loc_info, owner=owner_info),
            reply_markup=collab_action_keyboard(comp_id=company_id)
        )

        await state.update_data(
            location_id=location_id,
            agent_owner_user_id=owner_info.id_tg,
            agent_owner_id=owner_info.id_tg)

        await state.set_state(CollaborationStates.collab_location_info)


@router.callback_query(CollaborationStates.collab_location_info, F.data == 'collab_back')
async def process_city_selection(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    await search_collab(cb=cb, state=state, session=session)


@router.callback_query(CreateLocationStates.get_loc_city)
async def process_city_selection(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Обработка выбора городов"""
    data = await state.get_data()
    selected_cities: list = data.get('filter_selected_city', [])
    current_page: int = data.get('current_page', 0)

    if cb.data.startswith('city_'):
        city_id = int(cb.data.split('_')[1])
        if city_id in selected_cities:
            selected_cities.remove(city_id)
        else:
            selected_cities.append(city_id)

        await state.update_data(filter_selected_city=selected_cities)

        city_service = CityLogger(session)
        cities = await city_service.get_all_cities()
        keyboard = loc_city_keyboard(cities, selected_cities, current_page)

        await cb.message.edit_reply_markup(reply_markup=keyboard)

    elif cb.data.startswith('page_'):
        new_page = int(cb.data.split('_')[1])
        await state.update_data(current_page=new_page)

        city_service = CityLogger(session)
        cities = await city_service.get_all_cities()
        keyboard = loc_city_keyboard(cities, selected_cities, new_page)

        await cb.message.edit_reply_markup(reply_markup=keyboard)

    elif cb.data == 'add_city':
        if not selected_cities:
            await cb.answer(text="Выберите хотя бы один город!", show_alert=True)
            return

        await state.set_state(CollaborationStates.filter_comp_menu)
        await search_collab(cb=cb, state=state, session=session)
    elif cb.data == 'back_city':
        await state.update_data(filter_selected_city=[])
        await state.set_state(CollaborationStates.filter_comp_menu)
        await search_collab(cb=cb, state=state, session=session)


@router.callback_query(CreateLocationStates.get_loc_category)
async def process_category_selection(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Обработка выбора категорий"""
    data = await state.get_data()
    selected_categories: list = data.get('filter_selected_category', [])
    current_page: int = data.get('current_page', 0)

    if cb.data.startswith('category_'):
        category_id = int(cb.data.split('_')[1])
        if category_id in selected_categories:
            selected_categories.remove(category_id)
        else:
            selected_categories.append(category_id)

        await state.update_data(filter_selected_category=selected_categories)

        category_service = CategoryService(session)
        categories = await category_service.get_all_categories()
        keyboard = loc_categories_keyboard(categories, selected_categories, current_page)

        await cb.message.edit_reply_markup(reply_markup=keyboard)

    elif cb.data.startswith('page_'):
        new_page = int(cb.data.split('_')[1])
        await state.update_data(current_page=new_page)

        category_service = CategoryService(session)
        categories = await category_service.get_all_categories()
        keyboard = loc_categories_keyboard(categories, selected_categories, new_page)

        await cb.message.edit_reply_markup(reply_markup=keyboard)

    elif cb.data == 'add_category':
        if not selected_categories:
            await cb.answer(text="Выберите хотя бы одну категорию!", show_alert=True)
            return

        await state.set_state(CollaborationStates.filter_comp_menu)
        await search_collab(cb=cb, state=state, session=session)

    elif cb.data == 'back_category':
        await state.set_state(CollaborationStates.filter_comp_menu)
        await search_collab(cb=cb, state=state, session=session)
