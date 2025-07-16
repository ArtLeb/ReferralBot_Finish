# keyboards.py
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types import KeyboardButton
from utils.database.models import Company, CompLocation, CompanyCategory

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