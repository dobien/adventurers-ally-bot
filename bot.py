import os
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Получение токена из переменной окружения
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Привет! Я ваш бот.')

def main():
    if TELEGRAM_TOKEN is None:
        print("Ошибка: переменная окружения TELEGRAM_TOKEN не установлена.")
        return

    updater = Updater(TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
