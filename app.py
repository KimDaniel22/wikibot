from flask import Flask, request
from bot import application, set_webhook
import asyncio
from telegram import Update

app = Flask(__name__)

@app.route('/')
def home():
    return 'Bot is alive!'

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    telegram_update = Update.de_json(update, application.bot)
    asyncio.run(application.process_update(telegram_update))
    return '', 200


@app.before_first_request
def init_webhook():
    asyncio.run(set_webhook())