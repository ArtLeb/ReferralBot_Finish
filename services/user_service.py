import datetime
from utils.database.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

async def get_or_create_user(session: AsyncSession, tg_id: int, username: str, first_name: str, last_name: str):
    result = await session.execute(select(User).filter(User.id_tg == tg_id))
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(
            id_tg=tg_id,
            user_name=username,
            first_name=first_name,
            last_name=last_name,
            tel_num="",
            reg_date=datetime.now().date()
        )
        session.add(user)
        await session.commit()
    
    return user