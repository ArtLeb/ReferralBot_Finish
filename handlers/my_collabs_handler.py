from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from handlers.collaboration_handler import start_collab_menu
from services.coupon_service import CouponService
from utils.collab_helper import show_collaborations
from utils.states import CollaborationStates

router = Router()


# Обработчики пагинации
@router.callback_query(
    CollaborationStates.view_collaborations,
    F.data.startswith("page_")
)
async def prev_page(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    current_page = max(0, data["current_page"] - 1)
    await state.update_data(current_page=current_page)
    await show_collaborations(cb=cb, session=session, state=state, current_page=current_page, collab_type='my_collabs')


# Обработчик прекращения коллаборации
@router.callback_query(
    CollaborationStates.view_collaborations,
    F.data.startswith("terminate_")
)
async def terminate_collab(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    coupon_type_id = int(cb.data.split("_")[1])
    coupon_service = CouponService(session)
    collaborations = await coupon_service.get_collaborations(
        comp_id=data['company_id'], loc_id=data['location_id'],  role='my_collabs')
    terminated = await coupon_service.terminate_collaboration(coupon_type_id)

    if terminated:
        # Обновляем список
        collaborations = [
            c for c in collaborations
            if c.id_coupon_type != coupon_type_id
        ]
        await state.update_data(collaborations=collaborations)
        await cb.answer("✅ Коллаборация прекращена")
        # await display_collaborations_page(cb, state, collaborations)


# Возврат в меню
@router.callback_query(
    CollaborationStates.view_collaborations,
    F.data == "back_to_collab_menu"
)
async def back_to_menu(cb: CallbackQuery, state: FSMContext):
    await state.set_state(CollaborationStates.collab_menu)
    await cb.message.delete()
    await start_collab_menu(cb.message, state)


# Остальной существующий код...
@router.callback_query(
    CollaborationStates.view_requests,
    F.data == "back_to_collab_menu"
)
async def back_to_menu_from_requests(cb: CallbackQuery, state: FSMContext):
    await state.set_state(CollaborationStates.collab_menu)
    await cb.message.delete()
    await start_collab_menu(cb.message, state)
