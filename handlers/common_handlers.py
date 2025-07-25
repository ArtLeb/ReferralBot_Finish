from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from services.auth_service import AuthService
from services.role_service import RoleService
from services.company_service import CompanyService
from services.category_service import CategoryService
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from utils.database.models import LocCat

logger = logging.getLogger(__name__)
router = Router()

class RegistrationStates(StatesGroup):
    CHOOSING_ROLE = State()
    COMPANY_NAME = State()
    COMPANY_CATEGORY = State()
    CITY_SELECTION = State()
    COMPANY_ADDRESS = State()

async def main_menu(session: AsyncSession, user) -> ReplyKeyboardMarkup:
    """Создает главное меню в зависимости от роли пользователя"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="Мой профиль"))
    builder.row(KeyboardButton(text="Помощь"))
    
    role_service = RoleService(session)
    if await role_service.has_permission(user.id, "get_coupons"):
        builder.row(KeyboardButton(text="Получить купон"))
        builder.row(KeyboardButton(text="Мои купоны"))
    
    if await role_service.has_permission(user.id, "view_stats"):
        builder.row(KeyboardButton(text="Статистика"))
    
    if await role_service.has_permission(user.id, "gen_coupons"):
        builder.row(KeyboardButton(text="Сгенерировать купон"))
    
    if await role_service.has_permission(user.id, "add_admins"):
        builder.row(KeyboardButton(text="Мои администраторы"))
    
    if await role_service.has_permission(user.id, "add_partners"):
        builder.row(KeyboardButton(text="Добавить партнера"))
    
    if await role_service.has_permission(user.id, "check_subscription"):
        builder.row(KeyboardButton(text="Проверить подписку"))
        builder.row(KeyboardButton(text="Активировать купон"))
    
    if await role_service.has_permission(user.id, "manage_categories"):
        builder.row(KeyboardButton(text="Управление категориями"))
    
    return builder.as_markup(
        resize_keyboard=True,
        input_field_placeholder="Выберите действие из меню"
    )

@router.message(Command("start"))
async def start(message: Message, session: AsyncSession, state: FSMContext):
    """Обработчик команды /start с регистрацией пользователя"""
    auth_service = AuthService(session)
    user = await auth_service.get_or_create_user(
        tg_id=message.from_user.id,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name or ""
    )
    
    role_service = RoleService(session)
    user_roles = await role_service.get_user_roles(user.id_tg)
    
    if user_roles:
        await message.answer(
            "👋 Добро пожаловать в ReferralBot!",
            reply_markup=await main_menu(session, user)
        )
    else:
        await state.set_state(RegistrationStates.CHOOSING_ROLE)
        builder = ReplyKeyboardBuilder()
        builder.row(KeyboardButton(text="Я клиент"))
        builder.row(KeyboardButton(text="Я партнер (компания)"))
        await message.answer(
            "👋 Добро пожаловать! Пожалуйста, выберите тип вашего аккаунта:\n\n"
            "ℹ️ Один пользователь может создать до 5 компаний",
            reply_markup=builder.as_markup(resize_keyboard=True)
        )

@router.message(RegistrationStates.CHOOSING_ROLE, F.text == "Я клиент")
async def client_selected(message: Message, session: AsyncSession, state: FSMContext, user):
    """Обработчик выбора роли клиента"""
    role_service = RoleService(session)
    await role_service.assign_role_to_user(
        tg_id=user.id_tg,
        role_name='client',
        company_id=1  # ID системной компании
    )
    await state.clear()
    await message.answer(
        "✅ Вы зарегистрированы как клиент!",
        reply_markup=await main_menu(session, user)
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
async def process_company_name(message: Message, state: FSMContext, session: AsyncSession):
    """Сохранение названия компании"""
    await state.update_data(company_name=message.text)
    await state.set_state(RegistrationStates.COMPANY_CATEGORY)
    
    # Получение списка категорий
    category_service = CategoryService(session)
    categories = await category_service.get_all_categories()
    
    if not categories:
        await message.answer("⚠️ Категории не найдены. Обратитесь к администратору.")
        await state.clear()
        return
    
    # Создание клавиатуры с категориями
    builder = ReplyKeyboardBuilder()
    for category in categories:
        builder.add(KeyboardButton(text=category.name))
    builder.adjust(2)
    await message.answer("Выберите категорию компании:", reply_markup=builder.as_markup(resize_keyboard=True))

@router.message(RegistrationStates.COMPANY_CATEGORY)
async def process_company_category(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка выбора категории компании"""
    category_service = CategoryService(session)
    category = await category_service.get_category_by_name(message.text)
    
    if not category:
        await message.answer("❌ Пожалуйста, выберите категорию из списка:")
        return
    
    await state.update_data(company_category_id=category.id)
    await state.set_state(RegistrationStates.CITY_SELECTION)
    await message.answer("Введите город расположения компании:", reply_markup=ReplyKeyboardRemove())

@router.message(RegistrationStates.CITY_SELECTION)
async def process_city(message: Message, state: FSMContext):
    """Сохранение города компании и запрос адреса"""
    await state.update_data(city=message.text)
    await state.set_state(RegistrationStates.COMPANY_ADDRESS)
    await message.answer("Введите адрес компании:")

@router.message(RegistrationStates.COMPANY_ADDRESS)
async def process_company_address(message: Message, state: FSMContext, session: AsyncSession, user):
    """Завершение регистрации компании с гарантией создания локации"""
    data = await state.get_data()
    company_service = CompanyService(session)
    
    try:
        # Создаем компанию
        company = await company_service.create_company(
            name=data['company_name']
        )
        
        # Гарантированно создаем локацию
        location = await company_service.create_location(
            company_id=company.id_comp,
            city=data['city'],
            address=message.text,
            name_loc=data['company_name']  # Используем название компании
        )
        
        # Связываем категорию с локацией
        loc_cat = LocCat(
            comp_id=company.id_comp,
            id_location=location.id_location,
            id_category=data['company_category_id']
        )
        session.add(loc_cat)
        await session.commit()
        
        # Назначаем роль партнера используя telegram ID
        role_service = RoleService(session)
        await role_service.assign_role_to_user(
            tg_id=user.id_tg,  # Передаем telegram ID
            role_name='partner',
            company_id=company.id_comp,
            location_id=location.id_location  # Гарантированно передаем ID локации
        )
        
        await state.clear()
        await message.answer(
            f"✅ Компания {company.Name_comp} успешно зарегистрирована!",
            reply_markup=await main_menu(session, user)
        )
    
    except Exception as e:
        logger.error(f"Ошибка регистрации компании: {e}")
        await session.rollback()
        await message.answer("⚠️ Произошла ошибка при регистрации компании. Попробуйте позже.")

@router.message(F.text == "Мой профиль")
async def my_profile(message: Message, session: AsyncSession, user):
    """Отображение профиля пользователя"""
    role_service = RoleService(session)
    user_roles = await role_service.get_user_roles(user.id_tg)
    
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