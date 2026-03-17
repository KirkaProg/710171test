import os
import time
import threading
from datetime import datetime

import requests
from lxml import html
import schedule
import telebot
from dotenv import load_dotenv

# Пытаемся загрузить .env, если он есть (для локального тестирования). 
# На хостинге Bothost эти переменные будут браться из настроек панели.
load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

if not TELEGRAM_TOKEN or not CHAT_ID:
    raise ValueError("Ошибка: Не заданы TELEGRAM_TOKEN или CHAT_ID в переменных окружения")

URL = 'https://lab-store071.ru/catalog/kupit-makbuk-v-tule/'
XPATH_PRICE = '//*[@id="bx_1847241719_488"]/a/div[1]/span[2]'
FILE_NAME = 'prices.txt'

bot = telebot.TeleBot(TELEGRAM_TOKEN)

def fetch_and_save_price():
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
        else:
            price = "Цена не найдена"
    except Exception as e:
        price = f"Ошибка парсинга: {e}"

    now = datetime.now()
    log_entry = f"{now.strftime('%d.%m.%Y')} / {now.strftime('%H:%M:%S')} / {price}\n"
    
    # Сохраняем в файл внутри контейнера
    with open(FILE_NAME, 'a', encoding='utf-8') as file:
        file.write(log_entry)
        
    try:
        bot.send_message(CHAT_ID, f"🕒 Автоматическая проверка:\n{log_entry.strip()}")
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")

def run_schedule():
    schedule.every(1).hours.do(fetch_and_save_price)
    while True:
        schedule.run_pending()
        time.sleep(1)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Бот работает на Bothost.\n/check - проверить цену\n/file - скачать историю")

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
        bot.reply_to(message, "Файл еще не создан.")

if __name__ == '__main__':
    # На Bothost print() выводится в раздел "Логи"
    print("Запуск планировщика задач...")
    scheduler_thread = threading.Thread(target=run_schedule, daemon=True)
    scheduler_thread.start()
    
    fetch_and_save_price()
    
    print("Бот успешно запущен и готов к работе!")
    bot.polling(none_stop=True)
