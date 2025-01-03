from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Захардкоженный токен вашего бота
TELEGRAM_TOKEN = 'ваш_токен_здесь'

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Привет! Я ваш бот.')

def main():
    updater = Updater(TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
