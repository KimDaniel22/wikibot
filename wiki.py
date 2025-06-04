import sqlite3
import wikipedia
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

wikipedia.set_lang("ru")


# --- Инициализация базы данных ---
def init_db():
    conn = sqlite3.connect('wiki_bot.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS search_requests (
        request_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        search_query TEXT NOT NULL,
        search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS articles (
        article_id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id INTEGER,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        url TEXT,
        FOREIGN KEY (request_id) REFERENCES search_requests (request_id)
    )
    ''')

    conn.commit()
    conn.close()


# --- Работа с базой данных ---
def log_user(user_id, username=None, first_name=None, last_name=None):
    conn = sqlite3.connect('wiki_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
    INSERT OR IGNORE INTO users (user_id, username, first_name, last_name)
    VALUES (?, ?, ?, ?)
    ''', (user_id, username, first_name, last_name))
    conn.commit()
    conn.close()


def log_search(user_id, query):
    conn = sqlite3.connect('wiki_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO search_requests (user_id, search_query)
    VALUES (?, ?)
    ''', (user_id, query))
    conn.commit()
    request_id = cursor.lastrowid
    conn.close()
    return request_id


def save_article(request_id, title, content, url=None):
    conn = sqlite3.connect('wiki_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO articles (request_id, title, content, url)
    VALUES (?, ?, ?, ?)
    ''', (request_id, title, content, url))
    conn.commit()
    conn.close()


# --- Обработчики команд и сообщений ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    log_user(user.id, user.username, user.first_name, user.last_name)
    await update.message.reply_text(
        f"Привет, {user.first_name}! Я бот-википедия. Просто напиши мне что-нибудь или используй /wiki <запрос>")


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


# --- Основной запуск ---
def main():
    init_db()

    TOKEN = "7585359871:AAGG9F2z0IsPdrw2OsFXn6RfKtGrXbRl-Zo"
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("wiki", wiki_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("Бот запущен")
    app.run_polling()


if __name__ == "__main__":
    main()