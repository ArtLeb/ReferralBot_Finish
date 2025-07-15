from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import default_state
from services.subscription_service import SubscriptionService
from utils.database.models import User, CompanyCategory
from services.auth_service import AuthService
from services.role_service import RoleService
from services.company_service import CompanyService
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)
router = Router()

# Состояния для регистрации компании
class RegistrationStates(StatesGroup):
    """Состояния процесса регистрации компании"""
    CHOOSING_ROLE = State()          # Выбор роли (клиент/партнер)
    COMPANY_NAME = State()            # Ввод названия компании
    COMPANY_CATEGORY = State()        # Выбор категории компании
    COMPANY_LOCATION = State()        # Ввод локации компании
    COMPANY_ADDRESS = State()         # Ввод адреса компании

async def main_menu(session: AsyncSession, user: User) -> ReplyKeyboardMarkup:
    """
    Создает главное меню бота с основными кнопками в зависимости от роли пользователя
    """
    builder = ReplyKeyboardBuilder()
    role_service = RoleService(session)
    
    # Кнопки, доступные всем
    builder.row(KeyboardButton(text="Мой профиль"))
    builder.row(KeyboardButton(text="Помощь"))
    
    # Кнопки для клиентов
    builder.row(KeyboardButton(text="Получить купон"))
    builder.row(KeyboardButton(text="Мои купоны"))
    
    # Проверка прав перед добавлением кнопок
    if await role_service.has_permission(user, "view_stats"):
        builder.row(KeyboardButton(text="Статистика"))
    
    if await role_service.has_permission(user, "gen_coupons"):
        builder.row(KeyboardButton(text="Сгенерировать купон"))
    
    if await role_service.has_permission(user, "add_admins"):
        builder.row(KeyboardButton(text="Мои администраторы"))
    
    if await role_service.has_permission(user, "add_partners"):
        builder.row(KeyboardButton(text="Добавить партнера"))
    
    if await role_service.has_permission(user, "check_subscription"):
        builder.row(KeyboardButton(text="Проверить подписку"))
        builder.row(KeyboardButton(text="Активировать купон"))
    
    if await role_service.has_permission(user, "get_coupons"):
        builder.row(KeyboardButton(text="Получить QR"))
    
    return builder.as_markup(
        resize_keyboard=True,
        input_field_placeholder="Выберите действие из меню"
    )

@router.message(F.text == "/start")
async def start(message: Message, session: AsyncSession, state: FSMContext):
    """
    Обработчик команды /start с проверкой наличия пользователя в БД
    """
    auth_service = AuthService(session)
    
    # Получаем или создаем пользователя в БД
    user = await auth_service.get_or_create_user(
        tg_id=message.from_user.id,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name or ""
    )
    
    # Проверяем, есть ли у пользователя роли
    role_service = RoleService(session)
    user_roles = await role_service.get_user_roles(user.id)
    
    if user_roles:
        # У пользователя есть роли - показываем главное меню
        await message.answer(
            "👋 Добро пожаловать в ReferralBot!",
            reply_markup=await main_menu(session, user)
        )
    else:
        # У пользователя нет ролей - предлагаем выбрать тип аккаунта
        await state.set_state(RegistrationStates.CHOOSING_ROLE)
        builder = ReplyKeyboardBuilder()
        builder.row(KeyboardButton(text="Я клиент"))
        builder.row(KeyboardButton(text="Я партнер (компания)"))
        
        await message.answer(
            "👋 Добро пожаловать! Пожалуйста, выберите тип вашего аккаунта:\n\n"
            "ℹ️ Один пользователь может создать до 5 компаний",
            reply_markup=builder.as_markup(resize_keyboard=True)
        )

@router.message(Command("cancel"), ~StateFilter(default_state))
async def cancel_registration(message: Message, state: FSMContext):
    """
    Отменяет процесс регистрации компании и сбрасывает состояние
    """
    await state.clear()
    await message.answer(
        "❌ Регистрация отменена",
        reply_markup=ReplyKeyboardRemove()
    )

@router.message(RegistrationStates.CHOOSING_ROLE, F.text == "Я клиент")
async def client_selected(message: Message, session: AsyncSession, state: FSMContext, user: User):
    """
    Обработчик выбора роли клиента
    """
    role_service = RoleService(session)
    
    # Назначаем роль клиента (надо сделать запись для категории клиентов системную компанию с ID=1(1, 'Системная компания', 0, 'system'))
    await role_service.assign_role_to_user(
        user_id=user.id,
        role_name='client',
        company_id=1  # ID системной компании для клиентов
    )
    
    await state.clear()
    await message.answer(
        "✅ Вы зарегистрированы как клиент!",
        reply_markup=await main_menu(session, user)
    )

@router.message(RegistrationStates.CHOOSING_ROLE, F.text == "Я партнер (компания)")
async def partner_selected(message: Message, state: FSMContext):
    """
    Обработчик выбора роли партнера
    """
    await state.set_state(RegistrationStates.COMPANY_NAME)
    await message.answer(
        "Введите название вашей компании:\n\n"
        "❕ Вы можете отменить регистрацию командой /cancel",
        reply_markup=ReplyKeyboardRemove()
    )

