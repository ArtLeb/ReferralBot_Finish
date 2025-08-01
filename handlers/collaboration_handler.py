from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
import json
from aiogram.utils.keyboard import ReplyKeyboardBuilder, ReplyKeyboardMarkup
from aiogram.types import KeyboardButton
from services import user_service
from utils.database.models import User
from services.user_service import UserService
from datetime import date, timedelta
from services.role_service import RoleService
from datetime import date, timedelta
from services.action_logger import CityLogger
from services.category_service import CategoryService
from services.company_service import CompanyService

from services.coupon_service import CouponService
from utils.collab_helper import handle_pagination, filter_categories, filter_cities, comp_locations, loc_info_text, \
    collab_action_keyboard
from utils.keyboards import coupon_menu_keyboard, loc_comp_keyboard, loc_categories_keyboard, loc_city_keyboard, \
    comp_location_keyboard
from utils.states import PartnerStates, CollaborationStates, CreateLocationStates

router = Router()

# Обработчик кнопки "Назад" в меню управления локацией
@router.message(PartnerStates.select_location_action, F.text == "Назад")
async def back_to_company_menu(message: Message, state: FSMContext, session: AsyncSession):
    """
    Обработчик кнопки 'Назад' в меню управления локацией.
    Возвращает пользователя в меню выбора локации компании.
    """
    data = await state.get_data()
    company_id = data.get('company_id')
    
    if company_id:
        comp_service = CompanyService(session)
        locations = await comp_service.get_locations_by_company(company_id=company_id)
        
        keyboard = comp_location_keyboard(locations=locations, page=0)
        await message.answer(
            text="Выберите локацию для управления:",
            reply_markup=keyboard
        )
        await state.set_state(PartnerStates.edit_location_select)
    else:
        await message.answer("❌ Не удалось определить компанию. Возврат в главное меню.")
        # Здесь должен быть код возврата в главное меню
        await state.clear()

@router.message(PartnerStates.select_location_action, F.text == "Коллаборации")
async def start_collab_menu(message: Message, state: FSMContext):
    """
    Обработчик кнопки 'Коллаборации'. Выводит меню действий с коллаборациями.
    """
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Я выдаю купоны", callback_data='iam_coupon'))
    builder.row(InlineKeyboardButton(text="Я агент", callback_data='iam_agent'))
    builder.row(InlineKeyboardButton(text="Активные коллаборации (все)", callback_data='all_active_collabs_main'))
    builder.row(InlineKeyboardButton(text="↩️ Назад", callback_data='back_to_location_menu'))
    builder.adjust(1)

    await message.answer(
        text='Выберите вашу роль для управления коллаборациями',
        reply_markup=builder.as_markup()
    )
    await state.set_state(CollaborationStates.COLLABORATION_MENU)

# Обработчик кнопки "Администраторы"
@router.message(PartnerStates.select_location_action, F.text == "Администраторы")
async def handle_manage_admins(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    location_id = data.get('location_id')
    company_id = data.get('company_id')
    
    if not location_id or not company_id:
        await message.answer("❌ Не удалось определить локацию или компанию.")
        return

    # Получаем список администраторов
    role_service = RoleService(session)
    admins = await role_service.get_location_admins(company_id, location_id)
    
    text = "👑 Администраторы этой локации:\n"
    if admins:
        user_service = UserService(session)  
        
        for admin_role in admins:  # Перебираем роли администраторов
            # Получаем пользователя по Telegram ID из роли
            user = await user_service.get_user_by_tg_id(admin_role.user_id)
            
            if user:
                # Форматируем имя и фамилию, если они есть
                name = f"{user.first_name or ''} {user.last_name or ''}".strip()
                text += f"- {name} (Telegram ID: {user.id_tg})\n"
            else:
                # Если пользователь не найден, используем ID из роли
                text += f"- [Неизвестный пользователь] (Telegram ID: {admin_role.user_id})\n"
    else:
        text += "Пока нет администраторов."

    # Клавиатура действий 
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Добавить администратора")],
            [KeyboardButton(text="Удалить администратора")],
            [KeyboardButton(text="Назад")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(text, reply_markup=keyboard)
    await state.set_state(PartnerStates.manage_admins)

# Меню управления администраторами
@router.message(PartnerStates.manage_admins, F.text == "Назад")
async def back_to_location_management(message: Message, state: FSMContext):
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Редактировать")],
            [KeyboardButton(text="Коллаборации")],
            [KeyboardButton(text="Администраторы")],
            [KeyboardButton(text="Назад")]
        ],
        resize_keyboard=True
    )
    await state.set_state(PartnerStates.select_location_action)
    await message.answer("Выберите действие для локации:", reply_markup=markup)

