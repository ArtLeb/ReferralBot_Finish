# utils/database/__init__.py
from .db_session import (
    Base,
    engine,
    AsyncSessionLocal as async_session,  # Создаем псевдоним
    get_db,  init_db
)

# Явно экспортируем объекты
__all__ = ['Base', 'engine', 'async_session', 'get_db', 'init_db']