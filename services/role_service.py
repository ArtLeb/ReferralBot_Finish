from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date, datetime, timedelta
from utils.database.models import UserRole, Company, CompLocation, Coupon, CouponStatus, User
from utils.config import config
from typing import List
import logging

logger = logging.getLogger(__name__)

class RoleService:
    # Карта прав для разных ролей (основной источник разрешений)
    PERMISSION_MAP = {
        'owner': {  # Владелец системы (супер-администратор)
            'add_partners': True,
            'add_admins': True,
            'add_groups': True,
            'gen_coupons': True,
            'set_discount': True,
            'set_commission': True,
            'check_subscription': True,
            'get_coupons': True,
            'view_stats': True,
            'add_clients': True
        },
        'partner': {  # Партнер (владелец бизнеса)
            'add_admins': True,
            'gen_coupons': True,
            'view_stats': True,
            'add_clients': True,
            'get_coupons': True,
            'check_subscription': True
        },
        'admin': {  # Администратор (сотрудник компании)
            'gen_coupons': True,
            'get_coupons': True,
            'check_subscription': True,
            'view_stats': True
        },
        'client': {  # Обычный клиент
            'get_coupons': True
        }
    }

    def __init__(self, session: AsyncSession):
        self.session = session

    async def assign_role_to_user(self, user_id: int, role_name: str, 
                                 company_id: int, location_id: int = None) -> UserRole:
        """
        Назначает роль пользователю в определенной компании и локации
        
        Args:
            user_id: ID пользователя в системе
            role_name: Название роли (admin, partner, client, tech_admin)
            company_id: ID компании, к которой относится роль
            location_id: ID локации (если роль привязана к конкретной локации)
            
        Returns:
            UserRole: Созданный объект роли пользователя
            
        Raises:
            ValueError: Если компания или локация не найдены
            RuntimeError: При ошибках базы данных
        """
        try:
            # Проверка существования компании
            company = await self.session.get(Company, company_id)
            if not company:
                raise ValueError(f"Компания ID {company_id} не найдена")
            
            # Проверка существования локации (если указана)
            if location_id:
                location = await self.session.get(CompLocation, location_id)
                if not location or location.id_comp != company_id:
                    raise ValueError(f"Локация ID {location_id} не найдена или не принадлежит компании")

            # Создание новой роли (роль хранится как строка, а не ID)
            new_user_role = UserRole(
                user_id=user_id,
                role=role_name,  # Здесь храним название роли напрямую
                company_id=company_id,
                location_id=location_id,
                start_date=date.today(),
                end_date=date.today() + timedelta(days=365),  # Срок действия роли - 1 год
                changed_by=user_id,  # Пользователь назначает себе роль
                changed_date=datetime.now(),
                is_locked=False
            )
            
            self.session.add(new_user_role)
            await self.session.commit()
            
            logger.info(f"Назначена роль {role_name} пользователю {user_id} в компании {company_id}")
            return new_user_role
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Ошибка назначения роли: {str(e)}")
            raise RuntimeError(f"Ошибка назначения роли: {str(e)}")

    async def get_user_roles(self, user_id: int) -> List[UserRole]:
        """
        Возвращает все роли пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            List[UserRole]: Список объектов ролей пользователя
        """
        try:
            stmt = select(UserRole).where(UserRole.user_id == user_id)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Ошибка получения ролей: {str(e)}")
            return []

    async def has_permission(self, user: User, permission: str) -> bool:
        """
        Проверяет, есть ли у пользователя определенное разрешение
        
        Args:
            user: Объект пользователя
            permission: Название разрешения (например, 'gen_coupons')
            
        Returns:
            bool: True если разрешение есть, иначе False
        """
        try:
            # Для владельца бота (указанного в конфиге) всегда все разрешено
            if user.id_tg == config.OWNER_ID:
                return True
            
            # Получаем все роли пользователя
            user_roles = await self.get_user_roles(user.id)
            
            # Проверяем права для каждой роли
            for role in user_roles:
                role_name = role.role.lower()  # Получаем название роли
                perms = self.PERMISSION_MAP.get(role_name, {})
                if perms.get(permission, False):
                    return True
                    
            return False
            
        except Exception as e:
            logger.error(f"Ошибка проверки прав: {str(e)}")
            return False

    async def get_system_stats(self) -> dict:
        """
        Возвращает системную статистику
        
        Returns:
            dict: Словарь с ключевыми метриками системы
        """
        try:
            # Получаем количество уникальных пользователей с ролями
            users_count = await self.session.scalar(
                select(func.count(UserRole.user_id.distinct())))
            
            # Получаем количество компаний
            companies_count = await self.session.scalar(
                select(func.count(Company.id_comp)))
            
            # Получаем общее количество купонов
            coupons_count = await self.session.scalar(
                select(func.count(Coupon.id_coupon)))
            
            # Получаем количество использованных купонов
            used_coupons = await self.session.scalar(
                select(func.count(Coupon.id_coupon))
                .where(Coupon.status_id == CouponStatus.USED.value)
            )
            
            # Формируем итоговый словарь с метриками
            return {
                'total_users': users_count or 0,
                'total_companies': companies_count or 0,
                'total_coupons': coupons_count or 0,
                'used_coupons': used_coupons or 0
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {str(e)}")
            return {}