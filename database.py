import sqlite3

class Database:
    def __init__(self, db_name='wiki_bot.db'):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS search_requests (
            request_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            search_query TEXT NOT NULL,
            search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')

        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            article_id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id INTEGER,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            url TEXT,
            FOREIGN KEY (request_id) REFERENCES search_requests (request_id)
        )
        ''')
        self.conn.commit()

    def add_user(self, user_id, username=None, first_name=None, last_name=None):
        self.cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, first_name, last_name)
        VALUES (?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name))
        self.conn.commit()

    def log_search(self, user_id, query):
        self.cursor.execute('''
        INSERT INTO search_requests (user_id, search_query)
        VALUES (?, ?)
        ''', (user_id, query))
        self.conn.commit()
        return self.cursor.lastrowid

    def save_article(self, request_id, title, content, url=None):
        self.cursor.execute('''
        INSERT INTO articles (request_id, title, content, url)
        VALUES (?, ?, ?, ?)
        ''', (request_id, title, content, url))
        self.conn.commit()

    def get_user_history(self, user_id, limit=10):
        self.cursor.execute('''
        SELECT search_query, search_date 
        FROM search_requests 
        WHERE user_id = ? 
        ORDER BY search_date DESC 
        LIMIT ?
        ''', (user_id, limit))
        return self.cursor.fetchall()

    def get_popular_searches(self, limit=10):
        self.cursor.execute('''
        SELECT search_query, COUNT(*) as count 
        FROM search_requests 
        GROUP BY search_query 
        ORDER BY count DESC 
        LIMIT ?
        ''', (limit,))
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()

    def __del__(self):
        self.close()