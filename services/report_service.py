from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date
import csv
from io import StringIO
from utils.database.models import User, Company, Coupon

class ReportService:
    """Сервис для генерации отчетов"""
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_system_stats(self) -> dict:
        """
        Возвращает статистику системы
        Returns:
            dict: Словарь с метриками
        """
        # Пользователи
        users_count = await self.session.scalar(select(func.count(User.id)))
        
        # Компании
        companies_count = await self.session.scalar(select(func.count(Company.id_comp)))
        
        # Купоны
        coupons_count = await self.session.scalar(select(func.count(Coupon.id_coupon)))
        used_coupons = await self.session.scalar(
            select(func.count(Coupon.id_coupon))
            .where(Coupon.status_id == 2)  # Статус "использован"
        )
        

        

    
    async def generate_coupons_report(self):
        """
        Генерирует отчет по купонам
        Returns:
            BytesIO: Файл отчета в формате CSV
        """
        # Получаем данные
        stmt = select(Coupon)
        result = await self.session.execute(stmt)
        coupons = result.scalars().all()
        
        # Создаем CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Заголовки
        writer.writerow([
            'ID', 'Код', 'Тип купона', 'Клиент', 
            'Дата выдачи', 'Дата окончания', 'Статус',
            'Сумма заказа', 'Дата использования'
        ])
        
        # Данные
        for coupon in coupons:
            writer.writerow([
                coupon.id_coupon,
                coupon.code,
                coupon.coupon_type.code_prefix,
                coupon.client.first_name,
                coupon.start_date,
                coupon.end_date,
                coupon.status.name,
                coupon.order_amount,
                coupon.used_at
            ])
        
        # Возвращаем файл
        output.seek(0)
        return output.getvalue().encode('utf-8')
    
    async def generate_companies_report(self):
        """
        Генерирует отчет по компаниям
        Returns:
            BytesIO: Файл отчета в формате CSV
        """
        # Получаем данные
        stmt = select(Company)
        result = await self.session.execute(stmt)
        companies = result.scalars().all()
        
        # Создаем CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Заголовки
        writer.writerow([
            'ID', 'Название', 'Категория', 'Владелец',
            'Локации', 'Дата создания'
        ])
        
        # Данные
        for company in companies:
            writer.writerow([
                company.id_comp,
                company.Name_comp,
                company.category.name,
                f"{company.owner.first_name} {company.owner.last_name}",
                len(company.locations),
                company.created_at
            ])
        
        # Возвращаем файл
        output.seek(0)
        return output.getvalue().encode('utf-8')