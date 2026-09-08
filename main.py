import telebot
from telebot import types
import sqlite3
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

if not TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN не найден!")
    exit(1)

bot = telebot.TeleBot(TOKEN)

# База данных
conn = sqlite3.connect('empire.db', check_same_thread=False)
cursor = conn.cursor()

# Создаём таблицы
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                  (user_id INTEGER PRIMARY KEY, 
                   balance REAL DEFAULT 100, 
                   click_power INTEGER DEFAULT 1,
                   total_clicks INTEGER DEFAULT 0)''')
conn.commit()

# Клавиатура
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('💰 Баланс')
    btn2 = types.KeyboardButton('👆 Клик')
    btn3 = types.KeyboardButton('🏪 Бизнесы')
    btn4 = types.KeyboardButton('📈 Акции')
    btn5 = types.KeyboardButton('👤 Профиль')
    btn6 = types.KeyboardButton('🔄 Обновить')
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    bot.send_message(
        message.chat.id,
        f"🏢 *Business Empire*\n\n"
        f"Добро пожаловать, {message.from_user.first_name}!\n"
        f"💰 Баланс: *100.00*\n"
        f"👆 Сила клика: *1*",
        reply_markup=main_menu(),
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda m: m.text == '👆 Клик')
def click(message):
    user_id = message.from_user.id
    cursor.execute("SELECT click_power, balance FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    if result:
        power, balance = result
        earned = power
        new_balance = balance + earned
        cursor.execute("UPDATE users SET balance = ?, total_clicks = total_clicks + 1 WHERE user_id = ?", 
                       (new_balance, user_id))
        conn.commit()
        bot.send_message(
            message.chat.id,
            f"👆 *+{earned} монет!*\n"
            f"💰 Новый баланс: *{new_balance:.2f}*",
            parse_mode='Markdown'
        )

@bot.message_handler(func=lambda m: m.text == '💰 Баланс')
def balance(message):
    user_id = message.from_user.id
    cursor.execute("SELECT balance, click_power, total_clicks FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    if result:
        balance, power, clicks = result
        bot.send_message(
            message.chat.id,
            f"💰 *Баланс:* {balance:.2f}\n"
            f"👆 *Сила клика:* {power}\n"
            f"🔄 *Всего кликов:* {clicks}",
            parse_mode='Markdown'
        )

@bot.message_handler(func=lambda m: m.text == '🔄 Обновить')
def refresh(message):
    user_id = message.from_user.id
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    if result:
        balance = result[0]
        bot.send_message(
            message.chat.id,
            f"🔄 *Обновлено!*\n"
            f"💰 Баланс: *{balance:.2f}*",
            parse_mode='Markdown'
        )

@bot.message_handler(func=lambda m: m.text == '🏪 Бизнесы')
def businesses(message):
    text = "🏪 *Доступные бизнесы:*\n\n"
    text += "☕ Кофейня - 100💰\n"
    text += "🍽️ Ресторан - 500💰\n"
    text += "🏨 Отель - 2000💰\n"
    text += "🏬 ТЦ - 10000💰\n"
    text += "🏭 Завод - 50000💰"
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == '📈 Акции')
def shares(message):
    bot.send_message(
        message.chat.id,
        "📈 *Акции*\n\nСкоро будут доступны!",
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda m: m.text == '👤 Профиль')
def profile(message):
    user = message.from_user
    cursor.execute("SELECT balance, total_clicks FROM users WHERE user_id = ?", (user.id,))
    result = cursor.fetchone()
    if result:
        balance, clicks = result
        bot.send_message(
            message.chat.id,
            f"👤 *Профиль*\n\n"
            f"🆔 ID: `{user.id}`\n"
            f"👤 Имя: {user.first_name}\n"
            f"💰 Баланс: *{balance:.2f}*\n"
            f"🔄 Кликов: *{clicks}*",
            parse_mode='Markdown'
        )

@bot.message_handler(commands=['menu'])
def menu(message):
    bot.send_message(message.chat.id, "📋 Меню:", reply_markup=main_menu())

print("🚀 Бот Business Empire запущен!")
print(f"🤖 Токен: {TOKEN[:10]}...")
print("📱 Откройте Telegram и напишите /start")
print("⏹️ Нажмите Ctrl+C для остановки")

bot.polling(none_stop=True)
