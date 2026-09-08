from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime

from database.crud import DatabaseCRUD
from game.economy import EconomyManager
from bot.keyboards import *

router = Router()

# Инициализация (будет передаваться из bot.py)
db = None
economy = None

def setup_handlers(db_instance, economy_instance):
    global db, economy
    db = db_instance
    economy = economy_instance

@router.message(CommandStart())
async def start_command(message: Message):
    user = db.get_or_create_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )
    
    await message.answer(
        f"🏢 *Business Empire*\n\n"
        f"Добро пожаловать, {message.from_user.first_name}!\n"
        f"💰 Твой баланс: *{user.balance:.2f}*\n"
        f"👆 Сила клика: *{user.click_power}*\n\n"
        f"Кликай на кнопку ниже или покупай бизнесы!",
        reply_markup=get_main_keyboard(),
        parse_mode='Markdown'
    )

@router.message(F.text == '💰 Баланс')
async def show_balance(message: Message):
    user = db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Пользователь не найден")
        return
    
    income = economy.calculate_income(message.from_user.id)
    businesses = db.get_user_businesses(message.from_user.id)
    
    text = (
        f"💰 *Баланс:* {user.balance:.2f}\n"
        f"👆 *Сила клика:* {user.click_power}\n"
        f"🏪 *Бизнесов:* {len(businesses)}\n"
        f"💵 *Доход в час:* {income:.2f}\n"
        f"🔄 *Всего кликов:* {user.total_clicks}\n"
        f"📈 *Всего заработано:* {user.total_earned:.2f}"
    )
    await message.answer(text, parse_mode='Markdown')

@router.message(F.text == '🏪 Бизнесы')
async def show_businesses(message: Message):
    businesses = economy.get_business_list()
    user = db.get_user(message.from_user.id)
    user_businesses = db.get_user_businesses(message.from_user.id)
    user_business_ids = [b.id for b in user_businesses]
    
    text = "🏪 *Доступные бизнесы:*\n\n"
    for b in businesses:
        owned = "✅ Владеете" if b['id'] in user_business_ids else "❌ Не куплен"
        text += f"{b['emoji']} *{b['name']}*\n"
        text += f"💰 Цена: {b['price']:.2f} | 💵 Доход: {b['income']}/час\n"
        text += f"Статус: {owned}\n\n"
    
    await message.answer(text, reply_markup=get_business_keyboard(), parse_mode='Markdown')

@router.callback_query(F.data.startswith('buy_'))
async def buy_business(callback: CallbackQuery):
    business_id = int(callback.data.split('_')[1])
    result = db.buy_business(callback.from_user.id, business_id)
    
    if result['success']:
        await callback.message.edit_text(
            f"{result['message']}\n"
            f"💰 Новый баланс: {result['balance']:.2f}",
            reply_markup=get_business_keyboard()
        )
    else:
        await callback.answer(result['message'], show_alert=True)

@router.callback_query(F.data.startswith('upgrade_'))
async def upgrade_business(callback: CallbackQuery):
    business_id = int(callback.data.split('_')[1])
    result = db.upgrade_business(callback.from_user.id, business_id)
    
    if result['success']:
        await callback.message.edit_text(
            f"{result['message']}\n"
            f"💰 Новый баланс: {result['balance']:.2f}",
            reply_markup=get_business_actions(business_id)
        )
    else:
        await callback.answer(result['message'], show_alert=True)

@router.callback_query(F.data.startswith('shares_'))
async def show_share_options(callback: CallbackQuery):
    business_id = int(callback.data.split('_')[1])
    business = db.get_business(business_id)
    
    if business:
        await callback.message.edit_text(
            f"📈 *Покупка акций {business.emoji} {business.name}*\n"
            f"💰 Цена одной акции: {business.price * 0.1:.2f}\n\n"
            f"Выберите количество:",
            reply_markup=get_share_keyboard(business_id),
            parse_mode='Markdown'
        )

@router.callback_query(F.data.startswith('buy_share_'))
async def buy_share(callback: CallbackQuery):
    _, _, business_id, quantity = callback.data.split('_')
    business_id = int(business_id)
    quantity = int(quantity)
    
    result = db.buy_share(callback.from_user.id, business_id, quantity)
    
    if result['success']:
        await callback.message.edit_text(
            f"{result['message']}\n"
            f"💰 Новый баланс: {result['balance']:.2f}",
            reply_markup=get_share_keyboard(business_id)
        )
    else:
        await callback.answer(result['message'], show_alert=True)

@router.message(F.text == '📈 Акции')
async def show_shares(message: Message):
    shares = db.get_user_shares(message.from_user.id)
    
    if not shares:
        await message.answer("📉 У вас пока нет акций. Купите их через меню бизнеса!")
        return
    
    text = "📈 *Ваши акции:*\n\n"
    for share in shares:
        business = db.get_business(share.business_id)
        if business:
            text += f"{business.emoji} *{business.name}*: {share.quantity} шт\n"
            text += f"💰 Стоимость акции: {business.price * 0.1:.2f}\n\n"
    
    await message.answer(text, parse_mode='Markdown')

@router.message(F.text == '👤 Профиль')
async def show_profile(message: Message):
    user = db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Пользователь не найден")
        return
    
    businesses = db.get_user_businesses(message.from_user.id)
    shares = db.get_user_shares(message.from_user.id)
    
    text = (
        f"👤 *Профиль*\n\n"
        f"🆔 ID: {user.user_id}\n"
        f"👤 Имя: {user.first_name or 'Не указано'}\n"
        f"💰 Баланс: {user.balance:.2f}\n"
        f"👆 Сила клика: {user.click_power}\n"
        f"🏪 Бизнесов: {len(businesses)}\n"
        f"📈 Акций: {len(shares)}\n"
        f"🔄 Всего кликов: {user.total_clicks}\n"
        f"📈 Всего заработано: {user.total_earned:.2f}\n"
        f"📅 В игре с: {user.created_at.strftime('%d.%m.%Y')}"
    )
    
    await message.answer(text, reply_markup=get_profile_keyboard(), parse_mode='Markdown')

@router.message(F.text == '🔄 Обновить')
async def refresh(message: Message):
    user = db.get_user(message.from_user.id)
    if user:
        income = economy.calculate_income(message.from_user.id)
        await message.answer(
            f"🔄 *Обновлено*\n\n"
            f"💰 Баланс: {user.balance:.2f}\n"
            f"💵 Доход в час: {income:.2f}\n"
            f"👆 Сила клика: {user.click_power}",
            parse_mode='Markdown'
        )

@router.callback_query(F.data == 'back_main')
async def back_to_main(callback: CallbackQuery):
    user = db.get_user(callback.from_user.id)
    await callback.message.edit_text(
        f"🏢 *Business Empire*\n\n"
        f"💰 Баланс: {user.balance:.2f}\n"
        f"👆 Сила клика: {user.click_power}",
        reply_markup=None,
        parse_mode='Markdown'
    )
    await callback.message.answer("Главное меню:", reply_markup=get_main_keyboard())