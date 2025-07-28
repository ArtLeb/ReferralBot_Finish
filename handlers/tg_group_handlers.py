from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from sqlalchemy import select
from utils.database.models import TgGroup
from services.tg_group_service import TgGroupService
from services.company_service import CompanyService
from sqlalchemy.ext.asyncio import AsyncSession
from utils.states import PartnerStates
from sqlalchemy.orm import selectinload
import logging
from aiogram.exceptions import TelegramBadRequest  # Универсальное исключение для обработки ошибок Telegram

router = Router()
logger = logging.getLogger(__name__)

PAGE_SIZE = 5  # Количество групп на странице

class TgGroupStates(StatesGroup):
    waiting_for_group_id = State()
    waiting_for_group_name = State()

@router.message(PartnerStates.company_menu, F.text == "ТГ Группы")
async def manage_tg_groups(message: Message, session: AsyncSession, state: FSMContext):
    """Меню управления Telegram-группами для компании"""
    # Получаем company_id из состояния
    data = await state.get_data()
    company_id = data.get('company_id')
    
    if not company_id:
        await message.answer("❌ Компания не выбрана")
        return

    group_service = TgGroupService(session)
    groups = await group_service.get_groups_by_company(company_id)
    
    if not groups:
        # Если нет групп, предлагаем добавить
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить", callback_data="add_group")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
        ])
        await message.answer(
            "В этой компании пока нет групп. Хотите добавить?",
            reply_markup=keyboard
        )
        # Сохраняем company_id в состояние
        await state.update_data(company_id=company_id, groups=[], page=0)
        return
    
    # Сохраняем группы и company_id в состояние
    groups_data = [{
        'id_tg_group': g.id_tg_group,
        'group_id': g.group_id,
        'name': g.name,
        'is_active': g.is_active
    } for g in groups]
    
    await state.update_data(company_id=company_id, groups=groups_data, page=0)
    await show_groups_page(message, state)

async def show_groups_page(message: Message, state: FSMContext):
    """Показывает страницу с группами компании"""
    data = await state.get_data()
    page = data.get('page', 0)
    groups = data.get('groups', [])
    
    start_idx = page * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    page_groups = groups[start_idx:end_idx]
    
    # Создаем клавиатуру
    builder = InlineKeyboardBuilder()
    for group in page_groups:
        builder.button(
            text=group['name'], 
            callback_data=f"group_{group['id_tg_group']}"
        )
    
    # Кнопки пагинации
    pagination_buttons = []
    if page > 0:
        pagination_buttons.append(InlineKeyboardButton(
            text="⬅️ Назад", 
            callback_data="prev_page"
        ))
    
    if end_idx < len(groups):
        pagination_buttons.append(InlineKeyboardButton(
            text="Вперед ➡️", 
            callback_data="next_page"
        ))
    
    if pagination_buttons:
        builder.row(*pagination_buttons)
    
    # Кнопки управления
    builder.row(
        InlineKeyboardButton(text="➕ Добавить", callback_data="add_group"),
        InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")
    )
    
    await message.answer(
        "📢 Управление Telegram-группами:",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data == "prev_page")
async def prev_page(callback: CallbackQuery, state: FSMContext):
    """Обработка перехода на предыдущую страницу"""
    data = await state.get_data()
    current_page = data.get('page', 0)
    if current_page > 0:
        await state.update_data(page=current_page - 1)
        await callback.message.delete()
        await show_groups_page(callback.message, state)
    await callback.answer()

@router.callback_query(F.data == "next_page")
async def next_page(callback: CallbackQuery, state: FSMContext):
    """Обработка перехода на следующую страницу"""
    data = await state.get_data()
    current_page = data.get('page', 0)
    groups = data.get('groups', [])
    
    if (current_page + 1) * PAGE_SIZE < len(groups):
        await state.update_data(page=current_page + 1)
        await callback.message.delete()
        await show_groups_page(callback.message, state)
    await callback.answer()

@router.callback_query(F.data == "add_group")
async def add_group_start(callback: CallbackQuery, state: FSMContext):
    """Начало добавления новой группы"""
    await callback.message.answer("Введите ID группы в Telegram:")
    await state.set_state(TgGroupStates.waiting_for_group_id)
    await callback.answer()

