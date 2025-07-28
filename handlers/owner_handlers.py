from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from services.role_service import RoleService
from services.user_service import UserService
from sqlalchemy.ext.asyncio import AsyncSession
from utils.database.models import User
from services.report_service import ReportService
from typing import Optional

router = Router()

class AddPartnerStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_company_id = State()
    waiting_for_location_id = State()

@router.message(F.text == "Добавить партнера")
async def add_partner_start(message: Message, state: FSMContext):
    """Начало процесса добавления партнера"""
    await message.answer("Введите Telegram ID пользователя:")
    await state.set_state(AddPartnerStates.waiting_for_user_id)

@router.message(AddPartnerStates.waiting_for_user_id)
async def process_user_id(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка ID пользователя"""
    try:
        tg_id = int(message.text)
        await state.update_data(tg_id=tg_id)
        await message.answer("Введите ID компании:")
        await state.set_state(AddPartnerStates.waiting_for_company_id)
    except ValueError:
        await message.answer("❌ Некорректный ID. Введите числовой Telegram ID")

@router.message(AddPartnerStates.waiting_for_company_id)
async def process_company_id(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка ID компании"""
    try:
        company_id = int(message.text)
        await state.update_data(company_id=company_id)
        await message.answer("Введите ID локации (или 0, если не требуется):")
        await state.set_state(AddPartnerStates.waiting_for_location_id)
    except ValueError:
        await message.answer("❌ Некорректный ID компании. Введите число")

@router.message(AddPartnerStates.waiting_for_location_id)
async def process_location_id(message: Message, state: FSMContext, session: AsyncSession):
    """Завершение добавления партнера"""
    try:
        location_id = int(message.text) if message.text != "0" else None
        user_data = await state.get_data()
        tg_id = user_data['tg_id']
        company_id = user_data['company_id']
        
        user_service = UserService(session)
        role_service = RoleService(session)
        
        user = await user_service.get_user_by_tg_id(tg_id)
        if not user:
            await message.answer(f"❌ Пользователь с ID {tg_id} не найден")
            await state.clear()
            return
        
        await role_service.assign_role_to_user(
            user_id=user.id,
            role_name='partner',
            company_id=company_id,
            location_id=location_id
        )
        
        await message.answer(f"✅ Пользователь {user.first_name} добавлен как партнер")
    except ValueError:
        await message.answer("❌ Некорректный ID локации. Введите число или 0")
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {str(e)}")
    finally:
        await state.clear()

@router.message(F.text == "Статистика")
async def view_stats(message: Message, session: AsyncSession):
    report_service = ReportService(session)
    stats = await report_service.get_system_stats()
    # Форматирование и отправка статистики

@router.message(F.text == "Отчет по купонам")
async def coupons_report(message: Message, session: AsyncSession):
    report_service = ReportService(session)
    report = await report_service.generate_coupons_report()
    await message.answer_document(report)
    report.close() 