@router.message(RegistrationStates.COMPANY_NAME)
async def process_company_name(message: Message, state: FSMContext, session: AsyncSession):
    """
    Обработчик ввода названия компании
    """
    await state.update_data(company_name=message.text)
    await state.set_state(RegistrationStates.COMPANY_CATEGORY)
    
    try:
        # Загрузка категорий из БД
        result = await session.execute(select(CompanyCategory))
        categories = result.scalars().all()
        
        if not categories:
            await message.answer("⚠️ Категории компаний не найдены. Обратитесь к администратору.")
            await state.clear()
            return
            
        builder = ReplyKeyboardBuilder()
        for category in categories:
            builder.add(KeyboardButton(text=category.name))
        builder.adjust(2)
        
        await message.answer(
            "Выберите категорию компании:",
            reply_markup=builder.as_markup(resize_keyboard=True)
        )
    except Exception as e:
        logger.error(f"Ошибка загрузки категорий: {e}")
        await message.answer("⚠️ Ошибка загрузки категорий. Попробуйте позже.")
        await state.clear()

@router.message(RegistrationStates.COMPANY_CATEGORY)
async def process_company_category(message: Message, state: FSMContext, session: AsyncSession):
    """
    Обработчик выбора категории компании
    """
    try:
        # Проверяем существование категории в БД
        result = await session.execute(
            select(CompanyCategory).where(CompanyCategory.name == message.text)
        )
        category = result.scalar_one_or_none()
        
        if not category:
            await message.answer("❌ Пожалуйста, выберите категорию из списка:")
            return
        
        await state.update_data(company_category_id=category.id, company_category=message.text)
        await state.set_state(RegistrationStates.COMPANY_LOCATION)
        await message.answer(
            "Введите город, где находится компания:",
            reply_markup=ReplyKeyboardRemove()
        )
    except Exception as e:
        logger.error(f"Ошибка проверки категории: {e}")
        await message.answer("⚠️ Ошибка обработки категории. Попробуйте позже.")
        await state.clear()

@router.message(RegistrationStates.COMPANY_LOCATION)
async def process_company_location(message: Message, state: FSMContext):
    """
    Обработчик ввода локации компании
    """
    await state.update_data(company_location=message.text)
    await state.set_state(RegistrationStates.COMPANY_ADDRESS)
    await message.answer("Введите адрес компании:")

@router.message(RegistrationStates.COMPANY_ADDRESS)
async def process_company_address(
    message: Message, 
    state: FSMContext, 
    session: AsyncSession,
    user: User
):
    """
    Обработчик ввода адреса компании и завершение регистрации
    """
    # Получаем все сохраненные данные
    data = await state.get_data()
    company_service = CompanyService(session)
    
    try:
        # Создаем компанию
        company = await company_service.create_company(
            name=data['company_name'],
            category=data['company_category_id'],  # Используем ID категории
            owner_id=user.id
        )
        
        # Создаем локацию компании
        await company_service.create_location(
            company_id=company.id_comp,
            city=data['company_location'],
            address=message.text,
            name=f"Основная локация {company.Name_comp}"
        )
        
        # Назначаем пользователю роль партнера
        role_service = RoleService(session)
        await role_service.assign_role_to_user(
            user_id=user.id,
            role_name='partner',
            company_id=company.id_comp
        )
        
        await state.clear()
        await message.answer(
            f"✅ Компания {company.Name_comp} успешно зарегистрирована!",
            reply_markup=await main_menu(session, user)
        )
    except ValueError as e:
        # Обработка ошибки лимита компаний
        await state.clear()
        await message.answer(
            f"❌ {str(e)}",
            reply_markup=await main_menu(session, user)
        )
    except Exception as e:
        logger.error(f"Ошибка регистрации компании: {e}")
        await message.answer("⚠️ Произошла ошибка при регистрации компании. Попробуйте позже.")

@router.message(F.text == "Мой профиль")
async def my_profile(message: Message, session: AsyncSession, user: User):
    """
    Отображение профиля пользователя с расширенной информацией
    """
    role_service = RoleService(session)
    user_roles = await role_service.get_user_roles(user.id)
    
    # Формируем информацию о ролях
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

@router.message(F.text == "Проверить подписку")
async def check_subscription_command(message: Message, session: AsyncSession, user: User):
    """
    Обработчик для ручной проверки статуса подписки
    """
    # Получаем сервис подписок
    role_service = RoleService(session)
    subscription_service = SubscriptionService(session, role_service)
    
    # Проверяем подписку
    has_subscription = await subscription_service.check_subscription(user.id)
    
    if has_subscription:
        response = "✅ У вас есть активная подписка!"
    else:
        response = "❌ У вас нет активной подписки. Обратитесь к администратору."
    
    await message.answer(response)

@router.message(F.text == "Помощь")
async def help_command(message: Message):
    """
    Отправка справочной информации
    """
    help_text = (
        "ℹ️ <b>Справка по боту</b>\n\n"
        "• <b>Получить купон</b> - получить персональный купон на скидку\n"
        "• <b>Мои купоны</b> - список ваших активных купонов\n"
        "• <b>Мой профиль</b> - ваша учетная запись\n\n"
        "Для партнеров:\n"
        "• <b>Сгенерировать купон</b> - создать новый купон для клиента\n"
        "• <b>Статистика</b> - просмотр аналитики\n"
        "• <b>Мои администраторы</b> - управление персоналом\n\n"
        "Для администраторов:\n"
        "• <b>Проверить подписку</b> - проверка подписки клиента\n"
        "• <b>Активировать купон</b> - активация купона при покупке\n\n"
        "❕ Во время регистрации компании вы можете отменить процесс командой /cancel"
    )
    
    await message.answer(help_text, parse_mode="HTML")