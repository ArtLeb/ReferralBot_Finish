import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from services.category_service import CategoryService
from services.company_service import CompanyService
from utils.keyboards import loc_categories_keyboard
from utils.states import CreateLocationStates

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text == '➕ Добавить Локацию')
async def start_create_new_location(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    await message.answer(
        text=f"➕ Создание Локации\n\n"
             f"🏢 Компания: {data['company_name']}\n\n\n"
             f"✍️ Введите название локации:"
    )
    await state.set_state(CreateLocationStates.get_comp_name)


@router.message(CreateLocationStates.get_comp_name, F.text == '➕ Добавить Локацию')
async def start_create_new_location(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    await message.answer(
        text=f"➕ Создание Локации\n\n"
             f"🏢 Компания: {data['company_name']}\n\n\n"
             f"✍️ Введите название локации:"
    )


@router.message(CreateLocationStates.get_comp_name)
async def start_create_new_location(message: Message, state: FSMContext, session: AsyncSession):
    await state.update_data(new_loc_name=message.text)
    await message.answer(
        text=f"✍️ Введите Название Города:"
    )
    await state.set_state(CreateLocationStates.get_loc_city)


@router.message(CreateLocationStates.get_loc_city)
async def start_create_new_location(message: Message, state: FSMContext, session: AsyncSession):
    await state.update_data(new_loc_city=message.text)
    await message.answer(
        text=f"✍️ Введите Адрес локации:"
    )
    await state.set_state(CreateLocationStates.get_loc_address)


@router.message(CreateLocationStates.get_loc_address)
async def start_create_new_location(message: Message, state: FSMContext, session: AsyncSession):
    await state.update_data(new_loc_address=message.text)
    await message.answer(
        text=f"✍️ Введите Ссылку на картах:"
    )
    await state.set_state(CreateLocationStates.get_loc_address_url)


@router.message(CreateLocationStates.get_loc_address_url)
async def start_create_new_location(message: Message, state: FSMContext, session: AsyncSession):
    await state.update_data(new_loc_address_url=message.text)
    category_service = CategoryService(session)
    categories = await category_service.get_all_categories()
    keyboard = loc_categories_keyboard(categories, selected_category=[])
    await message.answer(
        text=f"✍️ Введите Категории",
        reply_markup=keyboard
    )
    await state.update_data(selected_category=[], current_page=0)
    await state.set_state(CreateLocationStates.get_loc_category)


@router.callback_query(CreateLocationStates.get_loc_category)
async def process_company_name(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Обработка выбора категорий и пагинации"""
    data = await state.get_data()
    selected_category: list = data.get('selected_category', [])
    current_page: int = data.get('current_page', 0)

    if cb.data.startswith('category_'):
        category_id = int(cb.data.split('_')[1])
        if category_id in selected_category:
            selected_category.remove(category_id)
        else:
            selected_category.append(category_id)

        await state.update_data(selected_category=selected_category)

        category_service = CategoryService(session)
        categories = await category_service.get_all_categories()
        keyboard = loc_categories_keyboard(categories, selected_category, current_page)

        await cb.message.edit_reply_markup(reply_markup=keyboard)

    elif cb.data.startswith('page_'):
        new_page = int(cb.data.split('_')[1])
        await state.update_data(current_page=new_page)

        category_service = CategoryService(session)
        categories = await category_service.get_all_categories()
        keyboard = loc_categories_keyboard(categories, selected_category, new_page)

        await cb.message.edit_reply_markup(reply_markup=keyboard)

    elif cb.data == 'add_category':
        if not selected_category:
            await cb.answer(text="Выберите хотя бы одну категорию!", show_alert=True)
            return

        await cb.message.answer(text="💾 Категории компании успешно сохранены")
        await cb.message.delete()
        creation_msg = await cb.message.answer(text="🕓 Локация создается, осталось немного...")
        comp_service = CompanyService(session=session)

        #   Создаем новую локацию
        location = await comp_service.create_location(
            company_id=data['company_id'],
            city=data['new_loc_city'],
            name_loc=data['new_loc_name'],
            map_url=data['new_loc_address_url'],
            address=data['new_loc_address']
        )

        #   Присваиваем категории новой локации
        for category_id in selected_category:
            await comp_service.set_loc_category(
                comp_id=location.id_comp,
                id_location=location.id_location,
                id_category=category_id
            )

        location_info = (
            "━━━━━━━━━━━━━━━━━━━━\n"
            "✨ <b>Локация успешно создана</b> ✨\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"

            "🏛 <b>Компания:</b>"
            f"   {data['company_name']}\n\n"

            "📍 <b>Локация:</b>"
            f"   {data['new_loc_name']}\n\n"

            "🌆 <b>Город:</b>"
            f"   {data['new_loc_city']}\n\n"

            "🏠 <b>Адрес:</b>"
            f"   {data['new_loc_address']}\n\n"

            "━━━━━━━━━━━━━━━━━━━━"
        )

        await creation_msg.edit_text(
            text=location_info,
            parse_mode='HTML'
        )


    elif cb.data == 'noop':
        await cb.answer()
