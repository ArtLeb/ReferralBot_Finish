from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, delete

from services.action_logger import CityLogger
from utils.database.models import Company, CompLocation, UserRole, LocCat
import logging
from typing import List

logger = logging.getLogger(__name__)


class CompanyService:
    """Сервис для управления компаниями и локациями"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_companies_filtered_by_loc(
            self,
            city: list[int] = None,
            category: list[int] = None,
    ) -> List[Company]:
        stmt = select(Company).join(
            CompLocation, Company.id_comp == CompLocation.id_comp
        ).join(
            LocCat, LocCat.id_location == CompLocation.id_location and
                    LocCat.comp_id == CompLocation.id_comp)

        if city:
            city_names = await CityLogger(self.session).get_cities_name_by_id(city)

            stmt = stmt.where(CompLocation.city.in_(city_names))
        if category:
            stmt = stmt.where(LocCat.id_category.in_(category))

        stmt = stmt.distinct(Company.id_comp)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create_company(self, name: str, owner_id: int) -> Company:
        """
        Создает новую компанию и возвращает её с ID из базы данных

        Args:
            name: Название компании
            owner_id: ID владельца

        Returns:
            Company: Созданная компания с заполненным ID

        Raises:
            ValueError: Если превышен лимит компаний на одного владельца
            Exception: При других ошибках базы данных
        """
        try:
            # Проверка лимита компаний
            stmt = select(func.count()).where(
                (UserRole.user_id == owner_id) &
                (UserRole.role == "partner")
            )

            count = await self.session.scalar(stmt)
            if count >= 5:
                raise ValueError("Превышен лимит компаний (5 на пользователя)")

            # Создание и сохранение компании
            company = Company(Name_comp=name)
            self.session.add(company)

            await self.session.commit()
            await self.session.refresh(company)

            return company

        except Exception as e:
            logger.error(f"Ошибка создания компании: {e}")
            await self.session.rollback()
            raise

    async def get_user_companies(self, owner_id: int) -> List[Company]:
        """
        Получает компании пользователя
        Args:
            owner_id: ID владельца
        Returns:
            List[Company]: Список компаний
        """
        stmt = select(Company).distinct().join(
            UserRole, Company.id_comp == UserRole.company_id
        ).where(
            and_(
                UserRole.role == 'partner',
                UserRole.user_id == owner_id
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_company_by_id(self, company_id: int) -> Company:
        """
        Получает компанию по ID
        Args:
            company_id: ID компании
        Returns:
            Company: Объект компании
        """
        return await self.session.get(Company, company_id)

    async def update_company(self, company_id: int, update_data: dict) -> Company:
        """
        Обновляет данные компании
        Args:
            company_id: ID компании
            update_data: Данные для обновления
        Returns:
            Company: Обновленная компания
        """
        company = await self.get_company_by_id(company_id)
        if company:
            for key, value in update_data.items():
                setattr(company, key, value)
            await self.session.commit()
            return company
        return None

    async def create_location(self, company_id: int, city: str, name_loc: str,
                              address: str, map_url: str) -> CompLocation:
        """
        Создает новую локацию компании
        Args:
            company_id: ID компании
            city: Город локации
            address: Адрес локации
            name_loc: название локации
            map_url: Ссылка на адрес в картах
        Returns:
            CompLocation: Созданная локация
        """
        try:
            location = CompLocation(
                id_comp=company_id,
                address=address,
                map_url=map_url,
                name_loc=name_loc,
                city=city
            )
            self.session.add(location)
            await self.session.commit()
            await self.session.refresh(location)
            return location
        except Exception as e:
            logger.error(f"Ошибка создания локации: {e}")
            await self.session.rollback()
            raise

    async def set_loc_category(self, comp_id: int, id_category: int, id_location) -> LocCat:
        """
        Создает новую локацию компании
        Args:
            comp_id: ID компании
            id_category: ID категории
            id_location: ID локации
        Returns:
            LocCat: Связка локация - категории
        """
        try:
            loc_cat = LocCat(
                comp_id=comp_id,
                id_location=id_location,
                id_category=id_category
            )
            self.session.add(loc_cat)
            await self.session.commit()
            await self.session.refresh(loc_cat)
            return loc_cat
        except Exception as e:
            logger.error(f"Ошибка создания локации: {e}")
            await self.session.rollback()
            raise

    async def remove_loc_category(self, comp_id: int, id_category: int, id_location) -> bool:
        """
        Удаляет категорю локации
        Args:
            comp_id: ID компании
            id_category: ID категории
            id_location: ID локации
        Returns:
            bool: Связка локация - категории
        """
        try:
            loc_cat = delete(LocCat).where(
                and_(LocCat.id_location == id_location,
                     LocCat.id_category == id_category,
                     LocCat.comp_id == comp_id)
            )
            await self.session.execute(loc_cat)
            await self.session.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка создания локации: {e}")
            await self.session.rollback()
            raise

    async def get_loc_categories_id(self, comp_id: int, id_location: int) -> List[int]:
        """
        Формирует массив из ИД категорий определенной локации

        Args:
            comp_id: ID компании
            id_location: ID локации

        Returns:
            List[int]: Список ID категорий, связанных с локацией
        """
        try:
            query = select(LocCat.id_category).where(
                (LocCat.comp_id == comp_id) &
                (LocCat.id_location == id_location))

            result = await self.session.execute(query)
            return [row for row in result.scalars()]

        except Exception as e:
            logger.error(f"Ошибка при получении категорий локации: {e}")
            await self.session.rollback()
            raise

    async def get_locations_by_company(self, company_id: int) -> List[CompLocation]:
        """
        Получает локации компании
        Args:
            company_id: ID компании
        Returns:
            List[CompLocation]: Список локаций
        """
        stmt = select(CompLocation).where(CompLocation.id_comp == company_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_location_by_id(self, location_id: int) -> CompLocation:
        """
        Получает локацию по ID
        Args:
            location_id: ID локации
        Returns:
            CompLocation: Объект локации
        """
        return await self.session.get(CompLocation, location_id)

    async def update_location(self, location_id: int, update_data: dict) -> CompLocation:
        """
        Обновляет данные локации
        Args:
            location_id: ID локации
            update_data: Данные для обновления
        Returns:
            CompLocation: Обновленная локация
        """
        location = await self.get_location_by_id(location_id)
        if location:
            for key, value in update_data.items():
                setattr(location, key, value)
            await self.session.commit()
            return location
        return None

    async def delete_location(self, location_id: int) -> None:
        """
        Удаляет данные локации
        Args:
            location_id: ID локации
        """
        location = await self.get_location_by_id(location_id)
        if location:
            try:
                stmt = delete(CompLocation).where(CompLocation.id_location == location_id)
                await self.session.execute(stmt)
                await self.session.commit()
                return location
            except Exception as e:
                await self.session.rollback()
        return None
