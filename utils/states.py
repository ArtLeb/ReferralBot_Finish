from aiogram.fsm.state import StatesGroup, State

class Gen(StatesGroup):
    enter_coupon_code = State()
    enter_order_amount = State()
    select_group = State()
    add_partner_data = State()

 # states.py
class PartnerStates(StatesGroup):
    # Для управления компаниями
    create_company_name = State()
    create_company_category = State()
    edit_company_select = State()
    edit_company_field = State()
    edit_company_value = State()
    
    # Для управления локациями
    add_location_city = State()
    add_location_address = State()
    add_location_name = State()
    edit_location_select = State()
    edit_location_field = State()
    edit_location_value = State()
    
    # Для управления администраторами
    add_admin_tg_id = State()
    
    # Для поиска агентов
    find_agent_query = State()
    
    # Для коллабораций
    create_collaboration_agent_id = State()
    create_collaboration_discount = State()
    
    
    generate_coupon_type = State() 

class AdminStates(StatesGroup):
    waiting_for_coupon_code = State()
    waiting_for_order_amount = State()