@router.message(TgGroupStates.waiting_for_group_id)
async def process_group_id(message: Message, state: FSMContext):
    """Обработка ввода ID группы"""
    try:
        group_id = int(message.text)
        bot_id = (await message.bot.get_me()).id
        
        try:
            # Пытаемся получить информацию о члене чата
            member = await message.bot.get_chat_member(chat_id=group_id, user_id=bot_id)
            
            # Проверяем, что бот является участником и не покинул группу
            if member.status in ['left', 'kicked']:
                await message.answer("❌ Бот не является участником группы. Добавьте бота в группу и повторите попытку.")
            else:
                await state.update_data(group_id=group_id, is_active=True)
                await message.answer("Введите название группы:")
                await state.set_state(TgGroupStates.waiting_for_group_name)
                
        except TelegramBadRequest as e:
            # Обрабатываем разные коды ошибок
            if "chat not found" in str(e).lower() or "CHAT_NOT_FOUND" in str(e):
                await message.answer("❌ Группа не найдена. Проверьте ID и добавьте бота в группу.")
            elif "bot is not a member" in str(e).lower() or "USER_NOT_PARTICIPANT" in str(e):
                await message.answer("❌ Бот не является участником группы. Добавьте бота в группу.")
            elif "forbidden" in str(e).lower() or "FORBIDDEN" in str(e):
                await message.answer("❌ Нет доступа к группе. Добавьте бота в группу как администратора.")
            else:
                logger.error(f"Ошибка Telegram при проверке группы: {e}")
                await message.answer(f"❌ Произошла ошибка при проверке группы: {e}")
        except Exception as e:
            logger.error(f"Неизвестная ошибка при проверке группы: {e}")
            await message.answer(f"❌ Произошла неизвестная ошибка при проверке группы: {e}")
            
    except ValueError:
        await message.answer("❌ ID группы должен быть числом. Попробуйте еще раз.")

@router.message(TgGroupStates.waiting_for_group_name)
async def process_group_name(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка ввода названия группы и сохранение в БД"""
    group_name = message.text.strip()
    if not group_name:
        await message.answer("❌ Название группы не может быть пустым")
        return
    
    data = await state.get_data()
    group_id = data['group_id']
    company_id = data['company_id']
    is_active = data.get('is_active', False)  # Статус из проверки
    
    # Проверка существования группы
    group_service = TgGroupService(session)
    existing = await group_service.get_group_by_id(group_id)
    if existing:
        await message.answer("❌ Группа с таким ID уже существует")
        # Сохраняем состояние компании
        await state.set_state(PartnerStates.company_menu)
        return
    
    # Создаем новую группу
    try:
        await group_service.create_group(
            group_id=group_id,
            name=group_name,
            company_id=company_id,
            is_active=is_active  # Передаем статус
        )
        await message.answer(f"✅ Группа '{group_name}' успешно добавлена!")
    except Exception as e:
        logger.error(f"Ошибка создания группы: {e}")
        await message.answer("❌ Произошла ошибка при создании группы")
        # Сохраняем состояние компании
        await state.set_state(PartnerStates.company_menu)
        return
    
    # Сохраняем company_id перед обновлением списка групп
    await state.update_data(company_id=company_id)
    
    # Обновляем список групп без очистки состояния
    await manage_tg_groups(message, session, state)
    
    # Устанавливаем состояние меню компании
    await state.set_state(PartnerStates.company_menu)

@router.callback_query(F.data.startswith("group_"))
async def view_group(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Просмотр деталей группы"""
    group_id = int(callback.data.split("_")[1])
    
    # Явно загружаем связанную компанию
    stmt = select(TgGroup).options(selectinload(TgGroup.company)).where(TgGroup.id_tg_group == group_id)
    result = await session.execute(stmt)
    group = result.scalars().first()
    
    if not group:
        await callback.answer("Группа не найдена")
        return
    
    # Проверяем актуальный статус бота в группе
    actual_status = "Неактивна"
    try:
        bot_id = (await callback.bot.get_me()).id
        try:
            # Проверяем статус бота в группе
            member = await callback.bot.get_chat_member(chat_id=group.group_id, user_id=bot_id)
            if member.status not in ['left', 'kicked']:
                actual_status = "Активна"
        except TelegramBadRequest as e:
            # Обрабатываем ошибки Telegram
            if "chat not found" in str(e).lower() or "CHAT_NOT_FOUND" in str(e):
                actual_status = "Группа не найдена"
            elif "bot is not a member" in str(e).lower() or "USER_NOT_PARTICIPANT" in str(e):
                actual_status = "Бот не в группе"
            elif "forbidden" in str(e).lower() or "FORBIDDEN" in str(e):
                actual_status = "Нет доступа"
            else:
                actual_status = f"Ошибка: {str(e)[:50]}"
        except Exception as e:
            actual_status = f"Ошибка: {str(e)[:50]}"
    except Exception as e:
        logger.error(f"Ошибка при получении информации о боте: {e}")
        actual_status = "Ошибка проверки"
    
    # Формируем ответ
    response = (
        f"📢 Группа: {group.name}\n"
        f"🆔 ID: {group.group_id}\n"
        f"🏢 Компания: {group.company.Name_comp}\n"
        f"🔹 Статус: {actual_status}"
    )
    
    # Добавляем предупреждение если бот не в группе
    if actual_status != "Активна":
        response += "\n\n⚠️ Бот не является участником группы. Добавьте бота в группу для активации."
    
    # Кнопки управления
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_groups"),
            InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_group_{group.id_tg_group}")
        ]
    ])
    
    await callback.message.edit_text(response, reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data == "back_to_groups")
