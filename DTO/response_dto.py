from pydantic import BaseModel
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

# --------------------------------------------------
#  DTO для всех моделей
# --------------------------------------------------

class UserBase(BaseModel):
    """схема для пользователя"""
    id: int
    id_tg: int
    user_name: Optional[str] = None
    first_name: str
    last_name: str
    tel_num: str
    reg_date: date
    role: str

    class Config:
        orm_mode = True

class CompanyBase(BaseModel):
    """схема для компании"""
    id_comp: int
    Name_comp: str

    class Config:
        orm_mode = True

class CompLocationBase(BaseModel):
    """ схема для локации компании"""
    id_location: int
    id_comp: int
    name_loc: str
    address: Optional[str] = None

    class Config:
        orm_mode = True

class RoleBase(BaseModel):
    """ схема для роли"""
    id_role: int
    name_role: str
    add_clients: bool
    add_partners: bool
    add_admins: bool
    add_groups: bool
    gen_coupons: bool
    set_discount: bool
    set_commission: bool
    check_subscription: bool
    get_coupons: bool
    view_stats: bool

    class Config:
        orm_mode = True

class UserRoleBase(BaseModel):
    """ схема для связи пользователь-роль"""
    id: int
    user_id: int
    role_id: int
    company_id: int
    location_id: Optional[int] = None
    start_date: date
    end_date: date
    changed_by: int
    changed_date: datetime
    is_locked: bool

    class Config:
        orm_mode = True

# Новые DTO модели
class ActionLogBase(BaseModel):
    """схема для логов действий"""
    id: int
    user_id: Optional[int] = None
    action_type: Optional[str] = None
    entity_id: Optional[int] = None
    timestamp: datetime

    class Config:
        orm_mode = True

class CompanyCategoryBase(BaseModel):
    """схема для категорий компаний"""
    id: int
    name: str

    class Config:
        orm_mode = True

class LocCatBase(BaseModel):
    """схема связи локаций и категорий"""
    comp_id: int
    id_location: int
    id_category: int

    class Config:
        orm_mode = True

class TagBase(BaseModel):
    """схема для тега"""
    id_tag: int
    tag_name: str
    entity_type: str
    entity_id: int

    class Config:
        orm_mode = True

# Обновленная схема типа купона
class CouponTypeBase(BaseModel):
    """ схема для типа купона"""
    id_coupon_type: int
    code_prefix: str
    company_id: int
    location_id: int
    discount_percent: Decimal
    commission_percent: Decimal
    require_all_groups: bool
    usage_limit: int
    start_date: date
    end_date: date
    # Новые поля
    company_agent_id: int
    location_agent_id: int
    days_for_used: int
    agent_agree: bool

    class Config:
        orm_mode = True

class TgGroupBase(BaseModel):
    """ схема для Telegram группы"""
    id_tg_group: int
    group_id: int
    company_id: int
    location_id: int
    name: str
    is_active: bool

    class Config:
        orm_mode = True

class GroupCouponBase(BaseModel):
    """ схема для связи группа-купон"""
    id: int
    coupon_type_id: int
    group_id: int

    class Config:
        orm_mode = True

class CouponStatusBase(BaseModel):
    """ схема для статуса купона"""
    id_status: int
    name: str

    class Config:
        orm_mode = True

class CouponBase(BaseModel):
    """ схема для купона"""
    id_coupon: int
    code: str
    coupon_type_id: int
    client_id: int
    start_date: date
    end_date: date
    issued_by: int
    used_by: Optional[int] = None
    status_id: int
    order_amount: Optional[Decimal] = None
    location_used: Optional[int] = None
    used_at: Optional[datetime] = None
    company_used: Optional[int] = None

    class Config:
        orm_mode = True

class SubscriptionBase(BaseModel):
    """ схема для подписки"""
    id_subscription: int
    company_id: int
    location_id: int
    start_date: date
    end_date: date
    is_active: bool

    class Config:
        orm_mode = True

# --------------------------------------------------
# Расширенные DTO с отношениями
# --------------------------------------------------

class UserResponse(UserBase):
    """Расширенная схема пользователя с отношениями"""
    roles: List[UserRoleBase] = []
    issued_coupons: List[CouponBase] = []
    used_coupons: List[CouponBase] = []
    client_coupons: List[CouponBase] = []
    action_logs: List[ActionLogBase] = []

class CompanyResponse(CompanyBase):
    """Расширенная схема компании с отношениями"""
    locations: List[CompLocationBase] = []
    coupon_types: List[CouponTypeBase] = []
    subscriptions: List[SubscriptionBase] = []
    tg_groups: List[TgGroupBase] = []
    loc_cats: List[LocCatBase] = []

class CompLocationResponse(CompLocationBase):
    """Расширенная схема локации с отношениями"""
    company: CompanyBase
    coupon_types: List[CouponTypeBase] = []
    tg_groups: List[TgGroupBase] = []
    subscriptions: List[SubscriptionBase] = []
    used_coupons: List[CouponBase] = []
    loc_cats: List[LocCatBase] = []

class RoleResponse(RoleBase):
    """Расширенная схема роли с отношениями"""
    user_roles: List[UserRoleBase] = []

class UserRoleResponse(UserRoleBase):
    """Расширенная схема связи пользователь-роль с отношениями"""
    user: UserBase
    role: RoleBase
    company: CompanyBase
    location: Optional[CompLocationBase] = None
    changer: UserBase

class CouponTypeResponse(CouponTypeBase):
    """Расширенная схема типа купона с отношениями"""
    company: CompanyBase
    location: CompLocationBase
    coupons: List[CouponBase] = []
    group_coupons: List[GroupCouponBase] = []

class TgGroupResponse(TgGroupBase):
    """Расширенная схема Telegram группы с отношениями"""
    company: CompanyBase
    location: CompLocationBase
    group_coupons: List[GroupCouponBase] = []

class GroupCouponResponse(GroupCouponBase):
    """Расширенная схема связи группа-купон с отношениями"""
    coupon_type: CouponTypeBase
    group: TgGroupBase

class CouponStatusResponse(CouponStatusBase):
    """Расширенная схема статуса купона с отношениями"""
    coupons: List[CouponBase] = []

class CouponResponse(CouponBase):
    """Расширенная схема купона с отношениями"""
    coupon_type: CouponTypeBase
    client: UserBase
    issuer: UserBase
    user: Optional[UserBase] = None
    status: CouponStatusBase
    used_location: Optional[CompLocationBase] = None
    used_company: Optional[CompanyBase] = None

class SubscriptionResponse(SubscriptionBase):
    """Расширенная схема подписки с отношениями"""
    company: CompanyBase
    location: CompLocationBase

class ActionLogResponse(ActionLogBase):
    """Расширенная схема лога действий"""
    user: Optional[UserBase] = None

class CompanyCategoryResponse(CompanyCategoryBase):
    """Расширенная схема категории компании"""
    locations: List[LocCatBase] = []

class LocCatResponse(LocCatBase):
    """Расширенная схема связи локации и категории"""
    company: CompanyBase
    location: CompLocationBase
    category: CompanyCategoryBase

class TagResponse(TagBase):
    """Расширенная схема тега"""
    # Для тегов обычно не требуется расширенная информация
    pass

class CityBase(BaseModel):
    """Схема для города"""
    id: int
    name: str
    region: Optional[str] = None

class CouponDetailsResponse(CouponBase):
    """Расширенная схема купона с деталями"""
    discount_amount: Decimal
    commission_amount: Decimal
    qr_code: str