from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from handlers.command_handler import start
from handlers.common_handlers import partner_selected
from services.category_service import CategoryService
from services.company_service import CompanyService
from sqlalchemy.ext.asyncio import AsyncSession
from services.role_service import RoleService
from services.user_service import UserService
from utils.states import PartnerStates
from utils.keyboards import companies_keyboard, locations_keyboard, loc_categories_keyboard, loc_admin_keyboard
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import KeyboardButton
import logging

router = Router()
logger = logging.getLogger(__name__)

@router.message(F.text == "Мои компании")
async def list_companies(message: Message, session: AsyncSession, state: FSMContext):
    """Просмотр списка компаний партнера"""
    comp_service = CompanyService(session)
    companies = await comp_service.get_user_companies(message.from_user.id)

    if not companies:
        await message.answer(
            "У вас пока нет компаний, введите комманду /regcomp чтобы зарегистрировать вашу первую компаянию")
        return

    await message.answer(
        "🏢 Ваши компании:",
        reply_markup=companies_keyboard(companies)
    )
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="⬅️ Назад"))

    await message.answer(text='Выберите компанию из списка выше', reply_markup=builder.as_markup())
    await state.set_state(PartnerStates.company_menu)

@router.message(F.text == "Создать компанию")
async def create_company(message: Message, state: FSMContext):
    """Просмотр списка компаний партнера"""
    await partner_selected(message=message, state=state)

@router.callback_query(PartnerStates.company_menu, F.data.startswith("company_"))
async def select_company(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Выбор компании для управления"""
    company_id = int(callback.data.split("_")[1])
    service = CompanyService(session)
    company = await service.get_company_by_id(company_id)

    if not company:
        await callback.answer("Компания не найдена")
        return

    await state.update_data(dict(company_id=company_id, company_name=company.Name_comp,
                                 my_company_id=company_id, my_company_name=company.Name_comp))
    company_info = (
        f"🏢 Компания: {company.Name_comp}\n"
        f"📍 Локаций: {len(company.locations)}"
    )

    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="Локации"))
    builder.row(KeyboardButton(text="Добавить Локацию"))
    builder.row(KeyboardButton(text="Редактировать Компанию"))
    builder.row(KeyboardButton(text="ТГ Группы"))  
    builder.row(KeyboardButton(text="⬅️ Назад"))

    await callback.message.answer(company_info, reply_markup=builder.as_markup(resize_keyboard=True))
    await callback.answer()




@router.message(PartnerStates.company_menu, F.text == "⬅️ Назад")
async def manage_locations(message: Message, state: FSMContext, session: AsyncSession):
    """Управление локациями компании"""
    await start(state=state, message=message, session=session)


@router.message(PartnerStates.company_menu, F.text == "Локации")
async def manage_locations(message: Message, state: FSMContext, session: AsyncSession):
    """Управление локациями компании"""
    data = await state.get_data()
    company_id = data.get('company_id')

    if not company_id:
        await message.answer("❌ Сначала выберите компанию")
        return

    service = CompanyService(session)
    locations = await service.get_locations_by_company(company_id)

    if not locations:
        await message.answer("В этой компании пока нет локаций")
        return

    await message.answer(
        "📍 Локации компании:",
        reply_markup=locations_keyboard(locations)
    )


@router.callback_query(PartnerStates.company_menu, F.data.startswith("location_"))
async def select_location(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Выбор локации для управления"""
    location_id = int(callback.data.split("_")[1])
    data = await state.get_data()
    service = CompanyService(session)
    location = await service.get_location_by_id(location_id)

    if not location:
        await callback.answer("Локация не найдена")
        return

    await state.update_data(dict(location_id=location_id, location_name=location.name_loc,
                                 my_location_id=location_id, my_location_name=location.name_loc))

    company_info = (
        f"🏢 Компания: {data['company_name']}\n"
        f"📍 Локация: {location.name_loc}"
    )

    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="Редактировать"))
    builder.row(KeyboardButton(text="Коллаборации"))
    builder.row(KeyboardButton(text="Администраторы"))
    builder.row(KeyboardButton(text="⬅️ Назад"))

    await state.set_state(PartnerStates.select_location_action)
    await callback.message.answer(company_info, reply_markup=builder.as_markup(resize_keyboard=True))
    await callback.answer()


@router.message(PartnerStates.select_location_action, F.text == "⬅️ Назад")
async def start_edit_location(message: Message, state: FSMContext, session: AsyncSession):
    await manage_locations(state=state, message=message, session=session)


