from flask import Flask, request
from telegram import Bot, Update
from config import TOKEN, WEBHOOK_URL
from bot import setup_handlers
import os

app = Flask(__name__)
bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot, None, workers=0)

# Настройка обработчиков из bot.py
setup_handlers(dispatcher)

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    return 'OK'

def set_webhook():
    bot.set_webhook(f"{WEBHOOK_URL}/webhook")

if name == '__main__':
    set_webhook()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)