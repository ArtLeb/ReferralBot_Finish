from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from services.action_logger import CityLogger
from services.category_service import CategoryService
from services.company_service import CompanyService
from services.role_service import RoleService
from services.coupon_service import CouponService
from utils.collab_helper import handle_pagination, filter_categories, filter_cities, comp_locations, loc_info_text, \
    collab_action_keyboard
from utils.keyboards import coupon_menu_keyboard, loc_comp_keyboard, loc_categories_keyboard, loc_city_keyboard, \
    comp_location_keyboard
from utils.states import PartnerStates, CollaborationStates, CreateLocationStates

router = Router()

@router.message(PartnerStates.select_location_action, F.text == "Коллаборации")
async def start_collab_menu(message: Message, state: FSMContext):
    """
    Обработчик кнопки 'Коллаборации'. Выводит меню действий с коллаборациями.
    
    Отображает три кнопки:
    1. Найти агента (поиск партнеров для коллаборации)
    2. Активные коллаборации (просмотр текущих сотрудничеств)
    3. Запросы на коллаборацию (входящие предложения)
    """
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Найти агента", callback_data='iam_coupon_search'))
    builder.row(InlineKeyboardButton(text="Активные коллаборации", callback_data='my_collabs'))
    builder.row(InlineKeyboardButton(text="Запросы на коллаборацию", callback_data='collab_requests'))
    builder.adjust(1)

    await message.answer(
        text='Выберите действие с коллаборациями',
        reply_markup=builder.as_markup()
    )
    await state.set_state(CollaborationStates.collab_menu)