@router.message(PartnerStates.select_location_action, F.text == "Редактировать")
async def start_edit_location(message: Message, state: FSMContext):
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="Название Локации"))
    builder.row(KeyboardButton(text="Адресс Локации"))
    builder.row(KeyboardButton(text="Город Локации"))
    builder.row(KeyboardButton(text="Ссылка на карты"))
    builder.row(KeyboardButton(text="Категории Локации"))
    builder.row(KeyboardButton(text="Удалить Локацию"))
    builder.row(KeyboardButton(text="Отменить редактирование"))

    await message.answer(
        text="Выберите поле для редактирования",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )

    await state.update_data(action=None)
    await state.set_state(PartnerStates.select_edit_fild_loc)


@router.message(PartnerStates.select_edit_fild_loc)
async def process_field_selection(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    field_btn_mapping = {
        'Название Локации': 'name_loc',
        'Адресс Локации': 'address',
        'Город Локации': 'city',
        'Ссылка на карты': 'map_url',
        'Категории Локации': 'category',
        'Удалить Локацию': 'delete'
    }

    action = field_btn_mapping.get(message.text)
    comp_service = CompanyService(session)

    if message.text == 'Отменить редактирование':
        await manage_locations(message=message, state=state, session=session)
        await state.set_state(PartnerStates.company_menu)
        return

    if not action:
        current_action = data.get('action')
        if current_action in ['name_loc', 'address', 'city', 'map_url']:
            await comp_service.update_location(
                location_id=int(data['location_id']),
                update_data={current_action: message.text},
            )
            await message.answer(f"Поле {current_action} успешно обновлено")
            await manage_locations(message=message, state=state, session=session)
            await state.set_state(PartnerStates.company_menu)
            return

        await message.answer("Пожалуйста, выберите действие из меню.")
        return

    await state.update_data(action=action)

    if action in ['name_loc', 'address', 'city', 'map_url']:
        await message.answer(f"Введите новое значение для: {message.text}")
    elif action == 'delete':
        await comp_service.delete_location(location_id=int(data['location_id']))
        await message.answer("✅ Локация успешно удалена.")
        await manage_locations(message=message, state=state, session=session)
        await state.set_state(PartnerStates.company_menu)

    elif action == 'category':
        category_service = CategoryService(session)
        categories = await category_service.get_all_categories()
        selected_category = await comp_service.get_loc_categories_id(
            comp_id=int(data['company_id']),
            id_location=int(data['location_id']),
        )
        keyboard = loc_categories_keyboard(
            categories=categories,
            selected_category=selected_category
        )
        await message.answer("✍️ Выберите категории для локации:", reply_markup=keyboard)
        await state.update_data(
            selected_category=selected_category,
            initial_categories=selected_category.copy(),
            current_page=0
        )
        await state.set_state(PartnerStates.edit_category_loc)


@router.callback_query(PartnerStates.edit_category_loc)
async def process_edit_categories(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    selected_category: list = data.get('selected_category', [])
    initial_categories: list = data.get('initial_categories', [])
    current_page: int = data.get('current_page', 0)

    comp_service = CompanyService(session)
    category_service = CategoryService(session)

    if cb.data.startswith('category_'):
        category_id = int(cb.data.split('_')[1])
        if category_id in selected_category:
            selected_category.remove(category_id)
        else:
            selected_category.append(category_id)

        await state.update_data(selected_category=selected_category)
        categories = await category_service.get_all_categories()
        keyboard = loc_categories_keyboard(categories, selected_category, current_page)
        await cb.message.edit_reply_markup(reply_markup=keyboard)

    elif cb.data.startswith('page_'):
        new_page = int(cb.data.split('_')[1])
        await state.update_data(current_page=new_page)
        categories = await category_service.get_all_categories()
        keyboard = loc_categories_keyboard(categories, selected_category, new_page)
        await cb.message.edit_reply_markup(reply_markup=keyboard)

    elif cb.data == 'add_category':
        if not selected_category:
            await cb.answer(text="Выберите хотя бы одну категорию!", show_alert=True)
            return

        added = [cat for cat in selected_category if cat not in initial_categories]
        removed = [cat for cat in initial_categories if cat not in selected_category]

        for cat_id in added:
            await comp_service.set_loc_category(
                comp_id=data['company_id'],
                id_location=data['location_id'],
                id_category=cat_id
            )

        for cat_id in removed:
            await comp_service.remove_loc_category(
                comp_id=data['company_id'],
                id_location=data['location_id'],
                id_category=cat_id
            )

        await cb.message.answer("✅ Категории успешно обновлены.")
        await cb.message.delete()

        await state.set_state(PartnerStates.company_menu)
        await manage_locations(message=cb.message, state=state, session=session)

    elif cb.data == 'noop':
        await cb.answer()


@router.message(PartnerStates.select_location_action, F.text == "Администраторы")
async def admin_menu_location(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    role_service = RoleService(session)
    roles_users = await role_service.get_roles_in_loc(
        location_id=int(data['location_id']),
        role_name='admin',
        company_id=data['company_id'])

    await state.update_data(current_page=0, admin_user_id=None)
    keyboard = loc_admin_keyboard(roles_users=roles_users)

    await message.answer(
        text="Выберите поле для редактирования",
        reply_markup=keyboard
    )

    await state.update_data(action=None)
    await state.set_state(PartnerStates.select_admin_menu)


@router.callback_query(PartnerStates.select_admin_menu)
async def process_edit_categories(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()

    role_service = RoleService(session)

    if cb.data == 'add_admin':
        await cb.message.answer(text="Отправьте User ID пользователя")
        await state.set_state(PartnerStates.get_new_admin_user_id)

    if cb.data == 'back':
        await cb.message.delete()
        service = CompanyService(session)
        location = await service.get_location_by_id(data['location_id'])

        if not location:
            await cb.answer("Локация не найдена")
            return

        await state.update_data(dict(location_id=data['location_id'], location_name=location.name_loc))

        company_info = (
            f"🏢 Компания: {data['company_name']}\n"
            f"📍 Локация: {location.name_loc}"
        )

        builder = ReplyKeyboardBuilder()
        builder.row(KeyboardButton(text="Редактировать"))
        builder.row(KeyboardButton(text="Администраторы"))

        await state.set_state(PartnerStates.select_location_action)
        await cb.message.answer(company_info, reply_markup=builder.as_markup(resize_keyboard=True))
        await cb.answer()

    if cb.data == 'del_admin':
        if not data.get('admin_user_id'):
            await cb.message.answer(text="Прежде нажмите на кнопку админа которого хотите удалить")
            return

        await role_service.remove_role(
            user_id=data.get('admin_user_id'),
            location_id=data['location_id'],
            role_name='admin',
            company_id=data['company_id']
        )
        await cb.message.delete()
        await cb.message.answer(text=f"Админ User ID {data.get('admin_user_id')} удален")
        await admin_menu_location(message=cb.message, state=state, session=session)

        return

    if cb.data.startswith('admin_'):
        admin_user_id = int(cb.data.split('_')[1])
        current_page = data.get('current_page')
        if data.get('admin_user_id', 0) == admin_user_id:
            admin_user_id = None
        await state.update_data(admin_user_id=admin_user_id)

        roles_users = await role_service.get_roles_in_loc(
            location_id=int(data['location_id']),
            role_name='admin',
            company_id=data['company_id'])

        keyboard = loc_admin_keyboard(
            roles_users=roles_users,
            page=current_page,
            admin_user_id=admin_user_id
        )

        await cb.message.edit_reply_markup(reply_markup=keyboard)

    elif cb.data.startswith('page_'):
        new_page = int(cb.data.split('_')[1])
        roles_users = await role_service.get_roles_in_loc(
            location_id=int(data['location_id']),
            role_name='admin',
            company_id=data['company_id'])
        keyboard = loc_admin_keyboard(roles_users=roles_users, page=new_page)
        await state.update_data(current_page=new_page)
        await cb.message.edit_reply_markup(reply_markup=keyboard)


@router.message(PartnerStates.get_new_admin_user_id)
async def get_new_admin_user_id(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    user_id = message.text

    if not user_id.isdigit():
        await message.answer('User ID пользователя должен состоять только из цифр')
        return

    user_service = UserService(session)
    admin = await user_service.get_user_by_tg_id(tg_id=int(user_id))

    if not admin:
        await message.answer('Пользователь не найден')
        return

    role_service = RoleService(session)
    new_admin = await role_service.assign_role_to_user(
        role_name='admin',
        company_id=data['company_id'],
        location_id=data['location_id'],
        user_id=admin.id_tg
    )

    if new_admin:
        await message.answer('Админ успешно добавлен')
    else:
        await message.answer('Ошибка при добавлении')

    await admin_menu_location(message=message, state=state, session=session)