# Начало добавления администратора
# Обработчик управления администраторами
@router.message(PartnerStates.manage_admins, F.text == "Добавить администратора")
async def start_adding_admin(message: Message, state: FSMContext):
    await message.answer("Введите Telegram ID пользователя для назначения администратором:")
    await state.set_state(PartnerStates.add_admin_tg_id)

# Обработка ввода Telegram ID
@router.message(PartnerStates.add_admin_tg_id)
async def process_add_admin_tg_id(message: Message, state: FSMContext, session: AsyncSession):
    try:
        tg_id = int(message.text)
    except ValueError:
        await message.answer("❌ Неверный формат. Введите числовой Telegram ID.")
        return

    data = await state.get_data()
    company_id = data.get('company_id')
    location_id = data.get('location_id')
    
    user_service = UserService(session)
    user = await user_service.get_user_by_tg_id(tg_id)
    
    if not user:
        await message.answer("❌ Пользователь с таким ID не найден.")
        return

    # Проверка наличия роли
    role_service = RoleService(session)
    existing = await role_service.get_user_role_in_location(
        tg_id=tg_id,
        company_id=company_id,
        location_id=location_id,
        role='admin'
    )
    
    if existing:
        await message.answer("❌ Этот пользователь уже является администратором.")
        return

    # Добавление роли
    end_date = date.today() + timedelta(days=365)
    await role_service.add_admin_role(
        tg_id=tg_id,
        company_id=company_id,
        location_id=location_id,
        end_date=end_date,
        changed_by=message.from_user.id
    )
    
    await message.answer(f"✅ Пользователь назначен администратором. (Telegram ID: {tg_id})")
    await handle_manage_admins(message, state, session)

# Удаление администратора
@router.message(PartnerStates.manage_admins, F.text == "Удалить администратора")
async def start_removing_admin(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    company_id = data.get('company_id')
    location_id = data.get('location_id')
    
    role_service = RoleService(session)
    admins = await role_service.get_location_admins(company_id, location_id)
    
    if not admins:
        await message.answer("Нет администраторов для удаления.")
        return

    # Создаем клавиатуру с администраторами
    keyboard = ReplyKeyboardBuilder()
    admin_records = {}
    user_service = UserService(session)
    
    for admin in admins:
        user = await user_service.get_user_by_tg_id(admin.user_id)
        display_name = f"{user.first_name} {user.last_name}" if user else f"ID: {admin.user_id}"
        btn_text = f"{display_name} (TG: {admin.user_id})"
        
        admin_records[btn_text] = admin.id  # Сохраняем ID записи роли
        keyboard.add(KeyboardButton(text=btn_text))
    
    keyboard.add(KeyboardButton(text="Назад"))
    keyboard.adjust(1)
    
    await state.update_data(admin_records=admin_records)
    await message.answer("Выберите администратора для удаления:", reply_markup=keyboard.as_markup(resize_keyboard=True))
    await state.set_state(PartnerStates.remove_admin)

# Обработка выбора для удаления
@router.message(PartnerStates.remove_admin)
async def process_remove_admin(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    admin_records = data.get("admin_records", {})
    
    if message.text == "Назад":
        await handle_manage_admins(message, state, session)
        return
        
    if message.text not in admin_records:
        await message.answer("❌ Администратор не найден.")
        return

    role_service = RoleService(session)
    success = await role_service.remove_admin_role(admin_records[message.text])
    
    if success:
        await message.answer("✅ Администратор успешно удален.")
    else:
        await message.answer("❌ Не удалось удалить администратора.")
    
    await handle_manage_admins(message, state, session)

@router.callback_query(CollaborationStates.COLLABORATION_MENU, F.data == 'back_to_location_menu')
async def back_to_location_menu(cb: CallbackQuery, state: FSMContext):
    """Возврат в меню управления локацией"""
    # Создаем клавиатуру для меню управления локацией
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Редактировать")],
            [KeyboardButton(text="Коллаборации")],
            [KeyboardButton(text="Администраторы")],
            [KeyboardButton(text="Назад")]
        ],
        resize_keyboard=True
    )
    
    await state.set_state(PartnerStates.select_location_action)
    await cb.message.answer("Выберите действие для локации:", reply_markup=markup)
    await cb.message.delete()

@router.callback_query(CollaborationStates.COLLABORATION_MENU, F.data == 'iam_coupon')
async def iam_coupon_menu(cb: CallbackQuery, state: FSMContext):
    """
    Меню для роли "Я выдаю купоны"
    """
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Найти агента", callback_data='iam_coupon_search'))
    builder.row(InlineKeyboardButton(text="Активные коллаборации (мои)", callback_data='my_active_collabs'))
    builder.row(InlineKeyboardButton(text="↩️ Назад", callback_data='back_to_main_collab'))
    builder.adjust(1)

    await cb.message.edit_text(
        text='Выберите действие для роли "Я выдаю купоны":',
        reply_markup=builder.as_markup()
    )

