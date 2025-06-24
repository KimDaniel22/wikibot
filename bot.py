from telegram import Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
from database import init_db
import wikipedia

wikipedia.set_lang("ru")

def setup_handlers(dispatcher):
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f"Привет, {user.first_name}! Я Wikipedia бот.")

def handle_message(update: Update, context):
    search_query = update.message.text
    try:
        summary = wikipedia.summary(search_query, sentences=2)
        update.message.reply_text(summary)
    except wikipedia.exceptions.PageError:
        update.message.reply_text("Не найдено информации по вашему запросу.")
    except wikipedia.exceptions.DisambiguationError as e:
        update.message.reply_text(f"Уточните запрос: {e.options[:5]}")

# Инициализация БД при импорте
init_db()