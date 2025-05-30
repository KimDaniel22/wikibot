from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import wikipedia
from database import get_connection
import unicodedata
import re
import logging

logging.basicConfig(
    filename='bot_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    encoding='utf-8'
)
wikipedia.set_lang("ru")

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Напиши мне слово или фразу, или используй команду /wiki <тема>, и я найду информацию в Википедии."
    )

# Логирование запросов в базу данных
def log_request(user_id, username, query, response):
    try:
        conn = get_connection()
        cur = conn.cursor()

        safe_username = str(username)
        safe_query = str(query)
        if isinstance(response, bytes):
            safe_response = response.decode('utf-8', errors='ignore')
        else:
            safe_response = str(response)

        logging.info(f"User: {safe_username} | Query: {safe_query} | Response: {safe_response[:200]}")

        print("== Logging preview ==")
        print("User:", repr(safe_username))
        print("Query:", repr(safe_query))
        print("Response:", repr(safe_response[:200]))  # первые 200 символов

        print(f"[DEBUG] Username: {safe_username}")
        print(f"[DEBUG] Query: {safe_query}")
        print(f"[DEBUG] Response (first 200 chars): {safe_response[:200]}")

        cur.execute("""
            INSERT INTO requests (user_id, username, query, response)
            VALUES (%s, %s, %s, %s)
        """, (user_id, safe_username, safe_query, safe_response))

        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("Ошибка при логировании в БД:", e)

def get_wiki_image(title):
    import requests

    URL = "https://ru.wikipedia.org/w/api.php"
    PARAMS = {
        "action": "query",
        "format": "json",
        "prop": "pageimages",
        "titles": title,
        "pithumbsize": 500  # размер изображения
    }

    try:
        response = requests.get(URL, params=PARAMS)
        data = response.json()
        pages = data["query"]["pages"]
        for page_id in pages:
            page = pages[page_id]
            if "thumbnail" in page:
                return page["thumbnail"]["source"]
    except Exception as e:
        print("Ошибка при получении изображения:", e)

    return None

def clean_query(text):
    text = text.lower()
    # Убираем вводные слова
    text = re.sub(r"^(что|кто|где|когда|зачем|почему) такое ", "", text)
    text = re.sub(r"[^\w\sёЁ\-]", "", text)  # убираем лишние символы, если надо
    return text.strip()

# Обработка запроса
async def handle_query(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
    try:
        query = clean_query(query)
        results = wikipedia.search(query)

        if not results:
            await update.message.reply_text("❌ Ничего не найдено.")
            return

        page_title = results[0]
        summary = wikipedia.summary(page_title, sentences=3)
        page = wikipedia.page(page_title)

        if len(summary) > 1000:
            summary = summary[:1000] + "..."

        keyboard = [[InlineKeyboardButton("📖 Читать в Википедии", url=page.url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Логирование
        log_request(
            update.message.from_user.id,
            update.message.from_user.username,
            query,
            summary
        )

        # Изображение
        image_url = get_wiki_image(query)

        if image_url:
            await update.message.reply_photo(photo=image_url, caption=summary, reply_markup=reply_markup)
        else:
            await update.message.reply_text(summary, reply_markup=reply_markup)

    except wikipedia.exceptions.DisambiguationError as e:
        await update.message.reply_text(f"🔎 Слишком много значений. Уточни запрос. Например: {', '.join(e.options[:5])}")
    except wikipedia.exceptions.PageError:
        await update.message.reply_text("❌ Ничего не найдено. Попробуй другой запрос.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Произошла ошибка: {e}")

# Команда /wiki
async def wiki_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        query = ' '.join(context.args)
        await handle_query(update, context, query)
    else:
        await update.message.reply_text("❗️ Использование: /wiki <тема>")

# Сообщения без команды
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    await handle_query(update, context, query)

# Запуск
def main():
    TOKEN = "7585359871:AAGG9F2z0IsPdrw2OsFXn6RfKtGrXbRl-Zo"

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("wiki", wiki_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("Бот запущен.")
    app.run_polling()

if __name__ == "__main__":
    main()