import logging

from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from handlers.common_handlers import partner_selected
from services.auth_service import AuthService
from services.role_service import RoleService
from utils.keyboards import main_menu
from utils.states import RegistrationStates

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("start"))
async def start(message: Message, session: AsyncSession, state: FSMContext):
    """Обработчик команды /start с регистрацией пользователя"""
    auth_service = AuthService(session)
    await auth_service.get_or_create_user(
        tg_id=message.from_user.id,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name or ""
    )
    await state.clear()
    role_service = RoleService(session)
    user_roles = await role_service.get_user_roles(message.from_user.id)

    if user_roles:
        await message.answer(
            "👋 Добро пожаловать в ReferralBot!",
            reply_markup=await main_menu(session, message.from_user.id)
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


@router.message(Command("regcomp"))
async def regcomp(message: Message, state: FSMContext):
    """Обработчик команды /start с регистрацией пользователя"""
    await partner_selected(message=message, state=state)


@router.message(Command("cancel"), ~StateFilter(default_state))
async def cancel_registration(message: Message, state: FSMContext):
    """Отмена процесса регистрации"""
    await state.clear()
    await message.answer(
        "❌ Регистрация отменена",
        reply_markup=ReplyKeyboardRemove()
    )
