from sqlalchemy import (
    Column, Integer, PrimaryKeyConstraint, String, ForeignKey, Boolean, DateTime,
    DECIMAL, TIMESTAMP, Date, Enum, BigInteger, Text, SmallInteger, CHAR, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .db_session import Base

class CouponStatusHelper:
    STATUS_MAP = {
        "active": 1,
        "used": 2,
        "expired": 3,
        "cancelled": 4
    }

    @staticmethod
    def get_status_id(status_name: str) -> int:
        return CouponStatusHelper.STATUS_MAP.get(
            status_name.lower(),
            CouponStatusHelper.STATUS_MAP["active"]
        )

class ActionLog(Base):
    __tablename__ = 'ACTION_LOGS'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('USERS.id', ondelete='SET NULL'), nullable=True)
    action_type = Column(String(50), nullable=True, comment="Тип действия")
    entity_id = Column(Integer, nullable=True, comment="ID сущности")
    timestamp = Column(DateTime, comment="Время действия")  
    
    user = relationship("User", lazy="selectin")

class CompanyCategory(Base):
    __tablename__ = 'COMPANY_CATEGORY'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(256), nullable=False, comment="Название категории")
    
    loc_cats = relationship("LocCat", back_populates="category", lazy="selectin")
    
    companies = relationship(
        "Company",
        secondary="LOC_CATS",
        back_populates="categories",
        lazy="selectin"
    )
    
    comp_locations = relationship(
        "CompLocation",
        secondary="LOC_CATS",
        back_populates="categories",
        lazy="selectin"
    )

class LocCat(Base):
    __tablename__ = 'LOC_CATS'
    __table_args__ = ()
    
    comp_id = Column(Integer, ForeignKey('COMPANIES.id_comp', ondelete='CASCADE'))
    id_location = Column(Integer, ForeignKey('COMP_LOCATIONS.id_location', ondelete='CASCADE'))
    id_category = Column(BigInteger, ForeignKey('COMPANY_CATEGORY.id', ondelete='CASCADE'))
    
    company = relationship("Company", back_populates="loc_cats", lazy="selectin")
    location = relationship("CompLocation", back_populates="loc_cats", lazy="selectin")
    category = relationship("CompanyCategory", back_populates="loc_cats", lazy="selectin")
    
    __mapper_args__ = {
        'primary_key': [comp_id, id_location, id_category]
    }

class User(Base):
    __tablename__ = 'USERS'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    id_tg = Column(BigInteger, unique=True, nullable=False, comment="Telegram ID")
    user_name = Column(String(255), comment="Username в Telegram")
    first_name = Column(String(255), nullable=False, comment="Имя")
    last_name = Column(String(255), nullable=False, comment="Фамилия")
    tel_num = Column(CHAR(11), nullable=False, comment="Телефон (11 цифр)")
    reg_date = Column(Date, nullable=False, server_default=func.current_date(), comment="Дата регистрации")
    role = Column(String(50), default='client', comment="Базовая роль")
    
    issued_coupons = relationship(
        "Coupon",
        foreign_keys="Coupon.issued_by",
        back_populates="issuer",
        lazy="selectin"
    )
    used_coupons = relationship(
        "Coupon",
        foreign_keys="Coupon.used_by",
        back_populates="user",
        lazy="selectin"
    )
    client_coupons = relationship(
        "Coupon",
        foreign_keys="Coupon.client_id",
        back_populates="client",
        lazy="selectin"
    )
    roles = relationship(
        "UserRole",
        primaryjoin="User.id_tg == foreign(UserRole.user_id)",
        back_populates="user_rel",
        lazy="selectin"
    )
    action_logs = relationship(
        "ActionLog",
        back_populates="user",
        lazy="selectin"
    )

