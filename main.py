import telebot
from telebot import types
import sqlite3
import os
import json
import logging
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

if not TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN не найден!")
    exit(1)

bot = telebot.TeleBot(TOKEN)
logging.basicConfig(level=logging.INFO)

# База данных
conn = sqlite3.connect('empire.db', check_same_thread=False)
cursor = conn.cursor()

# Создаём таблицы
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                  (user_id INTEGER PRIMARY KEY, 
                   balance REAL DEFAULT 100, 
                   click_power INTEGER DEFAULT 1,
                   total_clicks INTEGER DEFAULT 0,
                   total_earned REAL DEFAULT 0)''')
conn.commit()

# ============================================
# 1. КОМАНДА /start — отправляет Mini App
# ============================================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    
    # Кнопка для запуска Mini App
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        "🎮 Играть", 
        web_app=types.WebAppInfo(url="https://empire-ваш-проект.vercel.app/static/index.html")  # ЗАМЕНИТЕ на ваш URL
    ))
    
    bot.send_message(
        message.chat.id,
        f"🏢 *Business Empire*\n\n"
        f"Добро пожаловать, {message.from_user.first_name}!\n"
        f"💰 Баланс: *100.00*\n"
        f"👆 Сила клика: *1*\n\n"
        f"👇 Нажмите кнопку, чтобы открыть игру!",
        reply_markup=markup,
        parse_mode='Markdown'
    )

# ============================================
# 2. ОБРАБОТКА ДАННЫХ ИЗ MINI APP
# ============================================
@bot.message_handler(content_types=['web_app_data'])
def handle_web_app_data(message):
    """Принимает данные из Mini App и обрабатывает"""
    try:
        data = json.loads(message.web_app_data.data)
        action = data.get('action')
        user_id = message.from_user.id
        
        logging.info(f"📥 Получены данные от {user_id}: {data}")
        
        if action == 'click':
            # Получаем силу клика
            cursor.execute("SELECT click_power FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            if result:
                power = result[0]
                earned = power
                
                # Обновляем баланс
                cursor.execute("""
                    UPDATE users 
                    SET balance = balance + ?, 
                        total_clicks = total_clicks + 1, 
                        total_earned = total_earned + ? 
                    WHERE user_id = ?
                """, (earned, earned, user_id))
                conn.commit()
                
                # Получаем обновлённые данные
                cursor.execute("""
                    SELECT balance, click_power, total_clicks, total_earned 
                    FROM users WHERE user_id = ?
                """, (user_id,))
                user_data = cursor.fetchone()
                
                if user_data:
                    response = {
                        'balance': user_data[0],
                        'click_power': user_data[1],
                        'total_clicks': user_data[2],
                        'total_earned': user_data[3]
                    }
                    # Отправляем ответ в Mini App
                    bot.send_message(
                        user_id,
                        json.dumps(response)
                    )
                    logging.info(f"✅ Баланс обновлён: {user_data[0]}")
        
        elif action == 'get_data':
            # Получение всех данных пользователя
            cursor.execute("""
                SELECT balance, click_power, total_clicks, total_earned 
                FROM users WHERE user_id = ?
            """, (user_id,))
            user_data = cursor.fetchone()
            
            if user_data:
                response = {
                    'balance': user_data[0],
                    'click_power': user_data[1],
                    'total_clicks': user_data[2],
                    'total_earned': user_data[3]
                }
                bot.send_message(
                    user_id,
                    json.dumps(response)
                )
            else:
                bot.send_message(user_id, json.dumps({'error': 'User not found'}))
                
    except json.JSONDecodeError as e:
        logging.error(f"JSON ошибка: {e}")
        bot.send_message(message.from_user.id, json.dumps({'error': 'Invalid data format'}))
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        bot.send_message(message.from_user.id, json.dumps({'error': str(e)}))

# ============================================
# 3. КНОПКИ МЕНЮ
# ============================================
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        types.KeyboardButton('🏪 Бизнесы'),
        types.KeyboardButton('📈 Акции'),
        types.KeyboardButton('👤 Профиль'),
        types.KeyboardButton('🎮 Mini App')
    )
    return markup

@bot.message_handler(func=lambda m: m.text == '🏪 Бизнесы')
def businesses(message):
    user_id = message.from_user.id
    
    business_list = [
        {'id': 1, 'name': 'Кофейня', 'emoji': '☕', 'price': 100, 'income': 10},
        {'id': 2, 'name': 'Ресторан', 'emoji': '🍽️', 'price': 500, 'income': 50},
        {'id': 3, 'name': 'Отель', 'emoji': '🏨', 'price': 2000, 'income': 200},
        {'id': 4, 'name': 'ТЦ', 'emoji': '🏬', 'price': 10000, 'income': 1000},
        {'id': 5, 'name': 'Завод', 'emoji': '🏭', 'price': 50000, 'income': 5000},
    ]
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    for b in business_list:
        markup.add(types.InlineKeyboardButton(
            f"{b['emoji']} {b['name']} - {b['price']}💰",
            callback_data=f"buy_business_{b['id']}"
        ))
    
    bot.send_message(
        message.chat.id,
        "🏪 *Доступные бизнесы:*\n\nВыберите для покупки:",
        reply_markup=markup,
        parse_mode='Markdown'
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_business_'))
def buy_business(call):
    user_id = call.from_user.id
    business_id = int(call.data.split('_')[2])
    
    businesses = {
        1: {'name': 'Кофейня', 'emoji': '☕', 'price': 100, 'income': 10},
        2: {'name': 'Ресторан', 'emoji': '🍽️', 'price': 500, 'income': 50},
        3: {'name': 'Отель', 'emoji': '🏨', 'price': 2000, 'income': 200},
        4: {'name': 'ТЦ', 'emoji': '🏬', 'price': 10000, 'income': 1000},
        5: {'name': 'Завод', 'emoji': '🏭', 'price': 50000, 'income': 5000},
    }
    
    business = businesses.get(business_id)
    if not business:
        bot.answer_callback_query(call.id, "❌ Бизнес не найден")
        return
    
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    balance = cursor.fetchone()[0]
    
    if balance < business['price']:
        bot.answer_callback_query(call.id, f"❌ Нужно: {business['price']}💰")
        return
    
    cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", 
                   (business['price'], user_id))
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS businesses 
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         user_id INTEGER,
         name TEXT,
         emoji TEXT,
         price REAL,
         income_per_hour REAL,
         level INTEGER DEFAULT 1,
         purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
    """, (user_id, business['name'], business['emoji'], business['price'], business['income']))
    conn.commit()
    
    bot.answer_callback_query(call.id, f"✅ Куплено {business['emoji']} {business['name']}!")

@bot.message_handler(func=lambda m: m.text == '📈 Акции')
def shares(message):
    bot.send_message(
        message.chat.id,
        "📈 *Акции*\n\nСкоро будут доступны!",
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda m: m.text == '👤 Профиль')
def profile(message):
    user_id = message.from_user.id
    cursor.execute("SELECT balance, click_power, total_clicks, total_earned FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if user:
        bot.send_message(
            message.chat.id,
            f"👤 *Профиль*\n\n"
            f"🆔 ID: `{user_id}`\n"
            f"👤 Имя: {message.from_user.first_name}\n"
            f"💰 Баланс: *{user[0]:.2f}*\n"
            f"👆 Сила клика: *{user[1]}*\n"
            f"🔄 Кликов: *{user[2]}*\n"
            f"📈 Заработано: *{user[3]:.2f}*",
            parse_mode='Markdown'
        )

@bot.message_handler(func=lambda m: m.text == '🎮 Mini App')
def mini_app_button(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        "🎮 Открыть игру",
        web_app=types.WebAppInfo(url="https://empire-ваш-проект.vercel.app/static/index.html")  # ЗАМЕНИТЕ на ваш URL
    ))
    bot.send_message(
        message.chat.id,
        "🎮 Нажмите кнопку, чтобы открыть игру:",
        reply_markup=markup
    )

# ============================================
# 4. ЗАПУСК
# ============================================
print("🚀 Бот Business Empire запущен!")
print(f"🤖 Токен: {TOKEN[:10]}...")
print("📱 Откройте Telegram и напишите /start")
print("⏹️ Нажмите Ctrl+C для остановки")

bot.polling(none_stop=True)