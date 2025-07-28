from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from io import BytesIO, StringIO
import csv
from datetime import date
from utils.database.models import (
    CompLocation, User, Company, Coupon, CouponType, UserRole
)
from utils.database.models import CouponStatusHelper

class ReportService:
    """Сервис для генерации отчетов и статистики"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_system_stats(self) -> dict:
        """Получает системную статистику"""
        stats = {
            'total_users': 0,
            'total_companies': 0,
            'total_coupons': 0,
            'used_coupons': 0,
            'active_subscriptions': 0
        }
        
        try:
            # Количество пользователей
            stmt = select(func.count(User.id))
            stats['total_users'] = await self.session.scalar(stmt) or 0
            
            # Количество компаний
            stmt = select(func.count(Company.id_comp))
            stats['total_companies'] = await self.session.scalar(stmt) or 0
            
            # Общее количество купонов
            stmt = select(func.count(Coupon.id_coupon))
            stats['total_coupons'] = await self.session.scalar(stmt) or 0
            
            # Использованные купоны
            used_status_id = CouponStatusHelper.get_status_id("used")
            stmt = select(func.count(Coupon.id_coupon)).where(
                Coupon.status_id == used_status_id
            )
            stats['used_coupons'] = await self.session.scalar(stmt) or 0
            

            stats['active_subscriptions'] = await self.session.scalar(stmt) or 0
            
        except Exception as e:
            # Логирование ошибки 
            print(f"Ошибка получения статистики: {e}")
        
        return stats
    
    async def generate_coupons_report(self) -> BytesIO:
        """Генерирует отчет по купонам в формате CSV"""
        # Заголовки CSV
        fieldnames = [
            "ID", "Код", "Тип купона", "Клиент", 
            "Статус", "Дата выдачи", "Дата окончания",
            "Дата использования", "Сумма заказа", "Локация использования"
        ]
        
        # Собираем данные
        data = []
        try:
            stmt = select(
                Coupon.id_coupon,
                Coupon.code,
                CouponType.code_prefix,
                User.first_name,
                User.last_name,
                Coupon.status_id,
                Coupon.start_date,
                Coupon.end_date,
                Coupon.used_at,
                Coupon.order_amount,
                CompLocation.name_loc
            ).select_from(Coupon)\
            .join(CouponType, Coupon.coupon_type_id == CouponType.id_coupon_type)\
            .join(User, Coupon.client_id == User.id)\
            .outerjoin(CompLocation, Coupon.location_used == CompLocation.id_location)
            
            result = await self.session.execute(stmt)
            
            # Маппинг статусов
            status_map = {
                1: "Активен",
                2: "Использован",
                3: "Просрочен",
                4: "Отменен"
            }
            
            for row in result:
                status_id = row.status_id
                data.append([
                    row.id_coupon,
                    row.code,
                    row.code_prefix,
                    f"{row.first_name} {row.last_name}",
                    status_map.get(status_id, "Неизвестен"),
                    row.start_date.strftime("%Y-%m-%d") if row.start_date else "",
                    row.end_date.strftime("%Y-%m-%d") if row.end_date else "",
                    row.used_at.strftime("%Y-%m-%d %H:%M") if row.used_at else "",
                    str(row.order_amount) if row.order_amount else "0.00",
                    row.name_loc or ""
                ])
                
        except Exception as e:
            print(f"Ошибка генерации отчета: {e}")
            # Возвращаем пустой отчет с заголовком при ошибке
            data = [["Ошибка при генерации отчета"]]
        
        # Создаем CSV в памяти
        csv_buffer = StringIO()
        writer = csv.writer(csv_buffer, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        
        # Записываем данные
        writer.writerow(fieldnames)
        writer.writerows(data)
        
        # Конвертируем в бинарный формат
        csv_buffer.seek(0)
        binary_buffer = BytesIO(csv_buffer.getvalue().encode('utf-8'))
        csv_buffer.close()
        
        binary_buffer.seek(0)
        binary_buffer.name = 'coupons_report.csv'
        return binary_buffer

    async def get_agent_commission_report(self, agent_id: int, start_date: date, end_date: date) -> dict:
        """Генерирует отчет по комиссиям агента"""
        report = {
            "total_commission": 0.0,
            "coupons": []
        }
        
        try:
            # Получаем все купоны, где агент является получателем комиссии
            stmt = select(
                Coupon.id_coupon,
                Coupon.code,
                Coupon.order_amount,
                CouponType.commission_percent,
                (Coupon.order_amount * CouponType.commission_percent / 100).label("commission")
            ).join(
                CouponType, Coupon.coupon_type_id == CouponType.id_coupon_type
            ).where(
                (CouponType.company_agent_id == agent_id) &
                (Coupon.used_at >= start_date) &
                (Coupon.used_at <= end_date) &
                (Coupon.status_id == CouponStatusHelper.get_status_id("used"))
            )
            
            result = await self.session.execute(stmt)
            
            for row in result:
                commission = float(row.commission) if row.commission else 0.0
                report["total_commission"] += commission
                report["coupons"].append({
                    "id": row.id_coupon,
                    "code": row.code,
                    "amount": float(row.order_amount) if row.order_amount else 0.0,
                    "percent": float(row.commission_percent),
                    "commission": commission
                })
                
        except Exception as e:
            print(f"Ошибка генерации отчета по комиссиям: {e}")
        
        return report