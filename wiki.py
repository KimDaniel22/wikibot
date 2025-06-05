import re
import wikipedia
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from database import Database
import os
from config import TOKEN

wikipedia.set_lang("ru")

db = Database()
# db.init()

def extract_query(text: str) -> str:
    text = text.lower().strip()
    patterns = [
        r'^что такое\s+',
        r'^что это\s+',
        r'^объясни\s+что такое\s+',
        r'^расскажи про\s+',
        r'^поясни\s+что такое\s+',
        r'^кто такой\s+',
        r'^кто такая\s+',
        r'^что значит\s+',
        r'^\s*поясни\s+',
        r'^\s*объясни\s+',
    ]
    for pattern in patterns:
        text = re.sub(pattern, '', text)
    return text.strip()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.add_user(user.id, user.username, user.first_name, user.last_name)
    await update.message.reply_text(
        f"Привет, {user.first_name}! Я бот-википедия. Просто напиши мне что-нибудь или используй /wiki <запрос>")

async def handle_query(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
    query = extract_query(query)

    user = update.effective_user
    db.add_user(user.id, user.username, user.first_name, user.last_name)
    request_id = db.log_search(user.id, query)

    try:
        page = wikipedia.page(query)
        content = page.content.split('\n')[0]  # первый абзац
        url = page.url

        # Пытаемся найти картинку — первая из списка images, которая jpg/png и не слишком мелкая
        img_url = None
        for img in page.images:
            if img.lower().endswith(('.jpg', '.jpeg', '.png')):
                img_url = img
                break

        response = f"📚 <b>{page.title}</b>\n\n{content}\n\n"

        keyboard = [
            [InlineKeyboardButton("Читать в Википедии", url=url)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if img_url:
            # Отправляем фото с подписью и кнопкой
            await update.message.reply_photo(photo=img_url, caption=response, reply_markup=reply_markup, parse_mode="HTML")
        else:
            # Отправляем просто текст с кнопкой
            await update.message.reply_text(response, reply_markup=reply_markup, parse_mode="HTML")

        db.save_article(request_id, page.title, content, url)

    except wikipedia.exceptions.DisambiguationError as e:
        await update.message.reply_text(
            f"🔎 Слишком много значений. Уточни запрос. Например: {', '.join(e.options[:5])}")
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