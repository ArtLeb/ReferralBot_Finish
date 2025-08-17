# keyboards.py
from typing import List, Union, Tuple

from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from services.role_service import RoleService
from utils.database.models import Company, CompLocation, CompanyCategory, User, UserRole, City, CouponType


async def main_menu(session: AsyncSession, user) -> ReplyKeyboardMarkup:
    """Создает главное меню в зависимости от роли пользователя"""
    builder = ReplyKeyboardBuilder()
    role_service = RoleService(session)

    user_roles = await role_service.get_user_roles(user)
    is_owner = await role_service.has_permission(user, 'owner')
    roles = list(map(lambda role: role.role, user_roles))

    # Кнопки для всех пользователей
    builder.row(KeyboardButton(text="Мои купоны"))

    if 'admin' in roles or 'partner' in roles:
        builder.row(KeyboardButton(text="Мои компании"))
        builder.row(KeyboardButton(text="Создать компанию"))
    if is_owner:
        builder.row(KeyboardButton(text="Помощь"))

    return builder.as_markup(
        resize_keyboard=True,
        input_field_placeholder="Выберите действие из меню"
    )


def companies_keyboard(companies: list[Company]):
    """Клавиатура для выбора компаний"""
    builder = InlineKeyboardBuilder()
    for company in companies:
        builder.button(
            text=company.Name_comp,
            callback_data=f"company_{company.id_comp}"
        )
    builder.adjust(1)
    return builder.as_markup()


def locations_keyboard(locations: list[CompLocation]):
    """Клавиатура для выбора локаций"""
    builder = InlineKeyboardBuilder()
    for location in locations:
        builder.button(
            text=location.name_loc,
            callback_data=f"location_{location.id_location}"
        )
    builder.button(
        text="Назад",
        callback_data=f"location_back"
    )
    builder.adjust(1)
    return builder.as_markup()


def categories_keyboard(categories: list[CompanyCategory]):
    """Клавиатура для выбора категорий"""
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.button(
            text=category.name,
            callback_data=f"category_{category.id}"
        )
    builder.button(text="➕ Добавить категорию", callback_data="add_category")
    builder.adjust(1, 2)
    return builder.as_markup()


def edit_company_fields_keyboard():
    """Клавиатура для редактирования компании"""
    builder = InlineKeyboardBuilder()
    fields = [
        ("Название", "name"),
        ("Категория", "category"),
        ("Удалить компанию", "delete")
    ]
    for text, field in fields:
        builder.button(text=text, callback_data=f"edit_company_{field}")
    builder.adjust(1)
    return builder.as_markup()


def edit_location_fields_keyboard():
    """Клавиатура для редактирования локации"""
    builder = InlineKeyboardBuilder()
    fields = [
        ("Название", "name"),
        ("Город", "city"),
        ("Адрес", "address"),
        ("Удалить локацию", "delete")
    ]
    for text, field in fields:
        builder.button(text=text, callback_data=f"edit_location_{field}")
    builder.adjust(1)
    return builder.as_markup()


