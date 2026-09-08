from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from .models import User, Business, Share, ClickHistory

class DatabaseCRUD:
    def __init__(self, session: Session):
        self.session = session
    
    # === USER ===
    def get_or_create_user(self, user_id: int, username: str = None, first_name: str = None) -> User:
        user = self.session.query(User).filter_by(user_id=user_id).first()
        if not user:
            user = User(
                user_id=user_id,
                username=username,
                first_name=first_name,
                balance=100.0,  # Стартовый бонус
                click_power=1
            )
            self.session.add(user)
            self.session.commit()
        return user
    
    def get_user(self, user_id: int) -> User:
        return self.session.query(User).filter_by(user_id=user_id).first()
    
    def update_balance(self, user_id: int, amount: float) -> User:
        user = self.get_user(user_id)
        if user:
            user.balance += amount
            if amount > 0:
                user.total_earned += amount
            self.session.commit()
        return user
    
    def update_click_power(self, user_id: int, new_power: int) -> User:
        user = self.get_user(user_id)
        if user:
            user.click_power = new_power
            self.session.commit()
        return user
    
    def add_click(self, user_id: int, clicks: int = 1) -> User:
        user = self.get_user(user_id)
        if user:
            user.total_clicks += clicks
            user.last_click = datetime.utcnow()
            self.session.commit()
            
            # Сохраняем историю
            history = ClickHistory(
                user_id=user_id,
                clicks=clicks,
                earned=user.click_power * clicks
            )
            self.session.add(history)
            self.session.commit()
        return user
    
    # === BUSINESS ===
    def get_all_businesses(self) -> list:
        return self.session.query(Business).all()
    
    def get_business(self, business_id: int) -> Business:
        return self.session.query(Business).filter_by(id=business_id).first()
    
    def get_user_businesses(self, user_id: int) -> list:
        return self.session.query(Business).filter_by(owner_id=user_id).all()
    
    def buy_business(self, user_id: int, business_id: int) -> dict:
        user = self.get_user(user_id)
        business = self.get_business(business_id)
        
        if not user or not business:
            return {'success': False, 'message': 'Бизнес не найден'}
        
        if user.balance < business.price:
            return {'success': False, 'message': f'Недостаточно средств! Нужно: {business.price:.2f}'}
        
        # Проверяем, не владеет ли уже
        existing = self.session.query(Business).filter_by(
            owner_id=user_id, 
            id=business_id
        ).first()
        
        if existing:
            return {'success': False, 'message': 'Вы уже владеете этим бизнесом!'}
        
        # Покупаем
        user.balance -= business.price
        new_business = Business(
            name=business.name,
            emoji=business.emoji,
            price=business.price,
            income_per_hour=business.income_per_hour,
            level=1,
            owner_id=user_id
        )
        self.session.add(new_business)
        self.session.commit()
        
        return {
            'success': True, 
            'message': f'✅ Вы купили {business.emoji} {business.name}!',
            'balance': user.balance
        }
    
    def upgrade_business(self, user_id: int, business_id: int) -> dict:
        business = self.session.query(Business).filter_by(
            id=business_id, 
            owner_id=user_id
        ).first()
        
        if not business:
            return {'success': False, 'message': 'Бизнес не найден'}
        
        if business.level >= business.max_level:
            return {'success': False, 'message': 'Максимальный уровень!'}
        
        upgrade_cost = business.price * 0.5 * business.level
        user = self.get_user(user_id)
        
        if user.balance < upgrade_cost:
            return {'success': False, 'message': f'Недостаточно! Нужно: {upgrade_cost:.2f}'}
        
        user.balance -= upgrade_cost
        business.level += 1
        business.income_per_hour *= 1.2  # +20% к доходу
        self.session.commit()
        
        return {
            'success': True,
            'message': f'⬆️ {business.emoji} {business.name} улучшен до {business.level} уровня!',
            'balance': user.balance
        }
    
    # === SHARES ===
    def buy_share(self, user_id: int, business_id: int, quantity: int = 1) -> dict:
        user = self.get_user(user_id)
        business = self.get_business(business_id)
        
        if not business:
            return {'success': False, 'message': 'Бизнес не найден'}
        
        share_price = business.price * 0.1  # Акция стоит 10% от цены бизнеса
        total_cost = share_price * quantity
        
        if user.balance < total_cost:
            return {'success': False, 'message': f'Недостаточно средств! Нужно: {total_cost:.2f}'}
        
        user.balance -= total_cost
        
        share = self.session.query(Share).filter_by(
            user_id=user_id,
            business_id=business_id
        ).first()
        
        if share:
            share.quantity += quantity
        else:
            share = Share(user_id=user_id, business_id=business_id, quantity=quantity)
            self.session.add(share)
        
        self.session.commit()
        
        return {
            'success': True,
            'message': f'📈 Куплено {quantity} акций {business.emoji} {business.name}!',
            'balance': user.balance
        }
    
    def get_user_shares(self, user_id: int) -> list:
        return self.session.query(Share).filter_by(user_id=user_id).all()
    
    # === INCOME ===
    def calculate_income(self, user_id: int) -> float:
        businesses = self.get_user_businesses(user_id)
        total_income = sum(b.income_per_hour for b in businesses)
        
        # Доход от акций (1% от дохода бизнеса за каждую акцию)
        shares = self.session.query(Share).filter_by(user_id=user_id).all()
        for share in shares:
            business = self.get_business(share.business_id)
            if business and business.owner_id != user_id:
                total_income += business.income_per_hour * 0.01 * share.quantity
        
        return total_income
    
    def collect_income(self, user_id: int) -> dict:
        user = self.get_user(user_id)
        if not user:
            return {'success': False, 'message': 'Пользователь не найден'}
        
        income = self.calculate_income(user_id)
        if income > 0:
            user.balance += income
            user.last_income = datetime.utcnow()
            self.session.commit()
            return {
                'success': True,
                'message': f'💰 Получен доход: {income:.2f}',
                'balance': user.balance,
                'income': income
            }
        return {'success': False, 'message': 'Нет активных бизнесов'}