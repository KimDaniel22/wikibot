import os
import sqlite3
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

from config import BOT_TOKEN, APP_URL
from database import init_db, log_user, log_search, save_article
import wikipedia

wikipedia.set_lang("ru")

app = Flask(__name__)
bot_app = ApplicationBuilder().token(BOT_TOKEN).build()

# --- Обработчики ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    log_user(user.id, user.username, user.first_name, user.last_name)
    await update.message.reply_text("Привет! Я бот-википедия. Напиши что-нибудь или /wiki <запрос>")

async def handle_query(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
    user = update.effective_user
    log_user(user.id, user.username, user.first_name, user.last_name)
    request_id = log_search(user.id, query)

    try:
        page = wikipedia.page(query)
        save_article(request_id, page.title, page.content, page.url)

        response = f"📚 {page.title}\n\n{page.content[:4000]}..."
        if len(page.content) > 4000:
            response += f"\n\nЧитать полностью: {page.url}"

        await update.message.reply_text(response)

    except wikipedia.exceptions.DisambiguationError as e:
        await update.message.reply_text(f"🔎 Слишком много значений. Уточни запрос. Например: {', '.join(e.options[:5])}")
    except wikipedia.exceptions.PageError:
        await update.message.reply_text("❌ Ничего не найдено.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Ошибка: {e}")

async def wiki_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        await handle_query(update, context, ' '.join(context.args))
    else:
        await update.message.reply_text("❗️ Использование: /wiki <тема>")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_query(update, context, update.message.text)


# --- Webhook ---
@app.route("/")
def home():
    return "Бот работает"

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(force=True), bot_app.bot)
    await bot_app.process_update(update)
    return "ok"


# --- Запуск ---
if __name__ == "__main__":
    import asyncio
    from telegram import Bot

    init_db()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("wiki", wiki_command))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    async def main():
        await Bot(BOT_TOKEN).set_webhook(f"{APP_URL}/{BOT_TOKEN}")
        print("Webhook установлен!")

    asyncio.run(main())
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))