from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator
from utils.config import config

# Базовый класс для моделей SQLAlchemy
Base = declarative_base()

# Создание асинхронного движка для подключения к MySQL
engine = create_async_engine(
    #  строка подключения для MySQL
    f"mysql+aiomysql://{config.DB_USERNAME}:{config.DB_PASSWORD}"
    f"@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}",
    echo=True,          # Логирование SQL-запросов
    pool_pre_ping=True, # Проверка соединения перед использованием
    poolclass=NullPool  # Отключение пула соединений для асинхронной работы
)

# Фабрика для создания асинхронных сессий
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,  # Используем асинхронную сессию
    autocommit=False,     # Ручное управление коммитами
    autoflush=False,      # Ручное управление сбросом сессии
    expire_on_commit=False # Объекты остаются доступными после коммита
)

# Генератор сессий для использования в зависимостях
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Генератор для предоставления сессии БД в контексте запроса"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()  # Фиксация изменений при успешном выполнении
        except Exception:
            await session.rollback()  # Откат при возникновении ошибки
            raise
        finally:
            await session.close()  # Закрытие сессии

# Раскомментированная функция инициализации БД
async def init_db():
    """Инициализация БД - создание таблиц"""
    async with engine.begin() as conn:
        # Создание всех таблиц, определенных в моделях
        await conn.run_sync(Base.metadata.create_all)

# Псевдоним для совместимости с существующим кодом
async_session = AsyncSessionLocal