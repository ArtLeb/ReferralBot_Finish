import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from services.action_logger import CityLogger
from services.category_service import CategoryService
from services.company_service import CompanyService
from services.coupon_service import CouponService
from services.role_service import RoleService

from utils.collab_helper import handle_pagination, filter_categories, filter_cities, loc_info_text, \
    collab_action_keyboard, show_collaborations, collab_info, collab_stop, collaborations_requests
from utils.keyboards import coupon_menu_keyboard, loc_comp_keyboard, loc_categories_keyboard, loc_city_keyboard, \
    locations_keyboard
from utils.states import PartnerStates, CollaborationStates, CreateLocationStates

router = Router()


@router.message(PartnerStates.company_menu, F.text == "Коллаборации")
async def start_collab_menu(message: Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Я выдаю купоны", callback_data='iam_coupon'))
    builder.row(InlineKeyboardButton(text="Я агент", callback_data='iam_agent'))
    builder.row(InlineKeyboardButton(text="Мои Коллаборации", callback_data='my_collabs'))
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="Назад", callback_data='back'))

    await message.answer(
        text='Выберите свою роль в коллаборации',
        reply_markup=builder.as_markup()
    )
    await state.set_state(CollaborationStates.collab_menu)


@router.callback_query(CollaborationStates.collab_menu)
async def select_collab_menu(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    if cb.data == 'my_collabs':
        keyboard = await show_collaborations(
            cb, state, session, ['partner', 'admin']
        )
        await cb.message.edit_text(
            text='🕓 Выберите действие',
            reply_markup=keyboard
        )
        await state.set_state(CollaborationStates.my_collabs)
    elif cb.data == 'iam_coupon':
        keyboard = coupon_menu_keyboard(cb_data=str(cb.data))
        await cb.message.edit_text(
            text='🕓 Выберите действие',
            reply_markup=keyboard
        )
        await state.set_state(CollaborationStates.filter_comp_start_menu)
        await state.update_data(filter_selected_city=[], filter_selected_category=[])

    elif cb.data == 'iam_agent':
        keyboard = coupon_menu_keyboard(cb_data=str(cb.data))
        await cb.message.edit_text(
            text='🕓 Выберите действие',
            reply_markup=keyboard
        )
        await state.set_state(CollaborationStates.iam_agnt_menu)
    elif cb.data == 'back':
        service = CompanyService(session)
        locations = await service.get_locations_by_company(data['company_id'])

        if not locations:
            await cb.message.answer("В этой компании пока нет локаций")
            return

        await cb.message.edit_text(
            "📍 Локации компании:",
            reply_markup=locations_keyboard(locations)
        )
        await state.set_state(PartnerStates.company_menu)


@router.callback_query(CollaborationStates.my_collabs)
async def select_my_collabs(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    if cb.data.startswith('my_collab_'):
        coupon_id = int(cb.data.split('_')[-1])
        await state.update_data(coupon_id=coupon_id)
        data = await state.get_data()
        text, keyboard = await collab_info(session=session, coupon_id=coupon_id, company_id=data['company_id'])
        await cb.message.edit_text(
            text=text,
            reply_markup=keyboard
        )

    elif cb.data.startswith('collab_stop_'):
        coupon_id = int(cb.data.split('_')[-1])
        text = await collab_stop(session=session, coupon_id=coupon_id)
        await cb.answer(text='Остановлено' if text else 'Не удалось остановаить')

        await state.update_data(current_page=0)
        keyboard = await show_collaborations(
            session=session, collab_type=['partner', 'admin'],
            cb=cb, state=state, current_page=0)
        await cb.message.edit_text(
            text='🕓 Выберите действие',
            reply_markup=keyboard
        )


    elif cb.data.startswith('page_'):
        new_page = int(cb.data.split('_')[1])
        await state.update_data(current_page=new_page)
        keyboard = await show_collaborations(
            session=session, collab_type=['partner', 'admin'],
            cb=cb, state=state, current_page=new_page)
        await cb.message.edit_reply_markup(
            reply_markup=keyboard
        )

    elif cb.data == 'back_my_collab':
        await cb.message.delete()
        await start_collab_menu(message=cb.message, state=state)


@router.callback_query(CollaborationStates.filter_comp_start_menu, F.data == 'iam_coupon_search')
async def iam_coupon_search(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
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


@router.callback_query(CollaborationStates.filter_comp_start_menu, F.data == 'iam_coupon_active_collab')
async def iam_coupon_active_collab(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    keyboard = await show_collaborations(cb, state, session, 'partner')
    await cb.message.edit_text(
        text='🕓 Выберите действие',
        reply_markup=keyboard
    )
    await state.set_state(CollaborationStates.iam_coupon_active_collab)


@router.callback_query(CollaborationStates.iam_coupon_active_collab)
async def search_collab(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    if cb.data.startswith('my_collab_'):
        coupon_id = int(cb.data.split('_')[-1])
        await state.update_data(coupon_id=coupon_id)
        data = await state.get_data()
        text, keyboard = await collab_info(session=session, coupon_id=coupon_id, company_id=data['company_id'])
        await cb.message.edit_text(
            text=text,
            reply_markup=keyboard
        )

    elif cb.data.startswith('collab_stop_'):
        coupon_id = int(cb.data.split('_')[-1])
        text = await collab_stop(session=session, coupon_id=coupon_id)
        await cb.answer(text='Остановлено' if text else 'Не удалось остановаить')

        await state.update_data(current_page=0)

        keyboard = await show_collaborations(
            session=session, collab_type='partner',
            cb=cb, state=state, current_page=0)

        await cb.message.edit_text(
            text='🕓 Выберите действие',
            reply_markup=keyboard
        )


    elif cb.data.startswith('page_'):
        new_page = int(cb.data.split('_')[1])

        await state.update_data(current_page=new_page)

        keyboard = await show_collaborations(
            session=session,
            collab_type='partner',
            cb=cb, state=state,
            current_page=new_page
        )

        await cb.message.edit_reply_markup(reply_markup=keyboard)

    elif cb.data == 'back_my_collab':
        await cb.message.delete()
        await start_collab_menu(message=cb.message, state=state)


@router.callback_query(CollaborationStates.iam_agnt_menu, F.data == 'iam_agent_active')
async def iam_agent_active(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    keyboard = await show_collaborations(cb, state, session, 'agent')
    await cb.message.edit_text(
        text='🕓 Выберите действие',
        reply_markup=keyboard
    )
    await state.set_state(CollaborationStates.iam_coupon_active_collab)


@router.callback_query(CollaborationStates.iam_agnt_menu, F.data == 'iam_agent_requests')
async def iam_agent_requests(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    keyboard = await collaborations_requests(state, session, 0)
    await cb.message.edit_text(
        text='🕓 Выберите действие',
        reply_markup=keyboard
    )
    await state.set_state(CollaborationStates.collab_request)


@router.callback_query(CollaborationStates.collab_request)
async def iam_agent_requests(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    try:
        data = cb.data
        action, *args = data.split('_')
        data = await state.get_data()

        if action == 'collab':
            sub_action = args[0]
            coupon_id = int(args[-1])

            if sub_action == 'req':
                await _handle_collab_request(cb, state, session, coupon_id)
            elif sub_action == 'confirm':
                await _handle_collab_confirm(cb, session, coupon_id, data['company_id'])
            elif sub_action == 'stop':
                await _handle_collab_stop(cb, session, coupon_id)

        elif action == 'page':
            new_page = int(args[0])
            await _handle_page_change(cb, state, session, new_page)

        elif data == 'back_my_collab':
            await _handle_back_to_menu(cb, state)

    except Exception as e:
        logging.error(f"Error in iam_agent_requests: {e}")
        await cb.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")


@router.callback_query(CollaborationStates.iam_agnt_menu)
async def select_my_collabs(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    if cb.data.startswith('my_collab_'):
        coupon_id = int(cb.data.split('_')[-1])
        await state.update_data(coupon_id=coupon_id)
        data = await state.get_data()
        text, keyboard = await collab_info(session=session, coupon_id=coupon_id, company_id=data['company_id'])
        await cb.message.edit_text(
            text=text,
            reply_markup=keyboard
        )

    elif cb.data.startswith('collab_stop_'):
        coupon_id = int(cb.data.split('_')[-1])
        text = await collab_stop(session=session, coupon_id=coupon_id)
        await cb.answer(text='Остановлено' if text else 'Не удалось остановаить')

        await state.update_data(current_page=0)
        keyboard = await show_collaborations(
            session=session, collab_type=['admin'],
            cb=cb, state=state, current_page=0)
        await cb.message.edit_text(
            text='🕓 Выберите действие',
            reply_markup=keyboard
        )

    elif cb.data.startswith('page_'):
        new_page = int(cb.data.split('_')[1])
        await state.update_data(current_page=new_page)
        keyboard = await show_collaborations(
            session=session, collab_type=['admin'],
            cb=cb, state=state, current_page=new_page)
        await cb.message.edit_reply_markup(
            reply_markup=keyboard
        )

    elif cb.data == 'back_my_collab':
        await cb.message.delete()
        await start_collab_menu(message=cb.message, state=state)


@router.callback_query(CollaborationStates.filter_comp_menu)
async def handle_company_pagination(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    if cb.data.startswith('page_'):
        await handle_pagination(cb, state, session)
    elif cb.data.startswith('company_'):
        data = await state.get_data()
        company_id = int(cb.data.replace('company_', ''))
        my_comp_id = data['company_id']
        comp_service = CompanyService(session)
        role_service = RoleService(session)

        loc_info = await comp_service.get_locations_by_company(company_id=company_id, main_loc=True)
        my_loc_info = await comp_service.get_locations_by_company(company_id=my_comp_id, main_loc=True)
        comp_info = await comp_service.get_company_by_id(company_id=company_id)
        owner_info = await role_service.get_comp_owner(company_id=company_id, loc_id=loc_info.id_location)

        await cb.message.edit_text(
            text=loc_info_text(comp=comp_info, loc=loc_info, owner=owner_info),
            reply_markup=collab_action_keyboard(comp_id=company_id)
        )
        await state.update_data(
            agent_owner_user_id=owner_info.id_tg,
            my_location_id=my_loc_info.id_location,
            agent_company_id=company_id,
            agent_location_id=loc_info.id_location
        )
        await state.set_state(CollaborationStates.collab_location_info)

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


@router.callback_query(CollaborationStates.collab_location_info, F.data == 'collab_back')
async def process_city_selection(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    await search_collab(cb=cb, state=state, session=session)


@router.callback_query(CreateLocationStates.get_filter_loc_city)
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
        await iam_coupon_search(session=session, state=state, cb=cb)

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

        await iam_coupon_search(session=session, state=state, cb=cb)

    elif cb.data == 'back_category':
        await state.set_state(CollaborationStates.filter_comp_menu)
        await search_collab(cb=cb, state=state, session=session)


@router.callback_query(F.data == 'back')
async def search_collab(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    await start_collab_menu(message=cb.message, state=state)
    await cb.message.delete()


async def _handle_collab_request(
        cb: CallbackQuery,
        state: FSMContext,
        session: AsyncSession,
        coupon_id: int
):
    await state.update_data(current_page=0)
    data = await state.get_data()
    text, keyboard = await collab_info(session=session, coupon_id=coupon_id, company_id=data['company_id'])
    await _edit_message(cb, text, keyboard)


async def _handle_collab_confirm(
        cb: CallbackQuery,
        session: AsyncSession,
        coupon_id: int,
        company_id: int
):
    coupon_service = CouponService(session)
    await coupon_service.set_collab_status(coupon_id, True)
    text, keyboard = await collab_info(session=session, coupon_id=coupon_id, company_id=company_id)
    await _edit_message(cb, text, keyboard)


async def _handle_collab_stop(
        cb: CallbackQuery,
        session: AsyncSession,
        coupon_id: int
):
    coupon_service = CouponService(session)
    await coupon_service.set_collab_status(coupon_id, False)
    await coupon_service.set_collab_active_status(coupon_id, False)
    text, keyboard = await collab_info(coupon_id=coupon_id, session=session)
    await _edit_message(cb, text, keyboard)


async def _handle_page_change(
        cb: CallbackQuery,
        state: FSMContext,
        session: AsyncSession,
        new_page: int
):
    await state.update_data(current_page=new_page)
    keyboard = await show_collaborations(
        session=session,
        collab_type=['admin'],
        cb=cb,
        state=state,
        current_page=new_page
    )
    await cb.message.edit_reply_markup(reply_markup=keyboard)


async def _handle_back_to_menu(cb: CallbackQuery, state: FSMContext):
    await cb.message.delete()
    await start_collab_menu(message=cb.message, state=state)


async def _edit_message(cb: CallbackQuery, text: str, keyboard):
    try:
        await cb.message.edit_text(text=text, reply_markup=keyboard)
    except Exception as e:
        logging.error(f"Error editing message: {e}")
        await cb.answer("Не удалось обновить сообщение.")