@router.callback_query(CollaborationStates.COLLABORATION_MENU, F.data == 'iam_agent')
async def iam_agent_menu(cb: CallbackQuery, state: FSMContext):
    """
    Меню для роли "Я агент"
    """
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Запросы на коллаборацию", callback_data='collab_requests'))
    builder.row(InlineKeyboardButton(text="Активные коллаборации", callback_data='my_active_collabs'))
    builder.row(InlineKeyboardButton(text="↩️ Назад", callback_data='back_to_main_collab'))
    builder.adjust(1)

    await cb.message.edit_text(
        text='Выберите действие для роли "Я агент":',
        reply_markup=builder.as_markup()
    )

@router.callback_query(CollaborationStates.COLLABORATION_MENU, F.data == 'back_to_main_collab')
async def back_to_main_menu(cb: CallbackQuery, state: FSMContext):
    """
    Возврат в главное меню коллабораций
    """
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Я выдаю купоны", callback_data='iam_coupon'))
    builder.row(InlineKeyboardButton(text="Я агент", callback_data='iam_agent'))
    builder.row(InlineKeyboardButton(text="Активные коллаборации (все)", callback_data='all_active_collabs_main'))
    builder.adjust(1)

    await cb.message.edit_text(
        text='Выберите вашу роль для управления коллаборациями',
        reply_markup=builder.as_markup()
    )

