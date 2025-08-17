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
from services.coupon_service import CouponService
from utils.keyboards import main_menu
from utils.states import RegistrationStates

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("start"))
async def start(message: Message, session: AsyncSession, state: FSMContext):
    """Обработчик команды /start с регистрацией пользователя и обработкой deep-link"""
    # Обработка deep-link для купона
    args = message.text.split()
    if len(args) > 1 and args[1].startswith('coupon_'):
        try:
            # Парсинг параметров: coupon_<collaboration>_<admin>_<location>
            params = args[1].split('_')
            collaboration_id = int(params[1])
            admin_tg_id = int(params[2])
            location_id = int(params[3])

            # Вызов функции выдачи купона
            coupon_service = CouponService(session)
            result = await coupon_service.issue_coupon_to_client(
                client_id=message.from_user.id,
                collaboration_id=collaboration_id,
                admin_tg_id=admin_tg_id,
                location_id=location_id
            )
            await message.answer(result)
            return  # Прерываем дальнейшую обработку
        except Exception as e:
            await message.answer(f"🚫 Ошибка активации купона: {str(e)}")
    
    # Стандартная обработка /start
    auth_service = AuthService(session)
    user, exists = await auth_service.get_or_create_user(
        tg_id=message.from_user.id,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name or "",
        username=message.from_user.username or ""
    )
    await state.clear()
    role_service = RoleService(session)
    user_roles = await role_service.get_user_roles(message.from_user.id)

    if user_roles or exists:
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