from aiogram import Bot

async def check_group_subscription(bot: Bot, user_id: int, group_id: int) -> bool:
    try:
        member = await bot.get_chat_member(group_id, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Ошибка при проверке подписки: {e}")
        return False