@router.callback_query(CollaborationStates.COLLABORATION_MENU, F.data == 'iam_coupon_search')
async def start_find_agent(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Начало процесса поиска агента для коллаборации"""
    await state.set_state(CollaborationStates.filter_comp_start_menu)
    await search_collab(cb, state, session)

@router.callback_query(CollaborationStates.COLLABORATION_MENU, F.data == 'collab_requests')
async def show_collab_requests(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    """
    Показывает входящие запросы на коллаборацию
    """
    coupon_service = CouponService(session)
    requests = await coupon_service.get_collaboration_requests(
        user_id_tg=cb.from_user.id
    )
    
    # Сохраняем запросы в контекст как словари
    serializable_requests = []
    for req in requests:
        serializable_requests.append({
            'id_coupon_type': req.id_coupon_type,
            'company_id': req.company_id,
            'code_prefix': req.code_prefix,
            'discount_percent': float(req.discount_percent),
            'commission_percent': float(req.commission_percent),
            'start_date': req.start_date.isoformat(),
            'end_date': req.end_date.isoformat()
        })
    
    await state.update_data(
        collab_requests=serializable_requests,
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
    requests_data = data["collab_requests"]
    current_page = data["current_page"]
    
    # Пагинация
    page_size = 5
    start_index = current_page * page_size
    end_index = start_index + page_size
    page_items = requests_data[start_index:end_index]
    
    # Формируем текст сообщения
    text = "📬 <b>Запросы на коллаборацию</b>\n\n"
    
    if not requests_data:
        text = "🤷 У вас пока нет новых запросов на коллаборацию"
    else:
        for idx, req in enumerate(page_items, start=1):
            # Получаем информацию о компании инициатора
            company_service = CompanyService(session)
            company = await company_service.get_company_by_id(req['company_id'])
            
            text += (
                f"{start_index + idx}. <b>{company.Name_comp}</b>\n"
                f"   📅 Срок: {req['start_date'][:10]} - {req['end_date'][:10]}\n"
                f"   💰 Скидка: {req['discount_percent']}%, Комиссия: {req['commission_percent']}%\n"
                f"   🔑 Префикс: {req['code_prefix']}\n\n"
            )
    
    # Создаем клавиатуру
    builder = InlineKeyboardBuilder()
    
    # Кнопки для каждого запроса
    for req in page_items:
        builder.row(
            InlineKeyboardButton(
                text=f"✅ Принять {req['code_prefix']}",
                callback_data=f"accept_{req['id_coupon_type']}"
            ),
            InlineKeyboardButton(
                text=f"❌ Отклонить {req['code_prefix']}",
                callback_data=f"reject_{req['id_coupon_type']}"
            )
        )
    
    # Пагинация
    pagination_row = []
    if current_page > 0:
        pagination_row.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data="page_prev")
        )
    if end_index < len(requests_data):
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
            if r['id_coupon_type'] != coupon_type_id
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
            if r['id_coupon_type'] != coupon_type_id
        ]
        await state.update_data(collab_requests=requests)
        await cb.answer("❌ Запрос отклонен")
        await display_requests_page(cb, state, session)
    else:
        await cb.answer("❌ Ошибка при отклонении запроса", show_alert=True)

@router.callback_query(CollaborationStates.COLLABORATION_MENU, F.data == 'my_active_collabs')
async def show_my_collabs(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Показывает активные коллаборации пользователя"""
    await show_collaborations(cb, state, session, 'my_collabs')

@router.callback_query(
    CollaborationStates.COLLABORATION_MENU, 
    F.data == 'all_active_collabs_main'
)
async def show_all_collabs_main(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Показывает все активные коллаборации из главного меню"""
    await show_collaborations(cb, state, session, 'all_collabs')

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
        role='my_collabs' if collab_type == 'my_collabs' else 'all'
    )
    
    # Сохраняем только идентификаторы и необходимые данные
    serializable_collabs = []
    for collab in collaborations:
        serializable_collabs.append({
            'id_coupon_type': collab.id_coupon_type,
            'code_prefix': collab.code_prefix,
            'start_date': collab.start_date.isoformat(),
            'end_date': collab.end_date.isoformat(),
            'company_id': collab.company_id,
            'location_id': collab.location_id
        })
    
    # Сохраняем в контекст
    await state.update_data(
        collaborations=serializable_collabs,
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
    collab_data = data["collaborations"]
    current_page = data["current_page"]
    collab_type = data["collab_type"]
    
    # Пагинация
    page_size = 5
    start_index = current_page * page_size
    end_index = start_index + page_size
    page_items = collab_data[start_index:end_index]
    
    # Формируем текст
    role_text = {
        'my_collabs': 'Ваши активные коллаборации',
        'all_collabs': 'Все активные коллаборации'
    }
    text = f"🏢 <b>{role_text.get(collab_type, 'Коллаборации')}</b>\n\n"
    
    if not collab_data:
        text = "🤷 У вас пока нет активных коллабораций"
    else:
        for idx, collab in enumerate(page_items, start=1):
            # Получаем информацию о компаниях
            company_service = CompanyService(session)
            partner_company = await company_service.get_company_by_id(collab['company_id'])
            location = await company_service.get_location_by_id(collab['location_id'])
            agent_company = await company_service.get_company_by_id(location.id_comp)
            
            role = "🔹 Купон" if collab_type == 'my_collabs' else "🔸 Агент"
            text += (
                f"{start_index + idx}. {role} {partner_company.Name_comp} → {agent_company.Name_comp}\n"
                f"   📅 {collab['start_date'][:10]} - {collab['end_date'][:10]}\n"
                f"   🔑 {collab['code_prefix']}\n\n"
            )
    
    # Клавиатура
    builder = InlineKeyboardBuilder()
    
    # Кнопки для элементов
    for collab in page_items:
        builder.row(
            InlineKeyboardButton(
                text=f"❌ Прекратить {collab['code_prefix']}",
                callback_data=f"terminate_{collab['id_coupon_type']}"
            )
        )
    
    # Пагинация
    pagination_row = []
    if current_page > 0:
        pagination_row.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data="page_prev")
        )
    if end_index < len(collab_data):
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
            if c['id_coupon_type'] != coupon_type_id
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
    await state.set_state(CollaborationStates.COLLABORATION_MENU)
    await cb.message.delete()
    # Возврат в главное меню коллабораций
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Я выдаю купоны", callback_data='iam_coupon'))
    builder.row(InlineKeyboardButton(text="Я агент", callback_data='iam_agent'))
    builder.row(InlineKeyboardButton(text="Активные коллаборации (все)", callback_data='all_active_collabs_main'))
    builder.adjust(1)

    await cb.message.answer(
        text='Выберите вашу роль для управления коллаборациями',
        reply_markup=builder.as_markup()
    )

@router.callback_query(
    CollaborationStates.view_requests, 
    F.data == "back_to_collab_menu"
)
async def back_to_menu_from_requests(cb: CallbackQuery, state: FSMContext):
    await state.set_state(CollaborationStates.COLLABORATION_MENU)
    await cb.message.delete()
    # Возврат в главное меню коллабораций
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Я выдаю купоны", callback_data='iam_coupon'))
    builder.row(InlineKeyboardButton(text="Я агент", callback_data='iam_agent'))
    builder.row(InlineKeyboardButton(text="Активные коллаборации (все)", callback_data='all_active_collabs_main'))
    builder.adjust(1)

    await cb.message.answer(
        text='Выберите вашу роль для управления коллаборациями',
        reply_markup=builder.as_markup()
    )

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