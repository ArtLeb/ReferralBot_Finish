from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from services.category_service import CategoryService
from utils.keyboards import loc_categories_keyboard
from utils.states import CreateLocationStates

router = Router()

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

        await cb.message.delete()
