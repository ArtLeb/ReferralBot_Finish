from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from services.user_service import get_or_create_user

router = Router()

@router.message(Command("start"))
async def start_cmd(message: Message):
    user = await get_or_create_user(
        tg_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )
    await message.answer(
        "👋 Добро пожаловать в ReferralBot!\n\n"
        "🚀 Я помогу вам управлять реферальными программами, "
        "скидками и партнерскими кампаниями.\n\n"
        "🔍 Для просмотра доступных команд используйте /help"
    )

@router.message(Command("help"))
async def help_cmd(message: Message, user_roles: list):
    # Формируем список доступных команд в зависимости от роли
    commands = [
        "🛠 Доступные команды:",
        "/coupons - Управление купонами",
        "/stats - Просмотр статистики"
    ]
    
    if any(role.gen_coups for role in user_roles):
        commands.append("/generate_coupon - Создать новый купон")
    
    if any(role.add_admins for role in user_roles):
        commands.append("/add_admin - Добавить администратора")
    
    await message.answer("\n".join(commands))