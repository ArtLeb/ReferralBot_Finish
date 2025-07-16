from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from services.company_service import CompanyService
from services.coupon_service import CouponService
from services.user_service import UserService
from sqlalchemy.ext.asyncio import AsyncSession
from utils.states import PartnerStates
from utils.database.models import User
from utils.keyboards import companies_keyboard, locations_keyboard
import logging
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import KeyboardButton

router = Router()
logger = logging.getLogger(__name__)

@router.message(F.text == "Мои компании")
async def list_companies(message: Message, session: AsyncSession):
    """Просмотр списка компаний партнера"""
    service = CompanyService(session)
    companies = await service.get_user_companies(message.from_user.id)
    
    if not companies:
        await message.answer("У вас пока нет компаний")
        return
    
    await message.answer(
        "🏢 Ваши компании:",
        reply_markup=companies_keyboard(companies)
    )

@router.callback_query(F.data.startswith("company_"))
async def select_company(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Выбор компании для управления"""
    company_id = int(callback.data.split("_")[1])
    service = CompanyService(session)
    company = await service.get_company_by_id(company_id)
    
    if not company:
        await callback.answer("Компания не найдена")
        return
    
    await state.update_data(company_id=company_id)
    company_info = (
        f"🏢 Компания: {company.Name_comp}\n"
        f"📍 Локаций: {len(company.locations)}"
    )
    
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="Управление локациями"))
    builder.row(KeyboardButton(text="Добавить администратора"))
    builder.row(KeyboardButton(text="Сгенерировать купон"))
    
    await callback.message.answer(company_info, reply_markup=builder.as_markup(resize_keyboard=True))
    await callback.answer()

@router.message(F.text == "Управление локациями")
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

@router.message(F.text == "Сгенерировать купон")
async def generate_coupon(message: Message, state: FSMContext, session: AsyncSession):
    """Генерация нового купона"""
    data = await state.get_data()
    company_id = data.get('company_id')
    
    if not company_id:
        await message.answer("❌ Сначала выберите компанию")
        return
    
    await state.set_state(PartnerStates.generate_coupon_type)
    await message.answer("Введите процент скидки для купона:")

@router.message(PartnerStates.generate_coupon_type)
async def process_coupon_discount(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка данных для генерации купона"""
    try:
        discount = float(message.text)
        if discount <= 0 or discount > 100:
            raise ValueError("Недопустимое значение")
        
        data = await state.get_data()
        company_id = data.get('company_id')
        
        coupon_service = CouponService(session)
        coupon = await coupon_service.create_coupon_type(
            company_id=company_id,
            discount_percent=discount
        )
        
        await message.answer(f"✅ Тип купона создан! Префикс: {coupon.code_prefix}")
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число от 1 до 100")
    except Exception as e:
        logger.error(f"Ошибка создания купона: {e}")
        await message.answer("❌ Не удалось создать тип купона")
        await state.clear()