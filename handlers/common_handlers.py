# common_handlers.py
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.fsm.context import FSMContext
from utils.database.models import User
from services.role_service import RoleService
from services.company_service import CompanyService
from services.category_service import CategoryService
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from utils.keyboards import main_menu, loc_categories_keyboard
from utils.states import RegistrationStates

logger = logging.getLogger(__name__)
router = Router()


@router.message(RegistrationStates.CHOOSING_ROLE, F.text == "Я клиент")
async def client_selected(message: Message, session: AsyncSession, state: FSMContext):
    """Обработчик выбора роли клиента"""
    await state.clear()
    await message.answer(
        "✅ Вы зарегистрированы как клиент!",
        reply_markup=await main_menu(session, message.from_user.id)
    )


@router.message(RegistrationStates.CHOOSING_ROLE, F.text == "Я партнер (компания)")
async def partner_selected(message: Message, state: FSMContext):
    """Начало процесса регистрации компании"""
    await state.set_state(RegistrationStates.COMPANY_NAME)
    await message.answer(
        "Введите название вашей компании:\n\n"
        "❕ Вы можете отменить регистрацию командой /cancel",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(RegistrationStates.COMPANY_NAME)
async def start_create_new_location(message: Message, state: FSMContext, session: AsyncSession):
    await state.update_data(company_name=message.text)
    category_service = CategoryService(session)
    categories = await category_service.get_all_categories()
    keyboard = loc_categories_keyboard(categories, selected_category=[])
    await message.answer(
        text=f"✍️ Введите Категории",
        reply_markup=keyboard
    )
    await state.update_data(selected_category=[], current_page=0)
    await state.set_state(RegistrationStates.COMPANY_CATEGORY_RECORD)


@router.callback_query(RegistrationStates.COMPANY_CATEGORY_RECORD)
async def process_company_name(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Обработка выбора категорий и пагинации"""
    data = await state.get_data()
    selected_category: list = data.get('selected_category', [])
    current_page: int = data.get('current_page', 0)

    if cb.data.startswith('category_'):
        category_id = int(cb.data.split('_')[1])
        if category_id in selected_category:
            selected_category.remove(category_id)
        else:
            selected_category.append(category_id)

        await state.update_data(selected_category=selected_category)

        category_service = CategoryService(session)
        categories = await category_service.get_all_categories()
        keyboard = loc_categories_keyboard(categories, selected_category, current_page)

        await cb.message.edit_reply_markup(reply_markup=keyboard)

    elif cb.data.startswith('page_'):
        new_page = int(cb.data.split('_')[1])
        await state.update_data(current_page=new_page)

        category_service = CategoryService(session)
        categories = await category_service.get_all_categories()
        keyboard = loc_categories_keyboard(categories, selected_category, new_page)

        await cb.message.edit_reply_markup(reply_markup=keyboard)

    elif cb.data == 'add_category':
        if not selected_category:
            await cb.answer(text="Выберите хотя бы одну категорию!", show_alert=True)
            return

        await cb.message.answer(text="💾 Категории компании успешно сохранены")
        await cb.message.delete()
        await cb.message.answer(text="Введите город расположения компании:")
        await state.set_state(RegistrationStates.CITY_SELECTION)
    elif cb.data == 'noop':
        await cb.answer()


@router.message(RegistrationStates.CITY_SELECTION)
async def process_city(message: Message, state: FSMContext):
    """Сохранение города компании"""
    await state.update_data(city=message.text)
    await state.set_state(RegistrationStates.COMPANY_ADDRESS_URL)
    await message.answer("Введите адрес компании:")


@router.message(RegistrationStates.COMPANY_ADDRESS_URL)
async def process_city(message: Message, state: FSMContext):
    """Сохранение Ссылки компании"""
    await state.update_data(address=message.text)
    await state.set_state(RegistrationStates.COMPANY_ADDRESS)
    await message.answer("Введите Сслыку на картах:")


@router.message(RegistrationStates.COMPANY_ADDRESS)
async def process_company_address(message: Message, state: FSMContext, session: AsyncSession):
    """Завершение регистрации компании"""
    data = await state.get_data()
    company_service = CompanyService(session)

    try:
        company = await company_service.create_company(
            name=data['company_name'],
            owner_id=message.from_user.id
        )

        location = await company_service.create_location(
            company_id=company.id_comp,
            city=data['city'],
            address=data['address'],
            map_url=message.text,
            name_loc=data['company_name'],
            main_loc=True
        )
        for category_id in data.get('selected_category', []):
            await company_service.set_loc_category(
                comp_id=company.id_comp,
                id_location=location.id_location,
                id_category=category_id
            )

        role_service = RoleService(session)
        await role_service.assign_role_to_user(
            user_id=message.from_user.id,
            role_name='partner',
            company_id=company.id_comp,
            location_id=location.id_location
        )

        await state.clear()
        await message.answer(
            f"✅ Компания {company.Name_comp} успешно зарегистрирована!",
            reply_markup=await main_menu(session, message.from_user.id)
        )
    except Exception as e:
        logger.error(f"Ошибка регистрации компании: {e}")
        await message.answer("⚠️ Произошла ошибка при регистрации компании. Попробуйте позже.")


@router.message(F.text == "Мой профиль")
async def my_profile(message: Message, session: AsyncSession, user: User):
    """Отображение профиля пользователя"""
    role_service = RoleService(session)
    user_roles = await role_service.get_user_roles(user.id)

    roles_info = "\n".join([
        f"- {role.role} в компании ID {role.company_id}"
        for role in user_roles
    ]) if user_roles else "Нет назначенных ролей"

    profile_text = (
        f"👤 <b>Ваш профиль</b>\n"
        f"▫️ ID: {user.id}\n"
        f"▫️ Имя: {user.first_name} {user.last_name}\n"
        f"▫️ Telegram ID: {user.id_tg}\n"
        f"▫️ Дата регистрации: {user.reg_date}\n\n"
        f"🔑 <b>Ваши роли:</b>\n{roles_info}"
    )
    await message.answer(profile_text, parse_mode="HTML")


@router.message(F.text == "Помощь")
async def help_command(message: Message):
    """Отправка справочной информации"""
    help_text = (
        "ℹ️ <b>Справка по боту</b>\n\n"
        "• <b>Получить купон</b> - получить персональный купон на скидку\n"
        "• <b>Мои купоны</b> - список ваших активных купонов\n"
        "• <b>Мой профиль</b> - ваша учетная запись\n"
        "• <b>Управление категориями</b> - управление категориями компаний\n\n"
        "Для партнеров:\n"
        "• <b>Сгенерировать купон</b> - создать новый купон для клиента\n"
        "• <b>Статистика</b> - просмотр аналитики\n"
        "• <b>Мои администраторы</b> - управление персоналом\n\n"
        "Для администраторов:\n"
        "• <b>Проверить подписку</b> - проверка подписки клиента\n"
        "• <b>Активировать купон</b> - активация купона при покупке"
    )
    await message.answer(help_text, parse_mode="HTML")
