import telebot
from telebot import types
import sqlite3
import os
import json
import logging
import threading
import time
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

if not TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN не найден в файле .env!")
    exit(1)

bot = telebot.TeleBot(TOKEN)
logging.basicConfig(level=logging.INFO)

# ============================================
# БАЗА ДАННЫХ (SQLite)
# ============================================
DB_LOCK = threading.Lock()
conn = sqlite3.connect('empire.db', check_same_thread=False, timeout=30)
cursor = conn.cursor()

# Создаём таблицы
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                  (user_id INTEGER PRIMARY KEY, 
                   balance REAL DEFAULT 100, 
                   click_power INTEGER DEFAULT 1,
                   total_clicks INTEGER DEFAULT 0,
                   total_earned REAL DEFAULT 0)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS businesses 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   user_id INTEGER,
                   name TEXT,
                   emoji TEXT,
                   price REAL,
                   income_per_hour REAL)''')
conn.commit()

# ============================================
# КЭШ (для быстрой работы)
# ============================================
cache = {}
cache_time = {}

def get_cached_user(user_id):
    """Получает данные пользователя из кэша или БД"""
    now = time.time()
    if user_id in cache and (now - cache_time.get(user_id, 0)) < 10:
        return cache[user_id]
    
    with DB_LOCK:
        cursor.execute(
            "SELECT balance, click_power, total_clicks, total_earned FROM users WHERE user_id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
    
    if row:
        cache[user_id] = {
            'balance': row[0],
            'click_power': row[1],
            'total_clicks': row[2],
            'total_earned': row[3]
        }
        cache_time[user_id] = now
        return cache[user_id]
    return None

# ============================================
# КЛАВИАТУРА
# ============================================
def main_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        types.KeyboardButton('🏪 Бизнесы'),
        types.KeyboardButton('📈 Акции'),
        types.KeyboardButton('👤 Профиль'),
        types.KeyboardButton('🎮 Mini App'),
        types.KeyboardButton('🔄 Обновить')
    )
    return markup

# ============================================
# ОБРАБОТЧИКИ КОМАНД
# ============================================

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    
    # Создаём пользователя, если его нет
    with DB_LOCK:
        cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
    
    user = get_cached_user(user_id)
    
    # Кнопка для открытия мини-приложения
    webapp_url = "https://empire-one-iota.vercel.app/"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        "🎮 Играть",
        web_app=types.WebAppInfo(url=webapp_url)
    ))
    
    bot.send_message(
        message.chat.id,
        f"🏢 *Business Empire*\n\n"
        f"Добро пожаловать, {message.from_user.first_name}!\n"
        f"💰 Баланс: *{user['balance']:.2f}*\n"
        f"👆 Сила клика: *{user['click_power']}*",
        reply_markup=markup,
        parse_mode='Markdown'
    )
    
    # Отправляем основную клавиатуру
    bot.send_message(
        message.chat.id,
        "📋 Меню:",
        reply_markup=main_keyboard()
    )

# ============================================
# ОБРАБОТЧИКИ КНОПОК
# ============================================

@bot.message_handler(func=lambda m: m.text == '🔄 Обновить')
def refresh(message):
    user = get_cached_user(message.from_user.id)
    if user:
        bot.send_message(
            message.chat.id,
            f"🔄 *Обновлено!*\n"
            f"💰 Баланс: *{user['balance']:.2f}*\n"
            f"👆 Сила клика: *{user['click_power']}*",
            parse_mode='Markdown'
        )

@bot.message_handler(func=lambda m: m.text == '👤 Профиль')
def profile(message):
    user = get_cached_user(message.from_user.id)
    if user:
        bot.send_message(
            message.chat.id,
            f"👤 *Профиль*\n\n"
            f"🆔 ID: `{message.from_user.id}`\n"
            f"👤 Имя: {message.from_user.first_name}\n"
            f"💰 Баланс: *{user['balance']:.2f}*\n"
            f"👆 Сила клика: *{user['click_power']}*\n"
            f"🔄 Кликов: *{user['total_clicks']}*\n"
            f"📈 Заработано: *{user['total_earned']:.2f}*",
            parse_mode='Markdown'
        )

@bot.message_handler(func=lambda m: m.text == '🏪 Бизнесы')
def businesses(message):
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
            callback_data=f"buy_{b['id']}"
        ))
    
    bot.send_message(
        message.chat.id,
        "🏪 *Доступные бизнесы:*\n\nВыберите для покупки:",
        reply_markup=markup,
        parse_mode='Markdown'
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def buy_business(call):
    user_id = call.from_user.id
    business_id = int(call.data.split('_')[1])
    
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
    
    user = get_cached_user(user_id)
    if not user:
        bot.answer_callback_query(call.id, "❌ Пользователь не найден")
        return
    
    if user['balance'] < business['price']:
        bot.answer_callback_query(call.id, f"❌ Нужно: {business['price']}💰")
        return
    
    with DB_LOCK:
        cursor.execute(
            "UPDATE users SET balance = balance - ? WHERE user_id = ?",
            (business['price'], user_id)
        )
        cursor.execute(
            "INSERT INTO businesses (user_id, name, emoji, price, income_per_hour) VALUES (?, ?, ?, ?, ?)",
            (user_id, business['name'], business['emoji'], business['price'], business['income'])
        )
        conn.commit()
        # Обновляем кэш
        cursor.execute(
            "SELECT balance, click_power, total_clicks, total_earned FROM users WHERE user_id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        if row:
            cache[user_id] = {
                'balance': row[0],
                'click_power': row[1],
                'total_clicks': row[2],
                'total_earned': row[3]
            }
            cache_time[user_id] = time.time()
    
    bot.answer_callback_query(call.id, f"✅ Куплено {business['emoji']} {business['name']}!")

@bot.message_handler(func=lambda m: m.text == '📈 Акции')
def shares(message):
    bot.send_message(
        message.chat.id,
        "📈 *Акции*\n\nСкоро будут доступны!",
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda m: m.text == '🎮 Mini App')
def mini_app(message):
    webapp_url = "https://empire-one-iota.vercel.app/"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        "🎮 Открыть игру",
        web_app=types.WebAppInfo(url=webapp_url)
    ))
    bot.send_message(
        message.chat.id,
        "🎮 Нажмите кнопку, чтобы открыть игру:",
        reply_markup=markup
    )

# ============================================
# ОБРАБОТКА ДАННЫХ ИЗ MINI APP (САМОЕ ВАЖНОЕ!)
# ============================================
@bot.message_handler(content_types=['web_app_data'])
def handle_web_app(message):
    try:
        data = json.loads(message.web_app_data.data)
        action = data.get('action')
        user_id = message.from_user.id
        
        print(f"📥 Получены данные от {user_id}: {data}")  # Лог в Termux
        
        if action == 'get_data':
            user = get_cached_user(user_id)
            if user:
                bot.send_message(user_id, json.dumps(user))
            return
        
        if action == 'click':
            with DB_LOCK:
                cursor.execute("SELECT click_power FROM users WHERE user_id = ?", (user_id,))
                result = cursor.fetchone()
                if not result:
                    return
                earned = result[0]
                
                cursor.execute("""
                    UPDATE users 
                    SET balance = balance + ?, 
                        total_clicks = total_clicks + 1, 
                        total_earned = total_earned + ? 
                    WHERE user_id = ?
                    RETURNING balance, click_power, total_clicks, total_earned
                """, (earned, earned, user_id))
                new_data = cursor.fetchone()
                conn.commit()
            
            if new_data:
                response = {
                    'balance': new_data[0],
                    'click_power': new_data[1],
                    'total_clicks': new_data[2],
                    'total_earned': new_data[3]
                }
                cache[user_id] = response
                cache_time[user_id] = time.time()
                bot.send_message(user_id, json.dumps(response))
                print(f"✅ Баланс обновлён: {new_data[0]}")
                
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        print(f"❌ Ошибка: {e}")

# ============================================
# ЗАПУСК
# ============================================
if __name__ == "__main__":
    print("🚀 Бот Business Empire запущен!")
    print(f"🤖 Токен: {TOKEN[:10]}...")
    print("📱 Откройте Telegram и напишите /start")
    print("⏹️ Нажмите Ctrl+C для остановки")
    
    bot.polling(none_stop=True)