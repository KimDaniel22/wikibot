from flask import Flask, request
from bot import application
import asyncio

application = Flask(__name__)

@app.route('/')
def home():
    return 'Bot is alive!'

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    asyncio.run(application.process_update(update))
    return '', 200