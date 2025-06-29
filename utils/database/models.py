from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey, DECIMAL, TIMESTAMP, SmallInteger, Text
from sqlalchemy.orm import relationship, declarative_base
from .db_session import Base

Base = declarative_base()

class User(Base):
    __tablename__ = 'USERS'
    id = Column(Integer, primary_key=True, autoincrement=True)
    id_tg = Column(Integer, unique=True, nullable=False)
    user_name = Column(String(255))
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    tel_num = Column(String(11), nullable=False)
    reg_date = Column(Date, nullable=False)

    roles = relationship('UserRole', back_populates='user')
    coupons_received = relationship('CouponClient', foreign_keys='CouponClient.id_client', back_populates='client')
    coupons_used = relationship('CouponClient', foreign_keys='CouponClient.id_used_user', back_populates='used_user')

class Company(Base):
    __tablename__ = 'COMPANIES'
    id_comp = Column(Integer, primary_key=True, autoincrement=True)
    name_comp = Column(String(255))

    locations = relationship('CompanyLocation', back_populates='company')
    subscriptions = relationship('Subscription', back_populates='company')

class CompanyLocation(Base):
    __tablename__ = 'COMP_LOCATIONS'
    id_location = Column(Integer, primary_key=True)
    id_comp = Column(Integer, ForeignKey('COMPANIES.id_comp'), nullable=False)
    name_loc = Column(String(255), nullable=False)
    address = Column(String(255))

    company = relationship('Company', back_populates='locations')
    coupons = relationship('CouponType', back_populates='location')

class Role(Base):
    __tablename__ = 'ROLES'
    id_role = Column(Integer, primary_key=True, autoincrement=True)
    name_role = Column(String(255))
    add_clients = Column(Boolean)
    add_partners = Column(Boolean)
    add_admins = Column(Boolean)
    add_groups = Column(Boolean)
    gen_coups = Column(Boolean)
    set_disc = Column(Boolean)
    set_comiss = Column(Boolean)
    check_subscr = Column(Boolean)
    get_coups = Column(Boolean)
    stat = Column(Boolean)

    user_roles = relationship('UserRole', back_populates='role')

class UserRole(Base):
    __tablename__ = 'USERS_ROLES'
    id_tg = Column(Integer, ForeignKey('USERS.id_tg'), primary_key=True)
    id_role = Column(Integer, ForeignKey('ROLES.id_role'), primary_key=True)
    id_comp = Column(Integer, ForeignKey('COMPANIES.id_comp'), primary_key=True)
    id_location = Column(Integer, ForeignKey('COMP_LOCATIONS.id_location'))
    begda = Column(Date, primary_key=True)
    endda = Column(Date, nullable=False)
    changed_by = Column(Integer, ForeignKey('USERS.id_tg'), nullable=False)
    changed_date = Column(TIMESTAMP)
    locked = Column(Boolean, nullable=False)

    user = relationship('User', back_populates='roles')
    role = relationship('Role', back_populates='user_roles')
    company = relationship('Company')
    location = relationship('CompanyLocation')
    changed_by_user = relationship('User', foreign_keys=[changed_by])

class CouponType(Base):
    __tablename__ = 'COUPON_TYPES'
    id_coup = Column(Integer, primary_key=True, autoincrement=True)
    coup_code = Column(String(255), nullable=False, unique=True)
    partner_agent = Column(Integer, ForeignKey('COMPANIES.id_comp'), nullable=False)
    partner_cup_comp = Column(Integer, ForeignKey('COMPANIES.id_comp'), nullable=False)
    partner_cup_loc = Column(Integer, ForeignKey('COMP_LOCATIONS.id_location'), nullable=False)
    discount = Column(SmallInteger, nullable=False)
    commission = Column(SmallInteger, nullable=False)
    all_gr_subscription = Column(Boolean, nullable=False)
    usage_limit = Column(SmallInteger, nullable=False)
    begda = Column(Date, nullable=False)
    endda = Column(Date, nullable=False)

    location = relationship('CompanyLocation', back_populates='coupons')
    groups = relationship('GroupCoupon', back_populates='coupon')

class TelegramGroup(Base):
    __tablename__ = 'TG_GROUPS'
    id_tg_group = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String(255), nullable=False)
    id_comp = Column(Integer, ForeignKey('COMPANIES.id_comp'), nullable=False)
    id_loc = Column(Integer, ForeignKey('COMP_LOCATIONS.id_location'), nullable=False)
    name = Column(String(255), nullable=False)
    active = Column(Boolean, nullable=False)

    coupons = relationship('GroupCoupon', back_populates='group')

class GroupCoupon(Base):
    __tablename__ = 'GROUPS_COUPONS'
    id_coup = Column(Integer, ForeignKey('COUPON_TYPES.id_coup'), primary_key=True)
    id_tg_group = Column(Integer, ForeignKey('TG_GROUPS.id_tg_group'), primary_key=True)

    coupon = relationship('CouponType', back_populates='groups')
    group = relationship('TelegramGroup', back_populates='coupons')

class CouponClient(Base):
    __tablename__ = 'COUPON_CLIENT'
    id_coup = Column(Integer, ForeignKey('COUPON_TYPES.id_coup'), primary_key=True)
    id_client = Column(Integer, ForeignKey('USERS.id_tg'), primary_key=True)
    begda = Column(Date, nullable=False)
    endda = Column(Date, nullable=False)
    id_parent = Column(Integer, ForeignKey('USERS.id_tg'), nullable=False)
    id_used_user = Column(Integer, ForeignKey('USERS.id_tg'), nullable=False)
    id_stat = Column(SmallInteger, ForeignKey('STATUSES.id_stat'), nullable=False)
    order_sum = Column(DECIMAL(10, 2), nullable=False)
    location_used = Column(Integer, ForeignKey('COMP_LOCATIONS.id_location'), nullable=False)
    time_used = Column(TIMESTAMP, nullable=False)
    comp_used = Column(Integer, ForeignKey('COMPANIES.id_comp'), nullable=False)

    client = relationship('User', foreign_keys=[id_client], back_populates='coupons_received')
    used_user = relationship('User', foreign_keys=[id_used_user], back_populates='coupons_used')
    status = relationship('Status')
    location = relationship('CompanyLocation')
    company = relationship('Company')

class Status(Base):
    __tablename__ = 'STATUSES'
    id_stat = Column(SmallInteger, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)

class Subscription(Base):
    __tablename__ = 'SUBSCRIPTIONS'
    id_comp = Column(Integer, ForeignKey('COMPANIES.id_comp'), primary_key=True)
    id_location = Column(Integer, ForeignKey('COMP_LOCATIONS.id_location'), primary_key=True)
    begda = Column(Date, nullable=False)
    endda = Column(Date, nullable=False)
    is_active = Column(Boolean, nullable=False)

    company = relationship('Company', back_populates='subscriptions')
    location = relationship('CompanyLocation')

class Tag(Base):
    __tablename__ = 'TAGS'
    id_coup = Column(Integer, ForeignKey('COUPON_TYPES.id_coup'), primary_key=True)
    id_tg = Column(Integer, ForeignKey('USERS.id_tg'), primary_key=True)
    tag_text = Column(String(255), primary_key=True)