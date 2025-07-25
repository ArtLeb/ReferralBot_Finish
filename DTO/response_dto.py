from pydantic import BaseModel
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

class UserBase(BaseModel):
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
    id_comp: int
    Name_comp: str

    class Config:
        orm_mode = True

class CompLocationBase(BaseModel):
    id_location: int
    id_comp: int
    name_loc: str
    city: str
    address: Optional[str] = None
    map_url: Optional[str] = None

    class Config:
        orm_mode = True

class ActionLogBase(BaseModel):
    id: int
    user_id: Optional[int] = None
    action_type: Optional[str] = None
    entity_id: Optional[int] = None
    timestamp: datetime

    class Config:
        orm_mode = True

class CompanyCategoryBase(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True

class LocCatBase(BaseModel):
    comp_id: int
    id_location: int
    id_category: int

    class Config:
        orm_mode = True

class TagBase(BaseModel):
    id_tag: int
    tag_name: str
    entity_type: str
    entity_id: int

    class Config:
        orm_mode = True

class CouponTypeBase(BaseModel):
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
    company_agent_id: int
    location_agent_id: int
    days_for_used: int
    agent_agree: bool

    class Config:
        orm_mode = True

class TgGroupBase(BaseModel):
    id_tg_group: int
    group_id: int
    company_id: int
    location_id: int
    name: str
    is_active: bool

    class Config:
        orm_mode = True

class GroupCouponBase(BaseModel):
    id: int
    coupon_type_id: int
    group_id: int

    class Config:
        orm_mode = True

class CouponStatusBase(BaseModel):
    id_status: int
    name: str

    class Config:
        orm_mode = True

class CouponBase(BaseModel):
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

class UserRoleBase(BaseModel):
    id: int
    user_id: int
    role: str
    company_id: int
    location_id: Optional[int] = None
    start_date: date
    end_date: date
    changed_by: int
    changed_date: datetime
    is_locked: bool

    class Config:
        orm_mode = True

class UserResponse(UserBase):
    roles: List[UserRoleBase] = []
    issued_coupons: List[CouponBase] = []
    used_coupons: List[CouponBase] = []
    client_coupons: List[CouponBase] = []
    action_logs: List[ActionLogBase] = []

class CompanyResponse(CompanyBase):
    categories: List[CompanyCategoryBase] = [] 
    locations: List[CompLocationBase] = []
    coupon_types: List[CouponTypeBase] = []
    tg_groups: List[TgGroupBase] = []
    loc_cats: List[LocCatBase] = []

class CompLocationResponse(CompLocationBase):
    company: CompanyBase
    categories: List[CompanyCategoryBase] = []  
    coupon_types: List[CouponTypeBase] = []
    tg_groups: List[TgGroupBase] = []
    used_coupons: List[CouponBase] = []
    loc_cats: List[LocCatBase] = []

class CouponTypeResponse(CouponTypeBase):
    company: CompanyBase
    location: CompLocationBase
    coupons: List[CouponBase] = []
    group_coupons: List[GroupCouponBase] = []

class TgGroupResponse(TgGroupBase):
    company: CompanyBase
    location: CompLocationBase
    group_coupons: List[GroupCouponBase] = []

class GroupCouponResponse(GroupCouponBase):
    coupon_type: CouponTypeBase
    group: TgGroupBase

class CouponStatusResponse(CouponStatusBase):
    coupons: List[CouponBase] = []

class CouponResponse(CouponBase):
    coupon_type: CouponTypeBase
    client: UserBase
    issuer: UserBase
    user: Optional[UserBase] = None
    status: CouponStatusBase
    used_location: Optional[CompLocationBase] = None
    used_company: Optional[CompanyBase] = None

class ActionLogResponse(ActionLogBase):
    user: Optional[UserBase] = None

class CompanyCategoryResponse(CompanyCategoryBase):
    companies: List[CompanyBase] = []  
    locations: List[CompLocationBase] = [] 

class LocCatResponse(LocCatBase):
    company: CompanyBase
    location: CompLocationBase
    category: CompanyCategoryBase

class TagResponse(TagBase):
    pass

class CouponDetailsResponse(CouponBase):
    discount_amount: Decimal
    commission_amount: Decimal
    qr_code: str