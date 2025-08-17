from sqlalchemy import (
    Column, Integer, PrimaryKeyConstraint, String, ForeignKey, Boolean, DateTime,
    DECIMAL, TIMESTAMP, Date, Enum, BigInteger, Text, SmallInteger
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .db_session import Base


# Класс для работы со статусами купонов
class CouponStatusHelper:
    """Вспомогательный класс для работы со статусами купонов"""
    # Сопоставление имен статусов с их ID
    STATUS_MAP = {
        "active": 1,
        "used": 2,
        "expired": 3,
        "cancelled": 4
    }

    @staticmethod
    def get_status_id(status_name: str) -> int:
        """
        Возвращает ID статуса по его имени
        
        Args:
            status_name: Название статуса (active, used и т.д.)
            
        Returns:
            ID статуса или 1 (active) по умолчанию
        """
        return CouponStatusHelper.STATUS_MAP.get(
            status_name.lower(),
            CouponStatusHelper.STATUS_MAP["active"]
        )


# Модель категорий компаний
class CompanyCategory(Base):
    __tablename__ = 'COMPANY_CATEGORY'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(256), nullable=False, comment="Название категории")

    # Связь с локациями через ассоциативную таблицу
    locations = relationship(
        "LocCat",
        back_populates="category",
        lazy="selectin"
    )


# Модель связи локаций и категорий
class LocCat(Base):
    __tablename__ = 'LOC_CATS'
    __table_args__ = (
        PrimaryKeyConstraint('comp_id', 'id_location', 'id_category'),
        {}
    )

    comp_id = Column(Integer, ForeignKey('COMPANIES.id_comp', ondelete='CASCADE'))
    id_location = Column(Integer, ForeignKey('COMP_LOCATIONS.id_location', ondelete='CASCADE'))
    id_category = Column(BigInteger, ForeignKey('COMPANY_CATEGORY.id', ondelete='CASCADE'))

    # Связи
    company = relationship("Company", lazy="selectin")
    location = relationship("CompLocation", lazy="selectin")
    category = relationship("CompanyCategory", back_populates="locations", lazy="selectin")


# Модель пользователя
class User(Base):
    __tablename__ = 'USERS'

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_tg = Column(BigInteger, unique=True, nullable=False, comment="Telegram ID пользователя")
    user_name = Column(String(255), comment="Username в Telegram")
    first_name = Column(String(255), nullable=False, comment="Имя пользователя")
    last_name = Column(String(255), nullable=False, comment="Фамилия пользователя")
    tel_num = Column(String(15), nullable=False, comment="Номер телефона")
    reg_date = Column(Date, nullable=False, server_default=func.current_date(), comment="Дата регистрации")
    role = Column(String(50), default='client', comment="Базовая роль пользователя")

    # Отношения
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
        back_populates="user",
        foreign_keys="UserRole.user_id",
        lazy="selectin"
    )


# Модель компании
class Company(Base):
    __tablename__ = 'COMPANIES'

    id_comp = Column(Integer, primary_key=True, autoincrement=True)
    Name_comp = Column(String(255), nullable=False, comment="Название компании")

    # Отношения
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

    loc_cats = relationship(
        "LocCat",
        back_populates="company",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    tg_groups = relationship(
        "TgGroup", back_populates="company"
    )


# Модель локации компании
class CompLocation(Base):
    __tablename__ = 'COMP_LOCATIONS'

    id_location = Column(Integer, primary_key=True, autoincrement=True)
    id_comp = Column(Integer, ForeignKey('COMPANIES.id_comp', ondelete='CASCADE'), nullable=False,
                     comment="ID компании")
    name_loc = Column(String(255), nullable=False, comment="Название локации")
    address = Column(String(255), comment="Адрес локации")
    map_url = Column(Text, comment="Ссылка Адреса локации на картах")
    city = Column(String(255), comment="Город")
    main_loc = Column(Boolean, default=False, comment="Главная локация")

    # Отношения
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


# Модель связи пользователь-роль
class UserRole(Base):
    __tablename__ = 'USERS_ROLES'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('USERS.id', ondelete='CASCADE'), nullable=False, comment="ID пользователя")
    role = Column(String(50), nullable=False, comment="Название роли (admin, partner, client, teach_admin )")
    company_id = Column(Integer, ForeignKey('COMPANIES.id_comp', ondelete='CASCADE'), nullable=False,
                        comment="ID компании")
    location_id = Column(Integer, ForeignKey('COMP_LOCATIONS.id_location', ondelete='SET NULL'), comment="ID локации")
    start_date = Column(Date, nullable=False, server_default=func.current_date(), comment="Дата начала роли")
    end_date = Column(Date, nullable=False, comment="Дата окончания роли")
    changed_by = Column(Integer, ForeignKey('USERS.id', ondelete='CASCADE'), nullable=False, comment="Кто изменил")
    changed_date = Column(DateTime, server_default=func.now(), comment="Дата изменения")
    is_locked = Column(Boolean, default=False, comment="Заблокирована ли роль")

    # Отношения
    user = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="roles",
        lazy="selectin"
    )

    company = relationship(
        "Company",
        lazy="selectin"
    )
    location = relationship(
        "CompLocation",
        lazy="selectin"
    )
    changer = relationship(
        "User",
        foreign_keys=[changed_by],
        lazy="selectin"
    )


