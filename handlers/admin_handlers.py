from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.category_service import CategoryService
from services.coupon_service import CouponService
from services.user_service import UserService
from services.company_service import CompanyService
from sqlalchemy.ext.asyncio import AsyncSession
from utils.database.models import User, CompanyCategory
from utils.keyboards import categories_keyboard
import logging
from aiogram.filters import StateFilter, Command
from utils.states import AdminStates
import qrcode
from io import BytesIO
from utils.bot_obj import bot

router = Router()
logger = logging.getLogger(__name__)

class CategoryStates(StatesGroup):
    waiting_for_category_name = State()
    waiting_for_category_selection = State()

@router.message(F.text == "Управление категориями")
async def manage_categories(message: Message, session: AsyncSession):
    """Меню управления категориями компаний"""
    category_service = CategoryService(session)
    categories = await category_service.get_all_categories()
    
    if not categories:
        await message.answer("В системе пока нет категорий. Хотите добавить?")
        return
    
    await message.answer(
        "📂 Управление категориями компаний:",
        reply_markup=categories_keyboard(categories)
    )

@router.callback_query(F.data == "add_category")
async def add_category_start(callback: CallbackQuery, state: FSMContext):
    """Начало процесса добавления категории"""
    await callback.message.answer("Введите название новой категории:")
    await state.set_state(CategoryStates.waiting_for_category_name)
    await callback.answer()

@router.message(CategoryStates.waiting_for_category_name)
async def add_category_process(message: Message, state: FSMContext, session: AsyncSession):
    """Создание новой категории"""
    category_name = message.text.strip()
    if not category_name:
        await message.answer("❌ Название категории не может быть пустым")
        return
    
    category_service = CategoryService(session)
    
    try:
        existing = await category_service.get_category_by_name(category_name)
        if existing:
            await message.answer("❌ Категория с таким названием уже существует")
            return
        
        category = await category_service.create_category(category_name)
        await message.answer(f"✅ Категория '{category.name}' успешно добавлена!")
        
        categories = await category_service.get_all_categories()
        await message.answer(
            "📂 Обновленный список категорий:",
            reply_markup=categories_keyboard(categories)
        )
    except Exception as e:
        logger.error(f"Ошибка создания категории: {e}")
        await message.answer("❌ Произошла ошибка при создании категории")
    finally:
        await state.clear()

@router.message(F.text == "Активировать купон")
async def activate_coupon(message: Message, state: FSMContext):
    """Начало процесса активации купона"""
    await message.answer("Введите код купона:")
    await state.set_state(AdminStates.waiting_for_coupon_code)

@router.message(F.text, StateFilter(AdminStates.waiting_for_coupon_code))
async def process_coupon_activation(message: Message, state: FSMContext, session: AsyncSession):
    """Активация купона"""
    coupon_code = message.text.strip()
    coupon_service = CouponService(session)
    
    try:
        coupon = await coupon_service.get_coupon_by_code(coupon_code)
        if not coupon:
            await message.answer("❌ Купон не найден")
            await state.clear()
            return
        
        if coupon.status.name != "active":
            await message.answer(f"❌ Купон уже использован или истек срок действия")
            await state.clear()
            return
        
        await state.update_data(coupon_code=coupon_code)
        await state.set_state(AdminStates.waiting_for_order_amount)
        await message.answer("Введите сумму заказа:")
    except Exception as e:
        logger.error(f"Ошибка активации купона: {e}")
        await message.answer("❌ Ошибка при обработке купона")
        await state.clear()

@router.message(F.text, StateFilter(AdminStates.waiting_for_order_amount))
async def process_order_amount(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка суммы заказа для активации купона"""
    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError("Недопустимая сумма")
        
        data = await state.get_data()
        coupon_code = data['coupon_code']
        
        coupon_service = CouponService(session)
        await coupon_service.redeem_coupon(
            coupon_code=coupon_code,
            redeemed_by=message.from_user.id,
            amount=amount
        )
        
        await message.answer("✅ Купон успешно активирован!")
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите корректную сумму заказа")
    except Exception as e:
        logger.error(f"Ошибка активации купона: {e}")
        await message.answer("❌ Не удалось активировать купон")
        await state.clear()

@router.message(Command("get_coupon_qr"))
async def handle_get_coupon_qr(message: Message, session: AsyncSession):
    """Генерация QR-кода для выдачи купона"""
    # Проверка прав администратора
    user_service = UserService(session)
    if not await user_service.is_admin(message.from_user.id):
        await message.answer("❌ Только для администраторов")
        return

    # Парсинг аргументов
    args = message.text.split()
    if len(args) != 3:
        await message.answer("❗ Использование:\n`/get_coupon_qr <ID_купона> <ID_локации>`", parse_mode="Markdown")
        return

    try:
        collaboration_id = int(args[1])
        location_id = int(args[2])
    except ValueError:
        await message.answer("❌ Некорректные ID. Должны быть числа")
        return

    # Проверка существования купона и локации
    coupon_service = CouponService(session)
    if not await coupon_service.collaboration_exists(collaboration_id):
        await message.answer(f"❌ Купон {collaboration_id} не существует")
        return

    company_service = CompanyService(session)
    if not await company_service.location_exists(location_id):
        await message.answer(f"❌ Локация {location_id} не существует")
        return

    # Генерация deep-ссылки
    bot_username = (await bot.get_me()).username
    deep_link = f"https://t.me/{bot_username}?start=coupon_{collaboration_id}_{message.from_user.id}_{location_id}"
    
    # Создание QR-кода
    qr = qrcode.make(deep_link)
    img_bytes = BytesIO()
    qr.save(img_bytes, format='PNG')
    img_bytes.seek(0)

    # Отправка результата
    await message.answer_photo(
        photo=img_bytes,
        caption=f"✅ QR для выдачи купона:\n"
                f"• Купон: `{collaboration_id}`\n"
                f"• Локация: `{location_id}`\n"
                f"Ссылка: `{deep_link}`",
        parse_mode="Markdown"
    )