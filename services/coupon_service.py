import uuid
from datetime import datetime, timedelta
from repositories.coupon_repository import CouponRepository
from utils.database.models import CouponStatus  # Импорт модели

class CouponService:
    def __init__(self, session):
        self.coupon_repo = CouponRepository(session)

    async def generate_coupon(self, issuer_id: int, client_id: int, coupon_type_id: int) -> dict:
        """Генерирует новый купон и сохраняет его в базе данных"""
        coupon_code = f"REF-{uuid.uuid4().hex[:8].upper()}"
        
        # Используем метод get_status_id для получения ID активного статуса
        active_status_id = CouponStatus.get_status_id("active")
        
        # Формируем данные купона
        coupon_data = {
            'code': coupon_code,
            'coupon_type_id': coupon_type_id,
            'client_id': client_id,
            'start_date': datetime.now().date(),
            'end_date': (datetime.now() + timedelta(days=30)).date(),
            'issued_by': issuer_id,
            'status_id': active_status_id  # Используем полученный ID
        }
        
        # Создаем купон в базе данных
        coupon = await self.coupon_repo.create_coupon(coupon_data)
        return coupon

    async def use_coupon(self, coupon_code: str, user_id: int, amount: float):
        """Отмечает купон как использованный"""
        coupon = await self.coupon_repo.get_coupon_by_code(coupon_code)
        if coupon:
            # Получаем ID статуса "used"
            used_status_id = CouponStatus.get_status_id("used")
            
            # Обновляем данные купона
            coupon.used_by = user_id
            coupon.used_at = datetime.now()
            coupon.order_amount = amount
            coupon.status_id = used_status_id  # Устанавливаем статус "использован"
            
            # Сохраняем изменения
            await self.coupon_repo.session.commit()
            return coupon
        return None