def loc_categories_keyboard(
        categories: List[CompanyCategory],
        selected_category: Union[List[int], list],
        page: int = 0,
        per_page: int = 10
) -> InlineKeyboardMarkup:
    """Клавиатура для выбора категорий с пагинацией (2 колонки, 10 элементов)"""
    builder = InlineKeyboardBuilder()

    # Разбиваем на страницы
    total_pages = (len(categories) + per_page - 1) // per_page
    start_idx = page * per_page
    end_idx = start_idx + per_page
    paginated_categories = categories[start_idx:end_idx]

    # Добавляем кнопки категорий (в 2 колонки)
    row = []
    for i, category in enumerate(paginated_categories):
        text = f"🟢 {category.name}" if category.id in selected_category else category.name
        button = InlineKeyboardButton(
            text=text,
            callback_data=f"category_{category.id}"
        )
        row.append(button)

        # Каждые 2 кнопки — новая строка
        if len(row) == 2:
            builder.row(*row)
            row = []

    if row:  # Добавляем оставшуюся кнопку (если нечетное число)
        builder.row(*row)

    # Ряд пагинации
    pagination_row = []
    if page > 0:
        pagination_row.append(InlineKeyboardButton(text="⬅️", callback_data=f"page_{page - 1}"))
    else:
        pagination_row.append(InlineKeyboardButton(text=" ", callback_data="noop"))

    pagination_row.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop"))

    if page < total_pages - 1:
        pagination_row.append(InlineKeyboardButton(text="➡️", callback_data=f"page_{page + 1}"))
    else:
        pagination_row.append(InlineKeyboardButton(text=" ", callback_data="noop"))

    builder.row(*pagination_row)

    # Кнопка "Сохранить"
    builder.row(InlineKeyboardButton(text="🔽 Применить", callback_data="add_category"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_category"))

    return builder.as_markup()


def loc_admin_keyboard(
        roles_users: List[Tuple[UserRole, User]],
        page: int = 0,
        per_page: int = 8,
        admin_user_id: int = None
) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для управления администраторами локации

    Args:
        roles_users: Список пар (UserRole, User)
        page: Текущая страница
        per_page: Количество элементов на странице

    Returns:
        InlineKeyboardMarkup: Клавиатура с пагинацией
        :param admin_user_id:
    """
    builder = InlineKeyboardBuilder()

    # Разбиваем на страницы
    total_pages = max(1, (len(roles_users) + per_page - 1) // per_page)
    page = max(0, min(page, total_pages - 1))
    start_idx = page * per_page
    end_idx = start_idx + per_page
    paginated_items = roles_users[start_idx:end_idx]

    for user_role, user in paginated_items:
        emoji = '⭕️' if admin_user_id == user.id_tg else ''
        builder.add(InlineKeyboardButton(
            text=f"{emoji} {user.user_name or user.id_tg}",
            callback_data=f"admin_{user.id_tg}"
        ))

    builder.adjust(1)

    pagination_buttons = []
    if page > 0:
        pagination_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"page_{page - 1}"))
    else:
        pagination_buttons.append(InlineKeyboardButton(text=" ", callback_data="noop"))

    pagination_buttons.append(InlineKeyboardButton(
        text=f"{page + 1}/{total_pages}",
        callback_data="noop"
    ))

    if page < total_pages - 1:
        pagination_buttons.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"page_{page + 1}"))
    else:
        pagination_buttons.append(InlineKeyboardButton(text=" ", callback_data="noop"))

    builder.row(*pagination_buttons)

    builder.row(InlineKeyboardButton(
        text="❌ Удалить Админа",
        callback_data="del_admin"
    ))

    builder.row(InlineKeyboardButton(
        text="➕ Добавить Админа",
        callback_data="add_admin"
    ))

    builder.row(InlineKeyboardButton(
        text="Назад",
        callback_data="back"
    ))

    return builder.as_markup()


def coupon_menu_keyboard(cb_data: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if cb_data == 'iam_coupon':
        builder.add(InlineKeyboardButton(text="Найти агента", callback_data="iam_coupon_search"))
        builder.add(InlineKeyboardButton(text="Активные коллаборации", callback_data="iam_coupon_active_collab"))
    if cb_data == 'iam_agent':
        builder.add(InlineKeyboardButton(text="Запросы на Коллаборацию", callback_data="iam_agent_requests"))
        builder.add(InlineKeyboardButton(text="Активные коллаборации", callback_data="iam_agent_active"))
    builder.add(InlineKeyboardButton(text="Назад", callback_data="back"))
    builder.adjust(1)

    return builder.as_markup()


def loc_comp_keyboard(
        companies: List[Company],
        selected_companies: Union[List[int], list],
        page: int = 0,
        per_page: int = 10
) -> InlineKeyboardMarkup:
    """Клавиатура для выбора категорий с пагинацией (2 колонки, 10 элементов)"""
    builder = InlineKeyboardBuilder()

    total_pages = (len(companies) + per_page - 1) // per_page
    start_idx = page * per_page
    end_idx = start_idx + per_page
    paginated_categories = companies[start_idx:end_idx]

    row = []
    for i, company in enumerate(paginated_categories):
        text = f"🟢 {company.Name_comp}" if company.id_comp in selected_companies else company.Name_comp
        button = InlineKeyboardButton(
            text=text,
            callback_data=f"company_{company.id_comp}"
        )
        row.append(button)

        if len(row) == 2:
            builder.row(*row)
            row = []

    if row:
        builder.row(*row)

    pagination_row = []
    if page > 0:
        pagination_row.append(InlineKeyboardButton(text="⬅️", callback_data=f"page_{page - 1}"))
    else:
        pagination_row.append(InlineKeyboardButton(text=" ", callback_data="noop"))

    pagination_row.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop"))

    if page < total_pages - 1:
        pagination_row.append(InlineKeyboardButton(text="➡️", callback_data=f"page_{page + 1}"))
    else:
        pagination_row.append(InlineKeyboardButton(text=" ", callback_data="noop"))

    builder.row(*pagination_row)

    builder.row(InlineKeyboardButton(text="🔽 Фильтры 🔽", callback_data="noop"))
    builder.row(*[InlineKeyboardButton(text="🔍 Город", callback_data="filter_city"),
                  InlineKeyboardButton(text="🔍 Категория", callback_data="filter_category")])
    builder.row(InlineKeyboardButton(text="🧹 Сбросить фильтры", callback_data="filter_clear"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="filter_back"))

    return builder.as_markup()


def loc_city_keyboard(
        cities: List[City],
        selected_cities: Union[List[int], list] | int | None,
        page: int = 0,
        per_page: int = 10
) -> InlineKeyboardMarkup:
    """Клавиатура для выбора категорий с пагинацией (2 колонки, 10 элементов)"""
    builder = InlineKeyboardBuilder()

    selected_cities = [] if selected_cities is None else selected_cities

    selected_cities= (
        [selected_cities] if isinstance(selected_cities, int)
        else list(selected_cities)
    )

    total_pages = (len(cities) + per_page - 1) // per_page
    start_idx = page * per_page
    end_idx = start_idx + per_page
    paginated_categories = cities[start_idx:end_idx]

    row = []
    for i, company in enumerate(paginated_categories):
        text = f"🟢 {company.name}" if company.id in selected_cities else company.name
        button = InlineKeyboardButton(
            text=text,
            callback_data=f"city_{company.id}"
        )
        row.append(button)

        if len(row) == 2:
            builder.row(*row)
            row = []

    if row:
        builder.row(*row)

    pagination_row = []
    if page > 0:
        pagination_row.append(InlineKeyboardButton(text="⬅️", callback_data=f"page_{page - 1}"))
    else:
        pagination_row.append(InlineKeyboardButton(text=" ", callback_data="noop"))

    pagination_row.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop"))

    if page < total_pages - 1:
        pagination_row.append(InlineKeyboardButton(text="➡️", callback_data=f"page_{page + 1}"))
    else:
        pagination_row.append(InlineKeyboardButton(text=" ", callback_data="noop"))

    builder.row(*pagination_row)

    builder.row(InlineKeyboardButton(text="🔽 Применить", callback_data="add_city"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_city"))

    return builder.as_markup()


def comp_location_keyboard(
        locations: List[CompLocation],
        page: int = 0,
        per_page: int = 10
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    total_pages = (len(locations) + per_page - 1) // per_page
    start_idx = page * per_page
    end_idx = start_idx + per_page
    paginated_categories = locations[start_idx:end_idx]

    row = []
    for i, location in enumerate(paginated_categories):
        text = location.name_loc
        button = InlineKeyboardButton(
            text=text,
            callback_data=f"location_{location.id_location}"
        )
        row.append(button)

        if len(row) == 2:
            builder.row(*row)
            row = []

    if row:
        builder.row(*row)

    pagination_row = []
    if page > 0:
        pagination_row.append(InlineKeyboardButton(text="⬅️", callback_data=f"page_{page - 1}"))
    else:
        pagination_row.append(InlineKeyboardButton(text=" ", callback_data="noop"))

    pagination_row.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop"))

    if page < total_pages - 1:
        pagination_row.append(InlineKeyboardButton(text="➡️", callback_data=f"page_{page + 1}"))
    else:
        pagination_row.append(InlineKeyboardButton(text=" ", callback_data="noop"))

    builder.row(*pagination_row)

    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="location_back"))

    return builder.as_markup()


def collab_comp_keyboard(
        collabs: List[CouponType],
        page: int = 0,
        per_page: int = 10
) -> InlineKeyboardMarkup:
    """Клавиатура для выбора категорий с пагинацией (2 колонки, 10 элементов)"""
    builder = InlineKeyboardBuilder()

    total_pages = (len(collabs) + per_page - 1) // per_page
    start_idx = page * per_page
    end_idx = start_idx + per_page
    paginated_categories = collabs[start_idx:end_idx]

    row = []
    for i, collab in enumerate(paginated_categories):
        emoji = "🟢" if collab.is_active else "🟥"
        button = InlineKeyboardButton(
            text=f"{emoji} {collab.company.Name_comp}",
            callback_data=f"my_collab_{collab.id_coupon_type}"
        )
        row.append(button)

        if len(row) == 2:
            builder.row(*row)
            row = []

    if row:
        builder.row(*row)

    pagination_row = []
    if page > 0:
        pagination_row.append(InlineKeyboardButton(text="⬅️", callback_data=f"page_{page - 1}"))
    else:
        pagination_row.append(InlineKeyboardButton(text=" ", callback_data="noop"))

    pagination_row.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop"))

    if page < total_pages - 1:
        pagination_row.append(InlineKeyboardButton(text="➡️", callback_data=f"page_{page + 1}"))
    else:
        pagination_row.append(InlineKeyboardButton(text=" ", callback_data="noop"))

    builder.row(*pagination_row)

    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_my_collab"))

    return builder.as_markup()


def collab_request_keyboard(
        collabs: List[CouponType],
        page: int = 0,
        per_page: int = 10
) -> InlineKeyboardMarkup:
    """Клавиатура для выбора категорий с пагинацией (2 колонки, 10 элементов)"""
    builder = InlineKeyboardBuilder()

    total_pages = (len(collabs) + per_page - 1) // per_page
    start_idx = page * per_page
    end_idx = start_idx + per_page
    paginated_categories = collabs[start_idx:end_idx]

    row = []
    for i, collab in enumerate(paginated_categories):
        button = InlineKeyboardButton(
            text=f"{collab.company.Name_comp}",
            callback_data=f"collab_req_{collab.id_coupon_type}"
        )
        row.append(button)

        if len(row) == 2:
            builder.row(*row)
            row = []

    if row:
        builder.row(*row)

    pagination_row = []
    if page > 0:
        pagination_row.append(InlineKeyboardButton(text="⬅️", callback_data=f"page_{page - 1}"))
    else:
        pagination_row.append(InlineKeyboardButton(text=" ", callback_data="noop"))

    pagination_row.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop"))

    if page < total_pages - 1:
        pagination_row.append(InlineKeyboardButton(text="➡️", callback_data=f"page_{page + 1}"))
    else:
        pagination_row.append(InlineKeyboardButton(text=" ", callback_data="noop"))

    builder.row(*pagination_row)

    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_my_collab"))

    return builder.as_markup()
