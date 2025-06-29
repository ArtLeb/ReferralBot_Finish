from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine


load_dotenv()

Base = declarative_base()


class SqlConfigBase:
    """Конфигурация подключения к MySQL"""

    def __init__(self):
        self.host: str = os.getenv("DB_HOST", "62.217.182.228")
        self.port: str = os.getenv("DB_PORT", "3306")
        self.username: str = os.getenv("DB_USERNAME", "art_leb")
        self.password: str = os.getenv("DB_PASSWORD", "QCK_vjv2Il")
        self.db_name: str = os.getenv("DB_NAME", "referal_bot")

    @property
    def url(self) -> str:
        """Формирует строку подключения к MySQL с драйвером pymysql"""
        return f"mysql+pymysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.db_name}?charset=utf8mb4"


# Создание объекта конфигурации
sql_config = SqlConfigBase()
database_uri: str = sql_config.url

# Создание движка SQLAlchemy
engine = create_engine(
    database_uri,
    pool_pre_ping=True,  # Проверяет соединение перед выполнением запроса
    pool_size=20,        # Размер пула соединений
    max_overflow=100,    # Количество дополнительных соединений сверх пула
    pool_recycle=3600,   # Перезапуск соединений каждый час
    pool_timeout=10,     # Таймаут ожидания соединения
    echo=False           # Выключить логирование SQL-запросов
)

# Фабрика сессий SQLAlchemy
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
