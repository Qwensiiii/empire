from database.crud import DatabaseCRUD
import random

class EconomyManager:
    def __init__(self, db: DatabaseCRUD):
        self.db = db
    
    def process_click(self, user_id: int, count: int = 1) -> dict:
        """Обработка клика"""
        user = self.db.get_user(user_id)
        if not user:
            return {'success': False, 'message': 'Пользователь не найден'}
        
        # Базовый доход от клика
        earned = user.click_power * count
        
        # Шанс на бонус (10%)
        bonus_multiplier = 1
        if random.random() < 0.1:
            bonus_multiplier = random.choice([2, 3, 5])
            earned *= bonus_multiplier
        
        # Обновляем баланс
        self.db.update_balance(user_id, earned)
        self.db.add_click(user_id, count)
        
        return {
            'success': True,
            'earned': earned,
            'balance': user.balance + earned,
            'bonus': bonus_multiplier > 1,
            'bonus_multiplier': bonus_multiplier,
            'click_power': user.click_power
        }
    
    def get_business_list(self) -> list:
        """Список доступных бизнесов"""
        return [
            {'id': 1, 'name': 'Кофейня', 'emoji': '☕', 'price': 100, 'income': 10},
            {'id': 2, 'name': 'Ресторан', 'emoji': '🍽️', 'price': 500, 'income': 50},
            {'id': 3, 'name': 'Отель', 'emoji': '🏨', 'price': 2000, 'income': 200},
            {'id': 4, 'name': 'ТЦ', 'emoji': '🏬', 'price': 10000, 'income': 1000},
            {'id': 5, 'name': 'Завод', 'emoji': '🏭', 'price': 50000, 'income': 5000},
            {'id': 6, 'name': 'Корпорация', 'emoji': '🏢', 'price': 200000, 'income': 20000},
        ]
    
    def init_businesses(self):
        """Инициализация бизнесов в БД"""
        businesses = self.get_business_list()
        for b in businesses:
            existing = self.db.get_business(b['id'])
            if not existing:
                business = Business(
                    id=b['id'],
                    name=b['name'],
                    emoji=b['emoji'],
                    price=b['price'],
                    income_per_hour=b['income']
                )
                self.db.session.add(business)
        self.db.session.commit()