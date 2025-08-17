import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, KeyboardButton, CallbackQuery
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from handlers.partner_handlers import list_companies
from services.category_service import CategoryService
from services.company_service import CompanyService
from utils.keyboards import loc_categories_keyboard
from utils.states import PartnerStates

router = Router()
logger = logging.getLogger(__name__)

field_btn_mapping = {
    'Название': 'name_loc',
    'Адресс': 'address',
    'Город': 'city',
    'Ссылка на карты': 'map_url',
    'Категории': 'category',
    'Удалить': 'delete'
}


@router.message(PartnerStates.company_menu, F.text == "Редактировать Компанию")
async def edit_comp_btn(message: Message, session: AsyncSession, state: FSMContext):
    data = await state.get_data()
    service = CompanyService(session)
    company_data = await service.get_company_by_id(data['company_id'])
    comp_service = CompanyService(session)
    loc_info = await comp_service.get_locations_by_company(company_id=data['company_id'], main_loc=True)

    company_info = (
        f"🏢 Компания: {company_data.Name_comp}\n"
        f"\nВыберите поле которое нужно редактировать:"
    )

    builder = ReplyKeyboardBuilder()

    builder.row(
        KeyboardButton(text="Название"),
        KeyboardButton(text="Адрес"),
        width=2
    )
    builder.row(
        KeyboardButton(text="Город"),
        KeyboardButton(text="Ссылка на карты"),
        width=2
    )

    builder.row(KeyboardButton(text="Категории"))

    builder.row(
        KeyboardButton(text="Удалить"),
        KeyboardButton(text="Завершить редактирование"),
        width=2
    )

    await message.answer(company_info, reply_markup=builder.as_markup(resize_keyboard=True))
    await state.set_state(PartnerStates.edit_company_attr)
    await state.update_data(location_id=loc_info.id_location)


@router.message(PartnerStates.edit_company_attr)
async def edit_comp_btn(message: Message, state: FSMContext, session: AsyncSession):
    action = field_btn_mapping.get(message.text, None)
    comp_service = CompanyService(session)
    data = await state.get_data()
    current_action = data.get('current_action')
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="Мои компании"))

    if message.text == 'Завершить редактирование':
        await message.answer('Вы вышли из режима редактирования', reply_markup=builder.as_markup(resize_keyboard=True))
        await state.set_state(PartnerStates.company_menu)
        await state.set_state()
        return

    if not action and current_action:
        data = await state.get_data()
        if current_action in ['name_loc', 'address', 'city', 'map_url']:
            if current_action == 'name_loc':
                await comp_service.update_company(
                    company_id=data['company_id'],
                    update_data={'Name_comp': message.text}
                )

            await comp_service.update_location(
                location_id=int(data['location_id']),
                update_data={current_action: message.text},
            )
            await message.answer(f"Поле {current_action} успешно обновлено")
            await list_companies(message, session, state)
            return

        await message.answer("Пожалуйста, выберите действие из меню.")
        return

    if action in ['name_loc', 'address', 'city', 'map_url']:
        await state.update_data(current_action=action)
        await message.answer(f"Введите новое значение для: {message.text}")

    elif action == 'delete':
        await comp_service.delete_company(company_id=int(data['company_id']))
        await message.answer("✅ Компания успешно удалена.")
        await list_companies(message, session, state)


    elif action == 'category':
        category_service = CategoryService(session)
        categories = await category_service.get_all_categories()
        selected_category = await comp_service.get_loc_categories_id(
            comp_id=int(data['company_id']),
            id_location=int(data['location_id']),
        )
        keyboard = loc_categories_keyboard(
            categories=categories,
            selected_category=selected_category
        )
        await message.answer("✍️ Выберите категории для локации:", reply_markup=keyboard)
        await state.update_data(
            selected_category=selected_category,
            initial_categories=selected_category.copy(),
            current_page=0
        )
        await state.set_state(PartnerStates.edit_category_comp)


@router.callback_query(PartnerStates.edit_category_comp)
async def process_edit_categories(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    selected_category: list = data.get('selected_category', [])
    initial_categories: list = data.get('initial_categories', [])
    current_page: int = data.get('current_page', 0)

    comp_service = CompanyService(session)
    category_service = CategoryService(session)

    if cb.data.startswith('category_'):
        category_id = int(cb.data.split('_')[1])
        if category_id in selected_category:
            selected_category.remove(category_id)
        else:
            selected_category.append(category_id)

        await state.update_data(selected_category=selected_category)
        categories = await category_service.get_all_categories()
        keyboard = loc_categories_keyboard(categories, selected_category, current_page)
        await cb.message.edit_reply_markup(reply_markup=keyboard)

    elif cb.data.startswith('page_'):
        new_page = int(cb.data.split('_')[1])
        await state.update_data(current_page=new_page)
        categories = await category_service.get_all_categories()
        keyboard = loc_categories_keyboard(categories, selected_category, new_page)
        await cb.message.edit_reply_markup(reply_markup=keyboard)

    elif cb.data == 'add_category':
        if not selected_category:
            await cb.answer(text="Выберите хотя бы одну категорию!", show_alert=True)
            return

        added = [cat for cat in selected_category if cat not in initial_categories]
        removed = [cat for cat in initial_categories if cat not in selected_category]

        for cat_id in added:
            await comp_service.set_loc_category(
                comp_id=data['company_id'],
                id_location=data['location_id'],
                id_category=cat_id
            )

        for cat_id in removed:
            await comp_service.remove_loc_category(
                comp_id=data['company_id'],
                id_location=data['location_id'],
                id_category=cat_id
            )

        await cb.message.answer("✅ Категории успешно обновлены.")
        await list_companies(cb.message, session, state)
        await cb.message.delete()


    elif cb.data == 'noop':
        await cb.answer()


@router.message(PartnerStates.process_comp_name)
async def process_comp_name(message: Message, session: AsyncSession, state: FSMContext):
    data = await state.get_data()
    service = CompanyService(session)
    company = await service.update_company(
        company_id=data["company_id"],
        update_data=dict(Name_comp=message.text)
    )

    company_info = (
        f"✅ Данные успешно обновлены:\n\n"
        f"🆔 ID Компании: {company.id_comp}\n"
        f"🏢 Компания: {company.Name_comp}\n"
    )

    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="Мои компании"))

    await state.set_state()
    await message.answer(company_info, reply_markup=builder.as_markup(resize_keyboard=True))
