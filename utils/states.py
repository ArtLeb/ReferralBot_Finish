from aiogram.fsm.state import StatesGroup, State


class Gen(StatesGroup):
    enter_coupon_code = State()
    enter_order_amount = State()
    select_group = State()
    add_partner_data = State()


class CreateLocationStates(StatesGroup):
    # Для управления компаниями
    get_loc_category = State()
    get_loc_address_url = State()
    get_loc_address = State()
    get_loc_city = State()
    get_comp_name = State()
    start_cr_loc = State()


class PartnerStates(StatesGroup):
    # Для управления компаниями
    get_new_admin_user_id = State()
    select_admin_menu = State()
    select_edit_fild_loc = State()
    edit_category_loc = State()
    process_comp_name = State()
    company_menu = State()
    edit_company_name = State()

    get_company_name = State()

    collabs_start_menu = State()

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
    edit_location = State()
    edit_location_select = State()
    select_location_action = State()
    edit_location_value = State()

    # Для управления администраторами
    add_admin_tg_id = State()

    # Для поиска агентов
    find_agent_query = State()

    # Для коллабораций
    create_collaboration_agent_id = State()
    create_collaboration_discount = State()

    generate_coupon_type = State()


class CollaborationStates(StatesGroup):
    collab_location_info = State()
    filter_comp_start_menu = State()
    filter_comp_menu = State()
    collab_menu = State()
    view_collaborations = State()
    choose_location = State()
    view_requests = State()


class CreateCouponTypeStates(StatesGroup):
    code_prefix = State()
    discount_percent = State()
    commission_percent = State()
    require_all_groups = State()
    usage_limit = State()
    start_date = State()
    end_date = State()
    days_for_used = State()
    confirm = State()


class AdminStates(StatesGroup):
    waiting_for_coupon_code = State()
    waiting_for_order_amount = State()


class RegistrationStates(StatesGroup):
    COMPANY_CATEGORY_RECORD = State()
    CHOOSING_ROLE = State()
    COMPANY_NAME = State()
    COMPANY_CATEGORY = State()
    CITY_SELECTION = State()
    COMPANY_ADDRESS = State()
    COMPANY_ADDRESS_URL = State()
