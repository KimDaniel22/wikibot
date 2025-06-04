import sqlite3
from datetime import datetime

# Подключаемся к базе данных (файл создастся автоматически)
conn = sqlite3.connect('wiki_bot.db', check_same_thread=False)
cursor = conn.cursor()

# Создаем таблицы
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

def add_user(user_id, username=None, first_name=None, last_name=None):
    """Добавляем пользователя в базу"""
    cursor.execute('''
    INSERT OR IGNORE INTO users (user_id, username, first_name, last_name)
    VALUES (?, ?, ?, ?)
    ''', (user_id, username, first_name, last_name))
    conn.commit()

def log_search(user_id, query):
    """Логируем поисковый запрос"""
    cursor.execute('''
    INSERT INTO search_requests (user_id, search_query)
    VALUES (?, ?)
    ''', (user_id, query))
    conn.commit()
    return cursor.lastrowid  # Возвращаем ID запроса

def save_article(request_id, title, content, url=None):
    """Сохраняем найденную статью"""
    cursor.execute('''
    INSERT INTO articles (request_id, title, content, url)
    VALUES (?, ?, ?, ?)
    ''', (request_id, title, content, url))
    conn.commit()