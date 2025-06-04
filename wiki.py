import wikipedia
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from database import Database
import os

wikipedia.set_lang("ru")

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    print("Ошибка: Не найден токен бота в переменной окружения BOT_TOKEN")
    exit(1)

db = Database()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.add_user(user.id, user.username, user.first_name, user.last_name)
    await update.message.reply_text(
        f"Привет, {user.first_name}! Я бот-википедия. Просто напиши мне что-нибудь или используй /wiki <запрос>"
    )

async def handle_query(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
    user = update.effective_user
    db.add_user(user.id, user.username, user.first_name, user.last_name)
    request_id = db.log_search(user.id, query)

    try:
        page = wikipedia.page(query)
        db.save_article(request_id, page.title, page.content, page.url)

        response = f"📚 {page.title}\n\n{page.content[:4000]}"
        if len(page.content) > 4000:
            response += f"\n\nЧитать полностью: {page.url}"

        await update.message.reply_text(response)

    except wikipedia.exceptions.DisambiguationError as e:
        await update.message.reply_text(
            f"🔎 Слишком много значений. Уточни запрос. Например: {', '.join(e.options[:5])}"
        )
    except wikipedia.exceptions.PageError:
        await update.message.reply_text("❌ Ничего не найдено. Попробуй другой запрос.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Произошла ошибка: {e}")

async def wiki_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        query = ' '.join(context.args)
        await handle_query(update, context, query)
    else:
        await update.message.reply_text("❗️ Использование: /wiki <тема>")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    await handle_query(update, context, query)

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("wiki", wiki_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()