import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from services.company_service import CompanyService
from utils.states import PartnerStates

router = Router()
logger = logging.getLogger(__name__)


@router.message(PartnerStates.company_menu, F.text == "Редактировать Компанию")
async def edit_comp_btn(message: Message, session: AsyncSession, state: FSMContext):
    data = await state.get_data()
    service = CompanyService(session)
    company_data = await service.get_company_by_id(data['company_id'])

    company_info = (
        f"🏢 Компания: {company_data.Name_comp}\n"
        f"\nВыберите поле которое нужно редактировать:"
    )

    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="Название Компании"))

    await message.answer(company_info, reply_markup=builder.as_markup(resize_keyboard=True))
    await state.set_state(PartnerStates.edit_company_name)


@router.message(PartnerStates.edit_company_name, F.text == "Название Компании")
async def edit_comp_btn(message: Message, state: FSMContext):
    await message.answer('Введите <b>название компании</b>')
    await state.set_state(PartnerStates.process_comp_name)


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
