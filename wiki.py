from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import wikipedia
from database import get_connection


wikipedia.set_lang("ru")

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! Напиши мне слово или используй команду /wiki <тема>, и я найду информацию в Википедии.")

# Универсальный обработчик запроса

def log_request(user_id, username, query, response):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO requests (user_id, username, query, response)
        VALUES (%s, %s, %s, %s)
    """, (user_id, username, query, response))
    conn.commit()
    cur.close()
    conn.close()

async def handle_query(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
    try:
        summary = wikipedia.summary(query, sentences=3)
        page = wikipedia.page(query)
        # Ограничим текст (макс 1000 символов)
        if len(summary) > 1000:
            summary = summary[:1000] + "..."

        # Кнопка на статью
        keyboard = [[InlineKeyboardButton("📖 Читать в Википедии", url=page.url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(summary, reply_markup=reply_markup)
    except wikipedia.exceptions.DisambiguationError as e:
        await update.message.reply_text(f"🔎 Слишком много значений. Уточни запрос. Например: {', '.join(e.options[:5])}")
    except wikipedia.exceptions.PageError:
        await update.message.reply_text("❌ Ничего не найдено. Попробуй другой запрос.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Произошла ошибка: {e}")

# Обработчик команды /wiki
async def wiki_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        query = ' '.join(context.args)
        await handle_query(update, context, query)
    else:
        await update.message.reply_text("❗ Использование: /wiki <тема>")

# Обработчик обычного текста
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    await handle_query(update, context, query)

# Главная функция
def main():
    TOKEN = "7585359871:AAGG9F2z0IsPdrw2OsFXn6RfKtGrXbRl-Zo"

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("wiki", wiki_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("✅ Бот запущен. Ожидает сообщения...")
    app.run_polling()

if __name__ == "__main__":
    main()