class Company(Base):
    __tablename__ = 'COMPANIES'
    
    id_comp = Column(Integer, primary_key=True, autoincrement=True)
    Name_comp = Column(String(255), nullable=False, comment="Название компании")
    
    categories = relationship(
        "CompanyCategory",
        secondary="LOC_CATS",
        back_populates="companies",
        lazy="selectin"
    )
    
    locations = relationship(
        "CompLocation",
        back_populates="company",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    coupon_types = relationship(
        "CouponType",
        back_populates="company",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    # Удалено отношение tg_groups
    loc_cats = relationship(
        "LocCat",
        back_populates="company",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

class CompLocation(Base):
    __tablename__ = 'COMP_LOCATIONS'
    
    id_location = Column(Integer, primary_key=True, autoincrement=True)
    id_comp = Column(Integer, ForeignKey('COMPANIES.id_comp', ondelete='CASCADE'), nullable=False, comment="ID компании")
    name_loc = Column(String(255), nullable=False, comment="Название локации")
    city = Column(String(512), nullable=False, comment="Город")
    address = Column(String(255), comment="Адрес")
    map_url = Column(Text, comment="URL карты")
    
    company = relationship(
        "Company",
        back_populates="locations",
        lazy="selectin"
    )
    coupon_types = relationship(
        "CouponType",
        back_populates="location",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    # Удалено отношение tg_groups
    used_coupons = relationship(
        "Coupon",
        back_populates="used_location",
        lazy="selectin"
    )
    loc_cats = relationship(
        "LocCat",
        back_populates="location",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    categories = relationship(
        "CompanyCategory",
        secondary="LOC_CATS",
        back_populates="comp_locations",
        lazy="selectin"
    )

class UserRole(Base):
    __tablename__ = 'USERS_ROLES'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, comment="Telegram ID пользователя")
    role = Column(Enum('admin', 'partner', 'client', 'tech_admin', name='user_roles_enum'),
                nullable=False, comment="Роль")
    company_id = Column(Integer, ForeignKey('COMPANIES.id_comp', ondelete='CASCADE'), nullable=False, comment="ID компании")
    location_id = Column(Integer, ForeignKey('COMP_LOCATIONS.id_location', ondelete='SET NULL'), comment="ID локации")
    start_date = Column(Date, nullable=False, server_default=func.current_date(), comment="Начало действия")
    end_date = Column(Date, nullable=False, comment="Окончание действия")
    changed_by = Column(BigInteger, nullable=False, comment="Telegram ID изменившего")
    changed_date = Column(DateTime, server_default=func.now(), comment="Дата изменения")
    is_locked = Column(Boolean, default=False, comment="Блокировка роли")
    
    user_rel = relationship(
        "User",
        primaryjoin="UserRole.user_id == User.id_tg",
        foreign_keys=[user_id],
        back_populates="roles",
        lazy="selectin"
    )
    changer_rel = relationship(
        "User",
        primaryjoin="UserRole.changed_by == User.id_tg",
        foreign_keys=[changed_by],
        lazy="selectin"
    )
    company = relationship("Company", lazy="selectin")
    location = relationship("CompLocation", lazy="selectin")

class CouponType(Base):
    __tablename__ = 'COUPON_TYPES'
    
    id_coupon_type = Column(Integer, primary_key=True, autoincrement=True)
    code_prefix = Column(String(10), nullable=False, comment="Префикс кода")
    company_id = Column(Integer, ForeignKey('COMPANIES.id_comp', ondelete='CASCADE'), nullable=False, comment="ID компании")
    location_id = Column(Integer, ForeignKey('COMP_LOCATIONS.id_location', ondelete='CASCADE'), nullable=False, comment="ID локации")
    discount_percent = Column(DECIMAL(5, 2), nullable=False, comment="Процент скидки")
    commission_percent = Column(DECIMAL(5, 2), nullable=False, comment="Процент комиссии")
    require_all_groups = Column(Boolean, default=False, comment="Требовать все группы")
    usage_limit = Column(Integer, default=0, comment="Лимит использований")
    start_date = Column(Date, nullable=False, server_default=func.current_date(), comment="Начало действия")
    end_date = Column(Date, nullable=False, comment="Окончание действия")
    company_agent_id = Column(BigInteger, nullable=False, comment="ID агента компании")
    location_agent_id = Column(BigInteger, nullable=False, comment="ID агента локации")
    days_for_used = Column(BigInteger, nullable=False, comment="Дней для использования")
    agent_agree = Column(Boolean, default=False, nullable=False, comment="Подтверждение агента")
    
    company = relationship(
        "Company",
        back_populates="coupon_types",
        lazy="selectin"
    )
    location = relationship(
        "CompLocation",
        back_populates="coupon_types",
        lazy="selectin"
    )
    coupons = relationship(
        "Coupon",
        back_populates="coupon_type",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    # Удалено отношение group_coupons

class CouponStatus(Base):
    __tablename__ = 'COUPON_STATUSES'
    
    id_status = Column(SmallInteger, primary_key=True, autoincrement=True, comment="ID статуса")
    name = Column(String(50), nullable=False, comment="Название статуса")
    
    coupons = relationship(
        "Coupon",
        back_populates="status",
        lazy="selectin"
    )
    
    @staticmethod
    def get_status_id(status_name: str) -> int:
        return CouponStatusHelper.get_status_id(status_name)

class Coupon(Base):
    __tablename__ = 'COUPONS'
    
    id_coupon = Column(Integer, primary_key=True, autoincrement=True, comment="ID купона")
    code = Column(String(50), unique=True, nullable=False, comment="Уникальный код")
    coupon_type_id = Column(Integer, ForeignKey('COUPON_TYPES.id_coupon_type', ondelete='CASCADE'), nullable=False, comment="ID типа")
    client_id = Column(Integer, ForeignKey('USERS.id', ondelete='CASCADE'), nullable=False, index=True, comment="ID клиента")
    start_date = Column(Date, nullable=False, server_default=func.current_date(), comment="Начало действия")
    end_date = Column(Date, nullable=False, comment="Окончание действия")
    issued_by = Column(Integer, ForeignKey('USERS.id', ondelete='CASCADE'), nullable=False, comment="Кто выдал")
    used_by = Column(Integer, ForeignKey('USERS.id', ondelete='SET NULL'), comment="Кто использовал")
    status_id = Column(SmallInteger, ForeignKey('COUPON_STATUSES.id_status'), default=1, nullable=False, comment="Статус")
    order_amount = Column(DECIMAL(10, 2), comment="Сумма заказа")
    location_used = Column(Integer, ForeignKey('COMP_LOCATIONS.id_location', ondelete='SET NULL'), comment="Место использования")
    used_at = Column(TIMESTAMP, comment="Время использования")
    company_used = Column(Integer, ForeignKey('COMPANIES.id_comp', ondelete='SET NULL'), comment="Компания использования")
    
    coupon_type = relationship(
        "CouponType",
        back_populates="coupons",
        lazy="selectin"
    )
    client = relationship(
        "User",
        foreign_keys=[client_id],
        back_populates="client_coupons",
        lazy="selectin"
    )
    issuer = relationship(
        "User",
        foreign_keys=[issued_by],
        back_populates="issued_coupons",
        lazy="selectin"
    )
    user = relationship(
        "User",
        foreign_keys=[used_by],
        back_populates="used_coupons",
        lazy="selectin"
    )
    status = relationship(
        "CouponStatus",
        back_populates="coupons",
        lazy="selectin"
    )
    used_location = relationship(
        "CompLocation",
        back_populates="used_coupons",
        lazy="selectin"
    )
    used_company = relationship(
        "Company",
        lazy="selectin"
    )

class Tag(Base):
    __tablename__ = 'TAGS'
    
    id_tag = Column(Integer, primary_key=True, autoincrement=True, comment="ID тега")
    tag_name = Column(String(255), nullable=False, comment="Название тега")
    entity_type = Column(Enum('coupon', 'user', 'company', name='entity_types'), nullable=False, comment="Тип сущности")
    entity_id = Column(Integer, nullable=False, comment="ID сущности")