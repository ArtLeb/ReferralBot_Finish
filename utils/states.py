from aiogram.fsm.state import StatesGroup, State

class Gen(StatesGroup):
    enter_coupon_code = State()
    enter_order_amount = State()
    select_group = State()
    add_partner_data = State()