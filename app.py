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

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(application.process_update(telegram_update))
    loop.close()

    return '', 200


@app.before_first_request
def init_webhook():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(set_webhook())
    loop.close()