# Модель типа купона
class CouponType(Base):
    __tablename__ = 'COUPON_TYPES'

    id_coupon_type = Column(Integer, primary_key=True, autoincrement=True)
    code_prefix = Column(String(10), nullable=False, comment="Префикс кода купона")

    company_id = Column(
        Integer,
        ForeignKey('COMPANIES.id_comp', ondelete='CASCADE'),
        nullable=False,
        comment="ID компании"
    )
    location_id = Column(
        Integer,
        ForeignKey('COMP_LOCATIONS.id_location', ondelete='CASCADE'),
        nullable=False,
        comment="ID локации"
    )

    discount_percent = Column(DECIMAL(5, 2), nullable=False, comment="Процент скидки")
    commission_percent = Column(DECIMAL(5, 2), nullable=False, comment="Процент комиссии")

    require_all_groups = Column(Boolean, default=False, nullable=True, comment="Требуются все группы")
    usage_limit = Column(Integer, default=0, nullable=True, comment="Лимит использования")

    start_date = Column(Date, nullable=False, server_default=func.current_date(), comment="Дата начала действия")
    end_date = Column(Date, nullable=False, comment="Дата окончания действия")

    company_agent_id = Column(BigInteger, nullable=False, comment="ID агента компании")
    location_agent_id = Column(BigInteger, nullable=False, comment="ID агента локации")
    days_for_used = Column(BigInteger, nullable=False, comment="Дней для использования")

    agent_agree = Column(Boolean, default=False, nullable=False, comment="Подтверждение агента")
    is_active = Column(Boolean, default=False, nullable=False, comment="Подтверждение агента")

    # --- Relationships ---
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
    group_coupons = relationship(
        "GroupCoupon",
        back_populates="coupon_type",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

# Модель Telegram группы
class TgGroup(Base):
    __tablename__ = 'TG_GROUPS'

    id_tg_group = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(BigInteger, nullable=False, comment="ID группы в Telegram")
    company_id = Column(Integer, ForeignKey('COMPANIES.id_comp', ondelete='CASCADE'), nullable=False,
                        comment="ID компании")
    name = Column(String(255), nullable=False, comment="Название группы")
    is_active = Column(Boolean, default=True, comment="Активна ли группа")

    # Отношения

    group_coupons = relationship(
        "GroupCoupon",
        back_populates="group",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    company = relationship(
        "Company",
        back_populates="tg_groups",
        lazy="joined"  
    )


# Модель связи группа-купон
class GroupCoupon(Base):
    __tablename__ = 'GROUP_COUPONS'

    id = Column(Integer, primary_key=True, autoincrement=True)
    coupon_type_id = Column(Integer, ForeignKey('COUPON_TYPES.id_coupon_type', ondelete='CASCADE'), nullable=False,
                            comment="ID типа купона")
    group_id = Column(Integer, ForeignKey('TG_GROUPS.id_tg_group', ondelete='CASCADE'), nullable=False,
                      comment="ID группы")

    # Отношения
    coupon_type = relationship(
        "CouponType",
        back_populates="group_coupons",
        lazy="selectin"
    )
    group = relationship(
        "TgGroup",
        back_populates="group_coupons",
        lazy="selectin"
    )


# Модель статуса купона
class CouponStatus(Base):
    __tablename__ = 'COUPON_STATUSES'

    id_status = Column(SmallInteger, primary_key=True, autoincrement=True, comment="ID статуса")
    name = Column(String(50), nullable=False, comment="Название статуса")

    # Отношения
    coupons = relationship(
        "Coupon",
        back_populates="status",
        lazy="selectin"
    )

    @staticmethod
    def get_status_id(status_name: str) -> int:
        """
        Получает ID статуса по его имени
        
        Args:
            status_name: Название статуса (active, used и т.д.)
            
        Returns:
            ID статуса или 1 (active) по умолчанию
        """
        return CouponStatusHelper.get_status_id(status_name)


# Модель купона
class Coupon(Base):
    __tablename__ = 'COUPONS'

    id_coupon = Column(Integer, primary_key=True, autoincrement=True, comment="ID купона")
    code = Column(String(50), unique=True, nullable=False, comment="Уникальный код купона")
    coupon_type_id = Column(Integer, ForeignKey('COUPON_TYPES.id_coupon_type', ondelete='CASCADE'), nullable=False,
                            comment="ID типа купона")
    client_id = Column(Integer, ForeignKey('USERS.id', ondelete='CASCADE'), nullable=False, comment="ID клиента")
    start_date = Column(Date, nullable=False, server_default=func.current_date(), comment="Дата начала действия")
    end_date = Column(Date, nullable=False, comment="Дата окончания действия")
    issued_by = Column(Integer, ForeignKey('USERS.id', ondelete='CASCADE'), nullable=False, comment="Кто выдал купон")
    used_by = Column(Integer, ForeignKey('USERS.id', ondelete='SET NULL'), comment="Кто использовал купон")
    status_id = Column(SmallInteger, ForeignKey('COUPON_STATUSES.id_status'), default=1, comment="Статус купона")
    order_amount = Column(DECIMAL(10, 2), comment="Сумма заказа")
    location_used = Column(Integer, ForeignKey('COMP_LOCATIONS.id_location', ondelete='SET NULL'),
                           comment="Где использован купон")
    used_at = Column(TIMESTAMP, comment="Когда использован купон")
    company_used = Column(Integer, ForeignKey('COMPANIES.id_comp', ondelete='SET NULL'),
                          comment="В какой компании использован")

    # Отношения
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


# Модель тега
class Tag(Base):
    __tablename__ = 'TAGS'

    id_tag = Column(Integer, primary_key=True, autoincrement=True, comment="ID тега")
    tag_name = Column(String(255), nullable=False, comment="Название тега")
    entity_type = Column(Enum('coupon', 'user', 'company', name='entity_types'), nullable=False, comment="Тип сущности")
    entity_id = Column(Integer, nullable=False, comment="ID сущности")

class City(Base):
    __tablename__ = 'CITY'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(512), nullable=False)
