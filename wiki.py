import wikipedia
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from database import Database
import os


wikipedia.set_lang("ru")

db = Database()

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    print("❌ Ошибка: Не найден токен бота в переменной окружения BOT_TOKEN")
    exit(1)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.add_user(user.id, user.username, user.first_name, user.last_name)
    await update.message.reply_text(
        f"Привет, {user.first_name}! Я бот-википедия.\n"
        f"Просто напиши мне что-нибудь, например: <i>Что такое квантовая физика</i>,\n"
        f"или используй команду: /wiki <запрос>",
        parse_mode="HTML"
    )

async def handle_query(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
    user = update.effective_user
    db.add_user(user.id, user.username, user.first_name, user.last_name)
    request_id = db.log_search(user.id, query)

    try:
        page = wikipedia.page(query, auto_suggest=False)
        summary = wikipedia.summary(query, auto_suggest=False)
        db.save_article(request_id, page.title, summary, page.url)

        # Кнопка "Читать в Википедии"
        keyboard = [[InlineKeyboardButton("🔗 Читать в Википедии", url=page.url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Попробуем взять первое изображение (если есть)
        image_url = page.images[0] if page.images else None
        if image_url and image_url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
            await update.message.reply_photo(
                photo=image_url,
                caption=f"📚 <b>{page.title}</b>\n\n{summary}",
                parse_mode="HTML",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                text=f"📚 <b>{page.title}</b>\n\n{summary}",
                parse_mode="HTML",
                reply_markup=reply_markup
            )

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

    print("✅ Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()