async def back_to_groups(callback: CallbackQuery, state: FSMContext):
    """Возврат к списку групп"""
    await callback.message.delete()
    await show_groups_page(callback.message, state)
    await callback.answer()

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Возврат в главное меню компании"""
    data = await state.get_data()
    company_id = data.get('company_id')
    if not company_id:
        await callback.answer("Ошибка: компания не определена")
        return

    comp_service = CompanyService(session)
    company = await comp_service.get_company_by_id(company_id)
    if not company:
        await callback.answer("Компания не найдена")
        return

    # Формируем сообщение с меню компании
    company_info = (
        f"🏢 Компания: {company.Name_comp}\n"
        f"📍 Локаций: {len(company.locations)}"
    )

    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="Локации"))
    builder.row(KeyboardButton(text="Добавить Локацию"))
    builder.row(KeyboardButton(text="Редактировать Компанию"))
    builder.row(KeyboardButton(text="ТГ Группы"))
    builder.row(KeyboardButton(text="⬅️ Назад"))

    # Удаляем текущее сообщение
    await callback.message.delete()
    await callback.message.answer(
        company_info,
        reply_markup=builder.as_markup(resize_keyboard=True)
    )
    # Устанавливаем состояние меню компании
    await state.set_state(PartnerStates.company_menu)
    await callback.answer()

@router.callback_query(F.data.startswith("delete_group_"))
async def delete_group(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Удаление группы"""
    group_id = int(callback.data.split("_")[2])
    group_service = TgGroupService(session)
    
    try:
        # Получаем company_id для проверки принадлежности
        data = await state.get_data()
        company_id = data.get('company_id')
        
        # Удаляем группу с проверкой принадлежности компании
        success = await group_service.delete_group(group_id, company_id)
        
        if success:
            await callback.message.answer("✅ Группа успешно удалена!")
        else:
            await callback.message.answer("❌ Группа не найдена или не принадлежит компании")
    except Exception as e:
        logger.error(f"Ошибка удаления группы: {e}")
        await callback.message.answer("❌ Произошла ошибка при удалении группы")
    
    await callback.message.delete()
    
    # Сохраняем company_id перед обновлением списка
    await state.update_data(company_id=company_id)
    
    # Обновляем список групп
    await manage_tg_groups(callback.message, session, state)
    
    # Устанавливаем состояние
    await state.set_state(PartnerStates.company_menu)
    await callback.answer()