@router.callback_query(CollaborationStates.collab_menu, F.data == 'collab_requests')
async def show_collab_requests(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    """
    Показывает входящие запросы на коллаборацию
    """
    coupon_service = CouponService(session)
    requests = await coupon_service.get_collaboration_requests(
        user_id_tg=cb.from_user.id
    )
    
    # Сохраняем запросы в контекст
    await state.update_data(
        collab_requests=requests,
        current_page=0,
        request_type='collab_requests'
    )
    
    await state.set_state(CollaborationStates.view_requests)
    await display_requests_page(cb, state, session)

async def display_requests_page(
    cb: CallbackQuery, 
    state: FSMContext, 
    session: AsyncSession
):
    """
    Отображает страницу с запросами на коллаборацию
    """
    data = await state.get_data()
    requests = data["collab_requests"]
    current_page = data["current_page"]
    
    # Пагинация
    page_size = 5
    start_index = current_page * page_size
    end_index = start_index + page_size
    page_items = requests[start_index:end_index]
    
    # Формируем текст сообщения
    text = "📬 <b>Запросы на коллаборацию</b>\n\n"
    
    if not requests:
        text = "🤷 У вас пока нет новых запросов на коллаборацию"
    else:
        for idx, req in enumerate(page_items, start=1):
            # Получаем информацию о компании инициатора
            company_service = CompanyService(session)
            company = await company_service.get_company_by_id(req.company_id)
            
            text += (
                f"{start_index + idx}. <b>{company.Name_comp}</b>\n"
                f"   📅 Срок: {req.start_date.strftime('%d.%m.%Y')} - {req.end_date.strftime('%d.%m.%Y')}\n"
                f"   💰 Скидка: {req.discount_percent}%, Комиссия: {req.commission_percent}%\n"
                f"   🔑 Префикс: {req.code_prefix}\n\n"
            )
    
    # Создаем клавиатуру
    builder = InlineKeyboardBuilder()
    
    # Кнопки для каждого запроса
    for req in page_items:
        builder.row(
            InlineKeyboardButton(
                text=f"✅ Принять {req.code_prefix}",
                callback_data=f"accept_{req.id_coupon_type}"
            ),
            InlineKeyboardButton(
                text=f"❌ Отклонить {req.code_prefix}",
                callback_data=f"reject_{req.id_coupon_type}"
            )
        )
    
    # Пагинация
    pagination_row = []
    if current_page > 0:
        pagination_row.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data="page_prev")
        )
    if end_index < len(requests):
        pagination_row.append(
            InlineKeyboardButton(text="Вперед ➡️", callback_data="page_next")
        )
    
    if pagination_row:
        builder.row(*pagination_row)
    
    # Кнопка возврата
    builder.row(
        InlineKeyboardButton(
            text="↩️ Назад в меню", 
            callback_data="back_to_collab_menu"
        )
    )
    
    await cb.message.edit_text(
        text, 
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

# Обработчики пагинации для запросов
@router.callback_query(
    CollaborationStates.view_requests, 
    F.data == "page_prev"
)
async def requests_prev_page(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    current_page = max(0, data["current_page"] - 1)
    await state.update_data(current_page=current_page)
    await display_requests_page(cb, state, session)

@router.callback_query(
    CollaborationStates.view_requests, 
    F.data == "page_next"
)
async def requests_next_page(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    current_page = data["current_page"] + 1
    await state.update_data(current_page=current_page)
    await display_requests_page(cb, state, session)

# Обработчики принятия/отклонения запросов
@router.callback_query(
    CollaborationStates.view_requests, 
    F.data.startswith("accept_")
)
async def accept_collab_request(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Принимает запрос на коллаборацию"""
    coupon_type_id = int(cb.data.split("_")[1])
    coupon_service = CouponService(session)
    success = await coupon_service.accept_collaboration(coupon_type_id)
    
    if success:
        # Обновляем список запросов
        data = await state.get_data()
        requests = [
            r for r in data["collab_requests"] 
            if r.id_coupon_type != coupon_type_id
        ]
        await state.update_data(collab_requests=requests)
        await cb.answer("✅ Запрос принят! Коллаборация активирована.")
        await display_requests_page(cb, state, session)
    else:
        await cb.answer("❌ Ошибка при принятии запроса", show_alert=True)

@router.callback_query(
    CollaborationStates.view_requests, 
    F.data.startswith("reject_")
)
async def reject_collab_request(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Отклоняет запрос на коллаборацию"""
    coupon_type_id = int(cb.data.split("_")[1])
    coupon_service = CouponService(session)
    success = await coupon_service.reject_collaboration(coupon_type_id)
    
    if success:
        # Обновляем список запросов
        data = await state.get_data()
        requests = [
            r for r in data["collab_requests"] 
            if r.id_coupon_type != coupon_type_id
        ]
        await state.update_data(collab_requests=requests)
        await cb.answer("❌ Запрос отклонен")
        await display_requests_page(cb, state, session)
    else:
        await cb.answer("❌ Ошибка при отклонении запроса", show_alert=True)

@router.callback_query(CollaborationStates.collab_menu, F.data == 'my_collabs')
async def show_my_collabs(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Показывает активные коллаборации пользователя"""
    await show_collaborations(cb, state, session, 'my_collabs')

@router.callback_query(CollaborationStates.collab_menu, F.data == 'iam_coupon_search')
async def start_find_agent(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Начало процесса поиска агента для коллаборации"""
    await state.set_state(CollaborationStates.filter_comp_start_menu)
    await search_collab(cb, state, session)

async def show_collaborations(
    cb: CallbackQuery, 
    state: FSMContext, 
    session: AsyncSession,
    collab_type: str
):
    """Общий метод для отображения коллабораций"""
    coupon_service = CouponService(session)
    collaborations = await coupon_service.get_collaborations(
        user_id_tg=cb.from_user.id,
        role=collab_type
    )
    
    # Сохраняем в контекст
    await state.update_data(
        collaborations=collaborations,
        current_page=0,
        collab_type=collab_type
    )
    
    await state.set_state(CollaborationStates.view_collaborations)
    await display_collaborations_page(cb, state, session)

async def display_collaborations_page(
    cb: CallbackQuery, 
    state: FSMContext, 
    session: AsyncSession
):
    """Отображает страницу с коллаборациями"""
    data = await state.get_data()
    collaborations = data["collaborations"]
    current_page = data["current_page"]
    collab_type = data["collab_type"]
    
    # Пагинация
    page_size = 5
    start_index = current_page * page_size
    end_index = start_index + page_size
    page_items = collaborations[start_index:end_index]
    
    # Формируем текст
    text = "🏢 <b>Ваши коллаборации</b>\n\n"
    for idx, collab in enumerate(page_items, start=1):
        partner_company = collab.company.Name_comp
        agent_company = collab.location.company.Name_comp
        text += (
            f"{start_index + idx}. {partner_company} → {agent_company}\n"
            f"   📅 {collab.start_date.strftime('%d.%m.%Y')} - {collab.end_date.strftime('%d.%m.%Y')}\n"
            f"   🔑 {collab.code_prefix}\n\n"
        )
    
    if not collaborations:
        text = "🤷 У вас пока нет активных коллабораций"
    
    # Клавиатура
    builder = InlineKeyboardBuilder()
    
    # Кнопки для элементов
    for collab in page_items:
        builder.row(
            InlineKeyboardButton(
                text=f"❌ Прекратить {collab.code_prefix}",
                callback_data=f"terminate_{collab.id_coupon_type}"
            )
        )
    
    # Пагинация
    pagination_row = []
    if current_page > 0:
        pagination_row.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data="page_prev")
        )
    if end_index < len(collaborations):
        pagination_row.append(
            InlineKeyboardButton(text="Вперед ➡️", callback_data="page_next")
        )
    
    if pagination_row:
        builder.row(*pagination_row)
    
    # Кнопка возврата
    builder.row(
        InlineKeyboardButton(
            text="↩️ Назад в меню", 
            callback_data="back_to_collab_menu"
        )
    )
    
    await cb.message.edit_text(
        text, 
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

# Обработчики пагинации
@router.callback_query(
    CollaborationStates.view_collaborations, 
    F.data == "page_prev"
)
async def prev_page(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    current_page = max(0, data["current_page"] - 1)
    await state.update_data(current_page=current_page)
    await display_collaborations_page(cb, state, session)

@router.callback_query(
    CollaborationStates.view_collaborations, 
    F.data == "page_next"
)
async def next_page(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    current_page = data["current_page"] + 1
    await state.update_data(current_page=current_page)
    await display_collaborations_page(cb, state, session)

# Обработчик прекращения коллаборации
@router.callback_query(
    CollaborationStates.view_collaborations, 
    F.data.startswith("terminate_")
)
async def terminate_collab(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    coupon_type_id = int(cb.data.split("_")[1])
    coupon_service = CouponService(session)
    terminated = await coupon_service.terminate_collaboration(coupon_type_id)
    
    if terminated:
        # Обновляем список
        data = await state.get_data()
        collaborations = [
            c for c in data["collaborations"] 
            if c.id_coupon_type != coupon_type_id
        ]
        await state.update_data(collaborations=collaborations)
        await cb.answer("✅ Коллаборация прекращена")
        await display_collaborations_page(cb, state, session)

# Возврат в меню
@router.callback_query(
    CollaborationStates.view_collaborations, 
    F.data == "back_to_collab_menu"
)
async def back_to_menu(cb: CallbackQuery, state: FSMContext):
    await state.set_state(CollaborationStates.collab_menu)
    await cb.message.delete()
    await start_collab_menu(cb.message, state)

@router.callback_query(
    CollaborationStates.view_requests, 
    F.data == "back_to_collab_menu"
)
async def back_to_menu_from_requests(cb: CallbackQuery, state: FSMContext):
    await state.set_state(CollaborationStates.collab_menu)
    await cb.message.delete()
    await start_collab_menu(cb.message, state)

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