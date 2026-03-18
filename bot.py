import os
import time
import threading
from datetime import datetime, timezone, timedelta
import requests
from lxml import html
import schedule
import telebot
from telebot import types
from http.server import BaseHTTPRequestHandler, HTTPServer

# Убираем load_dotenv(), чтобы скрипт смотрел только в настройки хостинга!

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

# Добавим вывод в логи Bothost, чтобы вы точно видели, дошли ли данные
print("--- ОТЛАДКА ---")
print(f"Токен получен: {TELEGRAM_TOKEN is not None}")
print(f"Chat ID получен: {CHAT_ID is not None}")
print("---------------")

if not TELEGRAM_TOKEN or not CHAT_ID:
    raise ValueError("Ошибка: Хостинг не передал переменные TELEGRAM_TOKEN или CHAT_ID")

URL = 'https://lab-store071.ru/catalog/kupit-makbuk-v-tule/'
XPATH_PRICE = '//*[@id="bx_1847241719_488"]/a/div[1]/span[2]'
FILE_NAME = 'prices.txt'

bot = telebot.TeleBot(TELEGRAM_TOKEN)

def fetch_and_save_price():
    print("Начинаю проверку цены на сайте...", flush=True)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(URL, headers=headers)
        response.raise_for_status()
        tree = html.fromstring(response.content)
        price_element = tree.xpath(XPATH_PRICE)
        
        if price_element:
            price = price_element[0].text_content().strip()
            print(f"Цена успешно найдена: {price}", flush=True)
        else:
            price = "Цена не найдена"
            print("Внимание: Элемент с ценой не найден по XPATH!", flush=True)
            
    except Exception as e:
        price = f"Ошибка парсинга: {e}"
        print(f"Произошла ошибка при загрузке страницы: {e}", flush=True)

    msk_tz = timezone(timedelta(hours=3))
    now = datetime.now(msk_tz)
    
    date_str = now.strftime('%d.%m.%Y')
    time_str = now.strftime('%H:%M:%S')
    log_entry = f"{date_str} / {time_str} МСК / {price}\n"
    
    # Сохраняем в файл
    with open(FILE_NAME, 'a', encoding='utf-8') as file:
        file.write(log_entry)
        print("Данные записаны в файл prices.txt", flush=True)
        
    # Отправляем в Telegram
    try:
        bot.send_message(CHAT_ID, f"🕒 Автоматическая проверка:\n{log_entry.strip()}")
        print("Уведомление успешно отправлено в Telegram.", flush=True)
    except Exception as e:
        print(f"Ошибка отправки сообщения в Telegram: {e}", flush=True)
        
    print("-" * 30, flush=True)



def run_schedule():
    schedule.every(1).hours.do(fetch_and_save_price)
    while True:
        schedule.run_pending()
        time.sleep(1)

# --- Команды бота ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    btn_check = types.KeyboardButton('🔍 Проверить цену')
    btn_file = types.KeyboardButton('📄 Скачать историю')
    
    markup.add(btn_check, btn_file)
    
    bot.reply_to(
        message, 
        "Привет! Я бот для парсинга цен.",
        reply_markup=markup

    )

@bot.message_handler(commands=['keys'])
def send_keys(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    btn_check = types.KeyboardButton('🔍 Проверить цену')
    btn_file = types.KeyboardButton('📄 Скачать историю')
    
    markup.add(btn_check, btn_file)

    bot.reply_to(
        message,
        "Добавляю клавиатуру",
        reply_markup=markup
    )

@bot.message_handler(commands=['check'])
def manual_check(message):
    bot.reply_to(message, "Запускаю проверку...")
    fetch_and_save_price()

@bot.message_handler(commands=['file'])
def send_file(message):
    try:
        with open(FILE_NAME, 'rb') as file:
            bot.send_document(message.chat.id, file)
    except FileNotFoundError:
        bot.reply_to(message, "Файл еще не создан (не было ни одной проверки).")

# Обработчик нажатий на текстовые кнопки
@bot.message_handler(content_types=['text'])
def handle_text_buttons(message):
    if message.text == '🔍 Проверить цену':
        manual_check(message)
    elif message.text == '📄 Скачать историю':
        send_file(message)

def run_dummy_server():
    # Bothost обычно передает нужный порт в переменной окружения PORT, либо используем 8080
    port = int(os.environ.get("PORT", 8080))
    class DummyHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is alive!")
        # Отключаем вывод логов сервера, чтобы не спамить
        def log_message(self, format, *args):
            pass
            
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    server.serve_forever()

if __name__ == '__main__':
    # Запускаем веб-сервер-заглушку для хостинга
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    # Запускаем планировщик задач
    scheduler_thread = threading.Thread(target=run_schedule, daemon=True)
    scheduler_thread.start()
    
    # Делаем первую проверку
    fetch_and_save_price()
    
    print("Бот успешно запущен и готов к работе!")
    bot.polling(none_stop=True)

