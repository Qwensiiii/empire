from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Главная клавиатура"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='💰 Баланс'), KeyboardButton(text='🏪 Бизнесы')],
            [KeyboardButton(text='📈 Акции'), KeyboardButton(text='👤 Профиль')],
            [KeyboardButton(text='🔄 Обновить')]
        ],
        resize_keyboard=True
    )

def get_business_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для бизнесов"""
    builder = InlineKeyboardBuilder()
    businesses = [
        ('☕ Кофейня', 'buy_1'),
        ('🍽️ Ресторан', 'buy_2'),
        ('🏨 Отель', 'buy_3'),
        ('🏬 ТЦ', 'buy_4'),
        ('🏭 Завод', 'buy_5'),
        ('🏢 Корпорация', 'buy_6'),
    ]
    
    for name, callback in businesses:
        builder.button(text=name, callback_data=callback)
    
    builder.button(text='🔙 Назад', callback_data='back_main')
    builder.adjust(2)
    return builder.as_markup()

def get_business_actions(business_id: int) -> InlineKeyboardMarkup:
    """Клавиатура действий с бизнесом"""
    builder = InlineKeyboardBuilder()
    builder.button(text='⬆️ Улучшить', callback_data=f'upgrade_{business_id}')
    builder.button(text='📈 Купить акции', callback_data=f'shares_{business_id}')
    builder.button(text='🔙 Назад', callback_data='back_businesses')
    builder.adjust(2)
    return builder.as_markup()

def get_share_keyboard(business_id: int) -> InlineKeyboardMarkup:
    """Клавиатура покупки акций"""
    builder = InlineKeyboardBuilder()
    for i in [1, 5, 10, 50]:
        builder.button(text=f'{i} шт', callback_data=f'buy_share_{business_id}_{i}')
    builder.button(text='🔙 Назад', callback_data=f'business_{business_id}')
    builder.adjust(2)
    return builder.as_markup()

def get_profile_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура профиля"""
    builder = InlineKeyboardBuilder()
    builder.button(text='📊 Статистика', callback_data='stats')
    builder.button(text='🏆 Рейтинг', callback_data='rating')
    builder.button(text='🔙 Назад', callback_data='back_main')
    builder.adjust(2)
    return builder.as_markup()