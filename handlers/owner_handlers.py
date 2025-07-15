from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.role_service import RoleService
from services.user_service import UserService
from services.action_logger import ActionLogger
from sqlalchemy.ext.asyncio import AsyncSession
from utils.database.models import User
from typing import Optional

router = Router()

# Состояния для добавления партнера
class AddPartnerStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_company_id = State()
    waiting_for_location_id = State()

@router.message(F.text == "Добавить партнера")
async def add_partner_start(message: Message, state: FSMContext):
    await message.answer("Введите Telegram ID пользователя, которого хотите сделать партнером:")
    await state.set_state(AddPartnerStates.waiting_for_user_id)

@router.message(AddPartnerStates.waiting_for_user_id)
async def process_user_id(message: Message, state: FSMContext, session: AsyncSession):
    try:
        tg_id = int(message.text)
        await state.update_data(tg_id=tg_id)
        await message.answer("Введите ID компании для партнера:")
        await state.set_state(AddPartnerStates.waiting_for_company_id)
    except ValueError:
        await message.answer("❌ Некорректный ID. Пожалуйста, введите числовой Telegram ID.")

@router.message(AddPartnerStates.waiting_for_company_id)
async def process_company_id(message: Message, state: FSMContext, session: AsyncSession):
    try:
        company_id = int(message.text)
        await state.update_data(company_id=company_id)
        await message.answer("Введите ID локации (или отправьте 0, если не требуется):")
        await state.set_state(AddPartnerStates.waiting_for_location_id)
    except ValueError:
        await message.answer("❌ Некорректный ID компании. Пожалуйста, введите число.")

@router.message(AddPartnerStates.waiting_for_location_id)
async def process_location_id(message: Message, state: FSMContext, session: AsyncSession):
    try:
        location_id = int(message.text) if message.text != "0" else None
        user_data = await state.get_data()
        
        tg_id = user_data['tg_id']
        company_id = user_data['company_id']
        
        user_service = UserService(session)
        role_service = RoleService(session)
        logger = ActionLogger(session)
        
        # Получаем пользователя по Telegram ID
        user = await user_service.get_user_by_tg_id(tg_id)
        if not user:
            await message.answer(f"❌ Пользователь с ID {tg_id} не найден.")
            await state.clear()
            return
        
        # Назначаем роль 'partner'
        await role_service.assign_role_to_user(
            user_id=user.id,
            role_name='partner',
            company_id=company_id,
            location_id=location_id
        )
        
        # Логируем действие
        await logger.log_action(
            user_id=message.from_user.id,
            action_type='role_assigned',
            entity_id=user.id,
            details=f"Назначена роль partner в компании {company_id}"
        )
        
        await message.answer(
            f"✅ Пользователь {user.first_name} успешно добавлен как партнер в компанию ID {company_id}."
        )
        
    except ValueError:
        await message.answer("❌ Некорректный ID локации. Пожалуйста, введите число или 0.")
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {str(e)}")
    finally:
        await state.clear()

@router.message(F.text == "Статистика")
async def view_stats(message: Message, session: AsyncSession, user: User):
    role_service = RoleService(session)
    
    # Проверяем права пользователя
    if not await role_service.has_permission(user, "view_stats"):
        await message.answer("⛔ У вас нет прав для просмотра статистики")
        return
    
    try:
        # Получаем статистику
        stats = await role_service.get_system_stats()
        response = "📊 Статистика системы:\n"
        response += f"• Всего пользователей: {stats['total_users']}\n"
        response += f"• Всего компаний: {stats['total_companies']}\n"
        response += f"• Выдано купонов: {stats['total_coupons']}\n"
        response += f"• Использовано купонов: {stats['used_coupons']}"
        
        await message.answer(response)
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при получении статистики: {str(e)}")